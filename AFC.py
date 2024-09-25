# 8 Track Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from ast import Str
import math, logging
import chelper
import copy
import os 
import time
import json
import toolhead
import stepper
from configparser import Error as error
from kinematics import extruder
from . import stepper_enable, output_pin
from urllib.request import urlopen
from extras.heaters import Heater

class afc:
    def __init__(self, config):
        self.config = config
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()

        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        self.gcode = self.printer.lookup_object('gcode')
        self.VarFile = config.get('VarFile')
        self.Type = config.get('Type')
        self.current = None
        self.failure = False
        self.lanes = {}
        
        # SPOOLMAN
        
        self.spoolman = config.getboolean('spoolman', False)
        if self.spoolman:
            self.spoolman_filament={}
                
        #LED SETTINGS
        self.ind_lights = None
        self.led_name = config.get('led_name')
        self.led_fault =config.get('led_fault','1,0,0,0')
        self.led_ready = config.get('led_ready','1,1,1,1')
        self.led_not_ready = config.get('led_not_ready','1,0,0,0')
        self.led_loading = config.get('led_loading','1,1,0,0')
        self.led_unloading = config.get('led_unloading','1,1,.5,0')
        self.led_tool_loaded = config.get('led_tool_loaded','1,1,0,0')

        # HUB
        self.hub_dis = config.getfloat("hub_dis", 45)
        self.hub_move_dis = config.getfloat("hub_move_dis", 50)
        self.hub = ''

        # HUB CUTTER
        self.hub_cut_active = config.getboolean("hub_cut_active", False)
        self.hub_cut_dist = config.getfloat("hub_cut_dist", 200)
        self.hub_cut_clear = config.getfloat("hub_cut_clear", 120)
        self.hub_cut_min_length = config.getfloat("hub_cut_min_length", 200)
        self.hub_cut_servo_pass_angle = config.getfloat("hub_cut_servo_pass_angle", 0)
        self.hub_cut_servo_clip_angle = config.getfloat("hub_cut_servo_clip_angle", 160)
        self.hub_cut_servo_prep_angle = config.getfloat("hub_cut_servo_prep_angle", 75)
        self.hub_cut_confirm = config.getfloat("hub_cut_confirm", 0);

        # TOOL Cutting Settings
        self.tool = ''
        self.tool_cut_active = config.getboolean("tool_cut_active", False)
        self.tool_cut_cmd = config.get('tool_cut_cmd')

        # Tip Forming
        self.ramming_volume = config.getfloat("ramming_volume", 0)
        self.toolchange_temp  = config.getfloat("toolchange_temp", 0)
        self.unloading_speed_start  = config.getfloat("unloading_speed_start", 80)
        self.unloading_speed  = config.getfloat("unloading_speed", 18)
        self.cooling_tube_position  = config.getfloat("cooling_tube_position", 35)
        self.cooling_tube_length  = config.getfloat("cooling_tube_length", 10)
        self.initial_cooling_speed  = config.getfloat("initial_cooling_speed", 10)
        self.final_cooling_speed  = config.getfloat("final_cooling_speed", 50)
        self.cooling_moves  = config.getfloat("cooling_moves", 4)
        self.use_skinnydip  = config.getboolean("use_skinnydip", False)
        self.skinnydip_distance  = config.getfloat("skinnydip_distance", 4)
        self.dip_insertion_speed  = config.getfloat("dip_insertion_speed", 4)
        self.dip_extraction_speed  = config.getfloat("dip_extraction_speed", 4)
        self.melt_zone_pause  = config.getfloat("melt_zone_pause", 4)
        self.cooling_zone_pause  = config.getfloat("cooling_zone_pause", 4)

        # CHOICES
        self.park = config.getboolean("park", False)
        self.park_cmd = config.get('park_cmd', None)
        self.kick = config.getboolean("kick", False)
        self.kick_cmd = config.get('kick_cmd', None)
        self.wipe = config.getboolean("wipe", False)
        self.wipe_cmd = config.get('wipe_cmd', None)
        self.poop = config.getboolean("poop", False)
        self.poop_cmd = config.get('poop_cmd', None)
        self.form_tip = config.getboolean("form_tip", False)
        self.form_tip_cmd = config.get('form_tip_cmd', None)

        self.tool_stn = config.getfloat("tool_stn", 120)
        self.tool_stn_unload = config.getfloat("tool_stn_unload", self.tool_stn)
        self.afc_bowden_length = config.getfloat("afc_bowden_length", 900)
        
        # MOVE SETTINGS
        self.tool_sensor_after_extruder = config.getfloat("tool_sensor_after_extruder", 0)
        self.long_moves_speed = config.getfloat("long_moves_speed", 100)
        self.long_moves_accel = config.getfloat("long_moves_accel", 400)
        self.short_moves_speed = config.getfloat("short_moves_speed", 25)
        self.short_moves_accel = config.getfloat("short_moves_accel", 400)
        self.short_move = ' VELOCITY=' + str(self.short_moves_speed) + ' ACCEL='+ str(self.short_moves_accel)
        self.long_move = ' VELOCITY=' + str(self.long_moves_speed) + ' ACCEL='+ str(self.long_moves_accel)
        self.short_move_dis = config.getfloat("short_move_dis", 10)
        self.tool_unload_speed =config.getfloat("tool_unload_speed", 10)
        self.tool_load_speed =config.getfloat("tool_load_speed", 10)
        self.z_hop =config.getfloat("z_hop", 0)


        self.gcode.register_command('HUB_LOAD', self.cmd_HUB_LOAD, desc=self.cmd_HUB_LOAD_help)
        if self.Type == 'Box_Turtle':
            self.gcode.register_command('LANE_UNLOAD', self.cmd_LANE_UNLOAD, desc=self.cmd_LANE_UNLOAD_help)

        self.gcode.register_command('TOOL_LOAD', self.cmd_TOOL_LOAD, desc=self.cmd_TOOL_LOAD_help)
        self.gcode.register_command('TOOL_UNLOAD', self.cmd_TOOL_UNLOAD, desc=self.cmd_TOOL_UNLOAD_help)
        self.gcode.register_command('CHANGE_TOOL', self.cmd_CHANGE_TOOL, desc=self.cmd_CHANGE_TOOL_help)
        self.gcode.register_command('PREP', self.cmd_PREP, desc=self.cmd_PREP_help)
        self.gcode.register_command('LANE_MOVE', self.cmd_LANE_MOVE, desc=self.cmd_LANE_MOVE_help)

        self.gcode.register_command('TEST', self.cmd_TEST, desc=self.cmd_TEST_help)
        self.gcode.register_command('HUB_CUT_TEST', self.cmd_HUB_CUT_TEST, desc=self.cmd_HUB_CUT_TEST_help)

        self.VarFile = config.get('VarFile')
        
        # Get debug and cast to boolean
        self.debug = True == config.get('debug', 0)

    cmd_LANE_MOVE_help = "Lane Manual Movements"
    def cmd_LANE_MOVE(self, gcmd):
        lane = gcmd.get('LANE', None)
        distance = gcmd.get('DISTANCE', 0)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_LANE.move(int(distance), self.short_moves_speed, self.short_moves_accel)

    def respond_info(self, msg):
        """
        respond_info function is a help function to print non error information out to console
        """
        self.gcode.respond_info( msg )
    
    
    def respond_error(self, msg, raise_error=False):
        """
        respond_error Helper function to print errors to console
        
        :param msg: message to print to console
        :param raise_error: raises error and halt klipper
        """
        self.gcode._respond_error( msg )
        if raise_error: raise error( msg )
    
    def respond_debug(self, msg):
        """
        respond_debug function is a help function to print debug information out to console if debug flag is set in configuration
        """
        if self.debug: self.respond_info(msg)
    
    # Helper function to write variables to file. Prints with indents to make it more readable for users
    def save_vars(self):
        """
        save_vars function saves lane variables to var file and prints with indents to
                  make it more readable for users
        """
        with open(self.VarFile, 'w') as f:
            f.write(json.dumps(self.lanes, indent=4))

    def handle_connect(self):
        """
        Handle the connection event.

        This function is called when the printer connects. It looks up the toolhead object
        and assigns it to the instance variable `self.toolhead`.
        """
        self.toolhead = self.printer.lookup_object('toolhead')

    cmd_TEST_help = "Test Assist Motors"
    def cmd_TEST(self, gcmd):
        lane = gcmd.get('LANE', None)
        self.gcode.respond_info('TEST ROUTINE')
        LANE = self.printer.lookup_object('AFC_stepper '+lane)
        self.gcode.respond_info('Testing at full speed')
        LANE.assist(-1)
        time.sleep(4)
        if LANE.afc_motor_rwd.is_pwm:
            self.gcode.respond_info('Testing at 50 percent speed')
            LANE.assist(-.5)
            time.sleep(4)
            self.gcode.respond_info('Testing at 30 percent speed')
            LANE.assist(-.3)
            time.sleep(4)
            self.gcode.respond_info('Testing at 10 percent speed')
            LANE.assist(-.1)
            time.sleep(4)
            
        self.gcode.respond_info('Test routine complete')
        LANE.assist(0)
        
    def afc_led (self, status, idx=None):
        afc_object = 'AFC_led '+ idx.split(':')[0]
        
        # Try to find led object, if not found print error to console for user to see
        try:
            led = self.printer.lookup_object(afc_object)
        except:
            error_string = "Error: Cannot find [{}] in config, make sure led_index in config is correct for AFC_stepper {}".format(afc_object, idx.split(':')[-1])
            self.respond_error( error_string, raise_error=True )

        colors=list(map(float,status.split(',')))
        transmit = 1
        if idx is not None:
            index = int(idx.split(':')[1])
        else:
            index = None

        def lookahead_bgfunc(print_time):
            led.led_helper.set_color(index, colors)
            if transmit:
                led.led_helper.check_transmit(print_time) 
        
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.register_lookahead_callback(lookahead_bgfunc)

    cmd_PREP_help = "Prep AFC"
    def cmd_PREP(self, gcmd):
        while self.printer.state_message != 'Printer is ready':
            time.sleep(1)
        time.sleep(3)
        if os.path.exists(self.VarFile) and os.stat(self.VarFile).st_size > 0:
            try:
                self.lanes=json.load(open(self.VarFile))
            except IOError:
                self.lanes={}
            except ValueError:
                self.lanes={}
        else:
            self.lanes={}
        temp=[]
        
        for PO in self.printer.objects:
            if 'AFC_stepper' in PO and 'tmc' not in PO:
                LANE=self.printer.lookup_object(PO)
                temp.append(LANE.name)
                if LANE.unit not in self.lanes:
                    self.lanes[LANE.unit]={}
                if LANE.name not in self.lanes[LANE.unit]:
                    self.lanes[LANE.unit][LANE.name]={}
                if 'index' not in self.lanes[LANE.unit][LANE.name]:
                    self.lanes[LANE.unit][LANE.name]['index'] = LANE.index
                if 'material' not in self.lanes[LANE.unit][LANE.name]:
                    self.lanes[LANE.unit][LANE.name]['material']=''
                if 'spool_id' not in self.lanes[LANE.unit][LANE.name]:
                    self.lanes[LANE.unit][LANE.name]['spool_id']=''
                if 'color' not in self.lanes[LANE.unit][LANE.name]:
                    self.lanes[LANE.unit][LANE.name]['color']=''
                if 'tool_loaded' not in self.lanes[LANE.unit][LANE.name]:
                    self.lanes[LANE.unit][LANE.name]['tool_loaded'] = False
                if self.lanes[LANE.unit][LANE.name]['tool_loaded'] == True:
                    self.current = LANE.name
        tmp=[]

        for UNIT in self.lanes.keys():
            for lanecheck in self.lanes[UNIT].keys():
                if lanecheck not in temp:
                    tmp.append(lanecheck)
            for erase in tmp:
                del self.lanes[UNIT][erase]
            
        self.save_vars()
        
        if self.Type == 'Box_Turtle':
            logo ='R  _____     ____\n'
            logo+='E /      \  |  o | \n'
            logo+='A |       |/ ___/ \n'
            logo+='D |_________/     \n'
            logo+='Y |_|_| |_|_|\n'

            logo_error ='E  _____     ____\n'
            logo_error+='R /      \  |  o | \n'
            logo_error+='R |       |/ ___/ \n'
            logo_error+='O |_________/     \n'
            logo_error+='R |_|_| |_|_|\n'

            for UNIT in self.lanes.keys():
                self.gcode.respond_info(self.Type + ' ' + UNIT +' Prepping lanes')
                for LANE in self.lanes[UNIT].keys():
                    CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
                    CUR_LANE.extruder_stepper.sync_to_extruder(None)
                    CUR_LANE.move( -5, self.short_moves_speed, self.short_moves_accel)
                    CUR_LANE.move( 5, self.short_moves_speed, self.short_moves_accel)
                    if CUR_LANE.prep_state == False:
                        self.afc_led(self.led_not_ready, CUR_LANE.led_index)
            
            error_string = "Error: Filament switch sensor {} not found in config file"
            try:
                self.hub=self.printer.lookup_object('filament_switch_sensor hub').runout_helper
            except:
                self.respond_error(error_string.format("hub"), raise_error=True)

            try:
                self.tool=self.printer.lookup_object('filament_switch_sensor tool').runout_helper
            except:
                self.respond_error(error_string.format("tool"), raise_error=True)

            if self.current == None:
                for UNIT in self.lanes.keys():
                    for LANE in self.lanes[UNIT].keys():
                        check_success = True
                        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
                        CUR_LANE.do_enable(True)
                        if self.hub.filament_present == True and CUR_LANE.load_state == True:
                            x = 0
                            while CUR_LANE.load_state == True:
                                CUR_LANE.move( self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
                                x += 1
                                #time.sleep(1)
                                #callout if filament can't be retracted before extruder load switch
                                if x > (self.afc_bowden_length/self.short_move_dis)+3:
                                    message = (' FAILED TO RESET EXTRUDER\n||=====||=x--||-----||\nTRG   LOAD   HUB   TOOL')
                                    self.handle_lane_failure(CUR_LANE, LANE, message)
                                    check_success = False
                                    break

                            x = 0
                            while CUR_LANE.load_state == False:
                                CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                                x += 1
                                #time.sleep(1)
                                #callout if filament is past trigger but can't be brought past extruder
                                if x > 20:
                                    message = (' FAILED TO RELOAD, CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                                    self.handle_lane_failure(CUR_LANE, LANE, message)
                                    check_success = False
                                    break
                            if check_success == True:
                                self.afc_led(self.led_ready, CUR_LANE.led_index)
                        else:
                            if CUR_LANE.prep_state == True:
                                x = 0
                                while CUR_LANE.load_state == False:
                                    CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                                    x += 1
                                    time.sleep(1)
                                    #callout if filament is past trigger but can't be brought past extruder
                                    if x > 20:
                                        message = (' FAILED TO LOAD ' + LANE.upper() + ' CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                                        self.handle_lane_failure(CUR_LANE, lane, message)

                                        check_success = False
                                        break
                                if check_success == True:
                                    self.afc_led(self.led_ready, CUR_LANE.led_index)
                            else:
                                self.afc_led(self.led_not_ready, CUR_LANE.led_index)
                            
                        if check_success == True:
                            msg = ''
                            if CUR_LANE.prep_state == True:
                                msg +="LOCKED"
                                if CUR_LANE.load_state == True:
                                    msg +=" AND LOADED"
                                else:
                                    msg +=" NOT LOADED"
                            else:
                                if CUR_LANE.load_state == True:
                                    msg +=" NOT READY"
                                    CUR_LANE.set_afc_prep_done()
                                    CUR_LANE.do_enable(False)
                                    self.gcode.respond_info(CUR_LANE.name.upper() + 'CHECK FILAMENT Prep: False - Load: True')
                                else:
                                    msg += 'EMPTY READY FOR SPOOL'
                                    
                            # Setting lane to prepped so that loading will happen once user tries to load filament
                            CUR_LANE.set_afc_prep_done()
                            CUR_LANE.do_enable(False)
                            self.gcode.respond_info(CUR_LANE.name.upper() + ' ' + msg)
                
            else:
                for UNIT in self.lanes.keys():
                    for lane in self.lanes[UNIT].keys():
                        check_success = True
                        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
                        CUR_LANE.do_enable(True)
                        if self.current == lane:
                            if self.tool.filament_present == False and self.hub.filament_present == True:
                                untool_attempts = 0
                                while CUR_LANE.load_state == True:
                                    CUR_LANE.assist(-1)
                                    CUR_LANE.move( self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
                                    time.sleep(1) #take a break to give trigger time to disengage and not retract filament too far
                                    untool_attempts += 1
                                    if untool_attempts > (self.afc_bowden_length/self.short_move_dis)+3:
                                        message = (' FAILED TO CLEAR LINE, ' + CUR_LANE.upper() +' CHECK FILAMENT PATH\n')
                                        self.gcode.respond_info(message)
                                        break
                                CUR_LANE.status = None
                                self.current = None
                                reload_attempts = 0
                                x = 0
                                while CUR_LANE.load_state == False:
                                    CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                                    if x > 20:
                                        message = (' FAILED TO LOAD ' + CUR_LANE.upper() + ' CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                                        self.gcode.respond_info(message)
                                        break
                            
                            else:
                                CUR_LANE = self.printer.lookup_object('AFC_stepper ' + self.current)
                                CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
                                self.respond_info(self.current + " Tool Loaded")
                                self.afc_led(self.led_tool_loaded, CUR_LANE.led_index)
                        else:
                            # Filament is loaded to the prep sensor but not the hub sensor. Load until filament is detected in hub.
                            #   Times out after 20 tries so it does not spin forever, this probably means that the filament is not
                            #   far enough in for the gears to grab the filament
                            if CUR_LANE.prep_state == True and CUR_LANE.load_state == False:
                                num_tries = 0
                                while CUR_LANE.load_state == False and num_tries < 20:
                                    CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                                    num_tries += 1
                                if 20 == num_tries: self.gcode._respond_error("Could not load {} to load filament sensor, remove and reinsert to load correctly".format(CUR_LANE.name))
                            
                            if CUR_LANE.prep_state == True and CUR_LANE.load_state == True:
                                self.afc_led(self.led_ready, CUR_LANE.led_index)

                        if check_success == True:
                            # Setting lane to prepped so that loading will happen once user tries to load filament
                            CUR_LANE.set_afc_prep_done()
                            CUR_LANE.do_enable(False)
                            self.gcode.respond_info('LANE ' + lane[-1] + ' READY')
        if check_success == True:                            
            self.gcode.respond_info(logo)
        else:
            self.gcode.respond_info(logo_error)

        # Call out if all lanes are clear but hub is not
        if self.hub.filament_present == True and self.tool.filament_present == False:
            msg = ('LANES READY, HUB NOT CLEAR\n||-----||----|x|-----||\nTRG   LOAD   HUB   TOOL')
            self.respond_error(msg, raise_error=False)

    handle_lane_failure_help = "Get load errors, stop stepper and respond error"
    def handle_lane_failure(self, CUR_LANE, lane, message):
        CUR_LANE.set_afc_prep_done()
        # Disable the stepper for this lane
        CUR_LANE.do_enable(False)
        msg = (lane.upper() + ' NOT READY' + message)
        self.respond_error(msg, raise_error=False)
        self.afc_led(self.led_fault, CUR_LANE.led_index)

    # HUB COMMANDS
    cmd_HUB_LOAD_help = "Load lane into hub"
    def cmd_HUB_LOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        if LANE.load_state == False:
            LANE.do_enable(True)
            while LANE.load_state == False:
                LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
            LANE.move( self.hub_move_dis * -1 , self.short_moves_speed, self.short_moves_accel)
            LANE.do_enable(False)

    cmd_LANE_UNLOAD_help = "Unload lane from extruder"
    def cmd_LANE_UNLOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        LANE = self.printer.lookup_object('AFC_stepper '+ lane)
        if lane != self.current:
            LANE.do_enable(True)
            while LANE.load_state == True:
               LANE.move( self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
            LANE.move( self.hub_move_dis * -5, self.short_moves_speed, self.short_moves_accel)
            LANE.do_enable(False)
        else:
            self.gcode.respond_info('LANE ' + lane + ' IS TOOL LOADED')

    cmd_TOOL_LOAD_help = "Load lane into tool"
    def cmd_TOOL_LOAD(self, gcmd):
        self.failure = False
        #self.toolhead = self.printer.lookup_object('toolhead')
        extruder = self.toolhead.get_extruder() #Get extruder
        self.heater = extruder.get_heater() #Get extruder heater
        lane = gcmd.get('LANE', None)
        LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        LANE.status = 'loading'
        led_cont=LANE.led_index.split(':')
        self.afc_led(self.led_loading, LANE.led_index)
        if LANE.load_state == True and self.hub.filament_present == False:
            if self.hub_cut_active:
                self.hub_cut(lane)
            if not self.heater.can_extrude: #Heat extruder if not at min temp 
                self.gcode.respond_info('Extruder below min_extrude_temp, heating to 5 degrees above min')
                self.gcode.run_script_from_command('M109 S' + str((self.heater.min_extrude_temp) + 5))
            LANE.do_enable(True)
            LANE.move( LANE.dist_hub, self.short_moves_speed, self.short_moves_accel)
            hub_attempts = 0
            while self.hub.filament_present == False:
                LANE.move( self.short_move_dis, self.short_moves_speed, self.short_moves_accel)
                hub_attempts += 1
                time.sleep(0.1)
                #callout if filament doesn't go past hub during load
                if hub_attempts > 10:
                    message = (' FAILED TO LOAD ' + lane.upper() + ' PAST HUB, CHECK FILAMENT PATH\n||=====||==>--||-----||\nTRG   LOAD   HUB   TOOL')
                    self.gcode.respond_info(message)
                    #self.handle_lane_failure(LANE, lane, message)
                    break
            LANE.move( self.afc_bowden_length, self.long_moves_speed, self.long_moves_accel)
            LANE.extruder_stepper.sync_to_extruder(LANE.extruder_name)
            tool_attempts = 0
            while self.tool.filament_present == False:
                tool_attempts += 1
                pos = self.toolhead.get_position()
                pos[3] += self.short_move_dis
                self.toolhead.manual_move(pos, self.tool_load_speed)
                self.toolhead.wait_moves()
                time.sleep(0.1)
                #callout if filament doesn't reach toolhead
                if tool_attempts > 20:
                    message = (' FAILED TO LOAD ' + lane.upper() + ' TO TOOL, CHECK FILAMENT PATH\n||=====||====||==>--||\nTRG   LOAD   HUB   TOOL')
                    self.gcode.respond_info(message)
                    self.gcode.respond_info('unloading ' + lane.upper())
                    untool_attempts = 0
                    LANE.assist(-1)
                    while self.hub.filament_present == True:
                        untool_attempts += 1
                        pos = self.toolhead.get_position()
                        pos[3] += self.short_move_dis * -1
                        self.toolhead.manual_move(pos, self.tool_load_speed)
                        self.toolhead.wait_moves()
                        time.sleep(0.1)
                        if untool_attempts > (self.afc_bowden_length/self.short_move_dis)+3:
                            message = (' FAILED TO CLEAR LINE, ' + lane.upper() + ' CHECK FILAMENT PATH\n')
                            self.gcode.respond_info(message)
                            self.failure = True
                            break
                    self.failure = True
                    LANE.assist(0)
                    LANE.extruder_stepper.sync_to_extruder(None)
                    if LANE.load_state == True:
                        x = 0
                        while LANE.load_state == True:
                            if self.hub.filament_present == True:
                                LANE.assist(-1)
                            else:
                                LANE.assist(0)

                            LANE.move( self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
                            x += 1
                            if self.hub.filament_present == True:
                                LANE.assist(0)
                            time.sleep(0.1)
                            #callout if filament can't be retracted before extruder load switch
                            if x > 30:
                                message = (' FAILED TO RESET EXTRUDER\n||=====||=x--||-----||\nTRG   LOAD   HUB   TOOL')
                                self.handle_lane_failure(LANE, lane, message)
                                break

                        x = 0
                        while LANE.load_state == False:
                            LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                            x += 1
                            time.sleep(0.1)
                            #callout if filament is past trigger but can't be brought past extruder
                            if x > 10:
                                message = (' FAILED TO RELOAD, CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                                self.handle_lane_failure(LANE, lane, message)
                                break
                    break
            if self.failure == False:
                pos = self.toolhead.get_position()
                pos[3] += self.tool_stn
                self.toolhead.manual_move(pos, self.tool_load_speed)
                self.toolhead.wait_moves()
                self.printer.lookup_object('AFC_stepper ' + lane).status = 'tool'
                self.lanes[LANE.unit][LANE.name]['tool_loaded'] = True

                self.save_vars()

                self.current = lane
                LANE = self.printer.lookup_object('AFC_stepper ' + lane)
                self.afc_led(self.led_tool_loaded, LANE.led_index)
                if self.poop:
                    self.gcode.run_script_from_command(self.poop_cmd)
                    if self.wipe:
                        self.gcode.run_script_from_command(self.wipe_cmd)
                if self.kick:
                    self.gcode.run_script_from_command(self.kick_cmd)
                if self.wipe:
                    self.gcode.run_script_from_command(self.wipe_cmd)
            if self.failure:
                self.gcode.run_script_from_command('PAUSE')
                self.afc_led(self.led_fault, LANE.led_index)
        else:
            #callout if hub is triggered when trying to load
            if self.hub.filament_present == True:
                msg = ('HUB NOT CLEAR TRYING TO LOAD ' + lane.upper() + '\n||-----||----|x|-----||\nTRG   LOAD   HUB   TOOL')
                self.respond_error(msg, raise_error=False)
                self.gcode.run_script_from_command('PAUSE')
                self.afc_led(self.led_ready, LANE.led_index)
            #callout if lane is not ready when trying to load
            if LANE.load_state == False:
                msg = (lane.upper() + ' NOT READY' + '\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                self.respond_error(msg, raise_error=False)
                self.gcode.run_script_from_command('PAUSE')
                self.afc_led(self.led_not_ready, LANE.led_index)

    cmd_TOOL_UNLOAD_help = "Unload from tool head"
    def cmd_TOOL_UNLOAD(self, gcmd):
        if self.current == None:
            return
        #self.toolhead = self.printer.lookup_object('toolhead')
        pos = self.toolhead.get_position()
        pos[2] += self.z_hop
        self.toolhead.manual_move(pos, self.tool_unload_speed)
        self.toolhead.wait_moves()
        time.sleep(0.1)

        extruder = self.toolhead.get_extruder() #Get extruder
        self.heater = extruder.get_heater() #Get extruder heater
        lane = gcmd.get('LANE', self.current)

        LANE = self.printer.lookup_object('AFC_stepper '+ lane)
        LANE.status = 'unloading'
        led_cont = LANE.led_index.split(':')
        self.afc_led(self.led_unloading, LANE.led_index)
        LANE.extruder_stepper.sync_to_extruder(LANE.extruder_name)
        
        if not self.heater.can_extrude: #Heat extruder if not at min temp 
            self.gcode.respond_info('Extruder below min_extrude_temp, heating to 5 degrees above min')
            self.gcode.run_script_from_command('M109 S' + str((self.heater.min_extrude_temp) + 5))
            
        if self.tool_cut_active:
            self.gcode.run_script_from_command(self.tool_cut_cmd)
            if self.park:
                self.gcode.run_script_from_command(self.park_cmd)

        if self.form_tip:
            if self.park: self.gcode.run_script_from_command(self.park_cmd)
            if self.form_tip_cmd == "AFC":
                self.afc_tip_form()
            else:
                self.gcode.run_script_from_command(self.form_tip_cmd)

        while self.tool.filament_present == True:
            pos = self.toolhead.get_position()
            pos[3] += self.tool_stn_unload * -1
            self.toolhead.manual_move(pos, self.tool_unload_speed)
            self.toolhead.wait_moves()
            time.sleep(0.1)
        if self.tool_sensor_after_extruder >0:
            pos = self.toolhead.get_position()
            pos[3] += self.tool_sensor_after_extruder * -1
            self.toolhead.manual_move(pos, self.tool_unload_speed)
            self.toolhead.wait_moves()
            
        LANE.extruder_stepper.sync_to_extruder(None)
        LANE.assist(-1)
        LANE.move( self.afc_bowden_length * -1, self.long_moves_speed, self.long_moves_accel)
        x = 0
        while self.hub.filament_present == True:
            LANE.move( self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
            x += 1
            time.sleep(0.1)
            # callout if while unloading, filament doesn't move past HUB
            if x > 20:
                msg = ('HUB NOT CLEARING ' + lane.upper() + '\n||=====||====|x|-----||\nTRG   LOAD   HUB   TOOL')
                self.respond_error(msg, raise_error=False)
                LANE.assist(0)
                return
        LANE.assist( 0)
        self.lanes[LANE.unit][LANE.name]['tool_loaded'] = False
        self.save_vars()
        self.printer.lookup_object('AFC_stepper ' + lane).status = 'tool'
        time.sleep(1)
        x = 0
        while LANE.load_state == False and LANE.prep_state == True:
            LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
            x += 1
            time.sleep(0.1)
            #callout if filament is past trigger but can't be brought past extruder
            if x > 10:
                message = (' FAILED TO RELOAD CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                self.handle_lane_failure(LANE, lane, message)
                break
        self.afc_led(self.led_ready, LANE.led_index)
        LANE.status = None
        self.current = None
        LANE.do_enable(False)
    
    cmd_CHANGE_TOOL_help = "change filaments in tool head"
    def cmd_CHANGE_TOOL(self, gcmd):
        #self.toolhead = self.printer.lookup_object('toolhead')
        lane = gcmd.get('LANE', None)
        if lane != self.current:
            if self.current != None:
                self.gcode.run_script_from_command('TOOL_UNLOAD LANE=' + self.current)
            self.gcode.run_script_from_command('TOOL_LOAD LANE=' + lane)

    def hub_cut(self, lane):
        CUR_LANE=self.printer.lookup_object('AFC_stepper '+lane)
        # Prep the servo for cutting.
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_prep_angle))
        # Load the lane until the hub is triggered.
        while self.hub.filament_present == False:
            CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
        # Go back, to allow the `hub_cut_dist` to be accurate.
        CUR_LANE.move( -self.hub_move_dis*4, self.short_moves_speed, self.short_moves_accel)
        # Feed the `hub_cut_dist` amount.
        CUR_LANE.move( self.hub_cut_dist, self.short_moves_speed, self.short_moves_accel)
        # Have a snooze
        time.sleep(0.5)
        # Choppy Chop
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_clip_angle))
        if self.hub_cut_confirm == 1:
            # KitKat Break
            time.sleep(0.5)
            # ReChop, To be doubly choppy sure.
            self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_prep_angle))
            time.sleep(1.0)
            self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_clip_angle))
        # Longer Snooze
        time.sleep(1)
        # Align bowden tube (reset)
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_pass_angle))
        # Retract lane by `hub_cut_clear`.
        CUR_LANE.move( -self.hub_cut_clear, self.short_moves_speed, self.short_moves_accel)

    cmd_HUB_CUT_TEST_help = "Test the cutting sequence of the hub cutter, expects LANE=legN"
    def cmd_HUB_CUT_TEST(self, gcmd):
        lane = gcmd.get('LANE', None)
        self.gcode.respond_info('Testing Hub Cut on Lane: ' + lane)
        self.hub_cut(lane)
        self.gcode.respond_info('Done!')
        
    def get_status(self, eventtime):
        str = {}
        
        # Try to get hub filament sensor, if lookup fails default to None
        try: self.hub = self.printer.lookup_object('filament_switch_sensor hub').runout_helper
        except: self.hub = None
        
        # Try to get tool filament sensor, if lookup fails default to None
        try: self.tool=self.printer.lookup_object('filament_switch_sensor tool').runout_helper
        except: self.tool = None
        numoflanes = 0
        for UNIT in self.lanes.keys():
            str[UNIT]={}
            for NAME in self.lanes[UNIT].keys():
                LANE=self.printer.lookup_object('AFC_stepper '+ NAME)
                str[UNIT][NAME]={}
                str[UNIT][NAME]['LANE'] = LANE.index
                str[UNIT][NAME]['load'] = bool(LANE.load_state)
                str[UNIT][NAME]["prep"]=bool(LANE.prep_state)
                str[UNIT][NAME]["material"]=self.lanes[UNIT][NAME]['material']
                str[UNIT][NAME]["spool_id"]=self.lanes[UNIT][NAME]['spool_id']
                str[UNIT][NAME]["color"]=self.lanes[UNIT][NAME]['color']
                numoflanes +=1 
        str["system"]={}   
        str["system"]['current_load']= self.current
        # Set status of filament sensors if they exist, false if sensors are not found
        str["system"]['tool_loaded'] = True == self.tool.filament_present if self.tool is not None else False
        str["system"]['hub_loaded']  = True == self.hub.filament_present  if self.hub is not None else False
        str["system"]['num_units'] = len(self.lanes)
        str["system"]['num_lanes'] = numoflanes
        return str
    
    cmd_SPOOL_ID_help = "LINK SPOOL into hub"
    def cmd_SPOOL_ID(self, gcmd):
        return

    def afc_extrude(self, distance, speed):
        pos = self.toolhead.get_position()
        pos[3] += distance
        self.toolhead.manual_move(pos, speed)
        self.toolhead.wait_moves()
        time.sleep(0.1)

    def afc_tip_form(self):
        step = 1
        if self.ramming_volume > 0:
            self.gcode.respond_info('AFC-TIP-FORM: Step ' + step + ': Ramming')
            ratio = ramming_volume / 23
            self.afc_extrude(0.5784 * ratio, 299)
            self.afc_extrude(0.5834 * ratio, 302)
            self.afc_extrude(0.5918 * ratio, 306)
            self.afc_extrude(0.6169 * ratio, 319)
            self.afc_extrude(0.3393 * ratio, 350)
            self.afc_extrude(0.3363 * ratio, 350)
            self.afc_extrude(0.7577 * ratio, 392)
            self.afc_extrude(0.8382 * ratio, 434)
            self.afc_extrude(0.7776 * ratio, 469)
            self.afc_extrude(0.1293 * ratio, 469)
            self.afc_extrude(0.9673 * ratio, 501)
            self.afc_extrude(1.0176 * ratio, 527)
            self.afc_extrude(0.5956 * ratio, 544)
            self.afc_extrude(1.0662 * ratio, 552)
            step +=1

        self.gcode.respond_info('AFC-TIP-FORM: Step ' + step + ': Retraction & Nozzle Separation')
        total_retraction_distance = self.cooling_tube_position + self.cooling_tube_length - 15
        self.afc_extrude(-15, self.unloading_speed_start * 60)
        if self.total_retraction_dis > 0:
            self.afc_extrude(.7 * total_retraction_distance, 1.0 * self.unloading_speed)
            self.afc_extrude(.2 * total_retraction_distance, 0.5 * self.unloading_speed)
            self.afc_extrude(.7 * total_retraction_distance, 0.3 * self.unloading_speed)
        
        if self.toolchange_temp > 0:
            if self.use_skinnydip:
                wait = False
            else:
                wait =  True
            extruder = self.toolhead.get_extruder()
            pheaters = self.printer.lookup_object('heaters')
            pheaters.set_temperature(extruder.get_heater(), self.toolchange_temp, wait)

        self.gcode.respond_info('AFC-TIP-FORM: Step ' + step + ': Cooling Moves')
        speed_inc = (self.final_cooling_speed - self.initial_cooling_speed) / (2 * self.cooling_moves - 1)
        for move in range(self.cooling_moves):
            speed = self.initial_cooling_speed + speed_in * move * 2
            self.afc_extrude(self.cooling_tube_length, speed * 60)
            self.afc_extrude(self.cooling_tube_length * -1, (speed + speed_inc) * 60)
        step += 1

        if self.use_skinnydip:
            self.gcode.respond_info('AFC-TIP-FORM: Step ' + step + ': Skinny Dipping')
            self.afc_extrude(self.skinnydip_distance, self.dip_insertion_speed * 60)
            time.sleep(self.melt_zone_pause)
            self.afc_extrude(self.skinnydip_distance * -1, self.dip_extraction_speed * 60)
            time.sleep(self.cool_zone_pause)
            step += 1

        #M104 S{next_temp}


def load_config(config):         
    return afc(config)
