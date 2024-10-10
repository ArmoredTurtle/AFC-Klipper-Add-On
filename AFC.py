# 8 Track Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import os
import json
from . import AFC_functions
from configparser import Error as error
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
        # tool position when tool change was requested
        self.change_tool_pos = None

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
        
        # TOOL Cutting Settings
        self.tool = ''
        self.tool_cut_active = config.getboolean("tool_cut_active", False)
        self.tool_cut_cmd = config.get('tool_cut_cmd')
        
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
        if self.form_tip_cmd == 'AFC':
            self.afc_tip = AFC_functions.afc_tip_form(config)

        self.hub_cut_active = config.getboolean("hub_cut_active", False)
        if self.hub_cut_active == True:
            self.afc_cut.hub = AFC_functions.afc_hub_cut(config)

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
        self.tool_max_unload_attempts = config.getint('tool_max_unload_attempts', 2)
        self.z_hop =config.getfloat("z_hop", 0)
        self.gcode.register_command('HUB_LOAD', self.cmd_HUB_LOAD, desc=self.cmd_HUB_LOAD_help)
        if self.Type == 'Box_Turtle':
            self.gcode.register_command('LANE_UNLOAD', self.cmd_LANE_UNLOAD, desc=self.cmd_LANE_UNLOAD_help)
        self.gcode.register_command('TOOL_LOAD', self.cmd_TOOL_LOAD, desc=self.cmd_TOOL_LOAD_help)
        self.gcode.register_command('TOOL_UNLOAD', self.cmd_TOOL_UNLOAD, desc=self.cmd_TOOL_UNLOAD_help)
        self.gcode.register_command('CHANGE_TOOL', self.cmd_CHANGE_TOOL, desc=self.cmd_CHANGE_TOOL_help)
        self.gcode.register_command('RESTORE_CHANGE_TOOL_POS', self.cmd_RESTORE_CHANGE_TOOL_POS, desc=self.cmd_RESTORE_CHANGE_TOOL_POS_help)
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
        distance = gcmd.get_float('DISTANCE', 0)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_LANE.move(distance, self.short_moves_speed, self.short_moves_accel)

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

    handle_lane_failure_help = "Get load errors, stop stepper and respond error"
    def handle_lane_failure(self, CUR_LANE, message):
        # Disable the stepper for this lane
        CUR_LANE.do_enable(False)
        msg = (CUR_LANE.name.upper() + ' NOT READY' + message)
        self.respond_error(msg, raise_error=False)
        self.afc_led(self.led_fault, CUR_LANE.led_index)

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

    cmd_TOOL_LOAD_help = "Load lane into tool"
    def cmd_TOOL_LOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        self.TOOL_LOAD(CUR_LANE)

    cmd_TOOL_UNLOAD_help = "Unload from tool head"
    def cmd_TOOL_UNLOAD(self, gcmd):
        lane = gcmd.get('LANE', self.current)
        CUR_LANE = self.printer.lookup_object('AFC_stepper '+ lane)
        self.TOOL_UNLOAD(CUR_LANE)

    cmd_HUB_CUT_TEST_help = "Test the cutting sequence of the hub cutter, expects LANE=legN"
    def cmd_HUB_CUT_TEST(self, gcmd):
        lane = gcmd.get('LANE', None)
        self.gcode.respond_info('Testing Hub Cut on Lane: ' + lane)
        self.hub_cut(lane)
        self.gcode.respond_info('Done!')

    cmd_TEST_help = "Test Assist Motors"
    def cmd_TEST(self, gcmd):
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.respond_error('Must select LANE')
            return
        self.gcode.respond_info('TEST ROUTINE')
        try:
            CUR_LANE = self.printer.lookup_object('AFC_stepper '+lane)
        except error as e:
            self.respond_error(str(e))
            return
        self.gcode.respond_info('Testing at full speed')
        CUR_LANE.assist(-1)
        self.reactor.pause(self.reactor.monotonic() + 1)
        if CUR_LANE.afc_motor_rwd.is_pwm:
            self.gcode.respond_info('Testing at 50 percent speed')
            CUR_LANE.assist(-.5)
            self.reactor.pause(self.reactor.monotonic() + 1)
            self.gcode.respond_info('Testing at 30 percent speed')
            CUR_LANE.assist(-.3)
            self.reactor.pause(self.reactor.monotonic() + 1)
            self.gcode.respond_info('Testing at 10 percent speed')
            CUR_LANE.assist(-.1)
            self.reactor.pause(self.reactor.monotonic() + 1)
        self.gcode.respond_info('Test routine complete')
        CUR_LANE.assist(0)

    cmd_SPOOL_ID_help = "LINK SPOOL into hub"
    def cmd_SPOOL_ID(self, gcmd):
        return

    cmd_PREP_help = "Prep AFC"
    def cmd_PREP(self, gcmd):
        while self.printer.state_message != 'Printer is ready':
            self.reactor.pause(self.reactor.monotonic() + 1)
        if os.path.exists(self.VarFile) and os.stat(self.VarFile).st_size > 0:
            try: self.lanes=json.load(open(self.VarFile))
            except IOError: self.lanes={}
            except ValueError: self.lanes={}
        else:
            self.lanes={}
        temp=[]
        for PO in self.printer.objects:
            if 'AFC_stepper' in PO and 'tmc' not in PO:
                LANE=self.printer.lookup_object(PO)
                temp.append(LANE.name)
                if LANE.unit not in self.lanes: self.lanes[LANE.unit]={}
                if LANE.name not in self.lanes[LANE.unit]: self.lanes[LANE.unit][LANE.name]={}
                if 'index' not in self.lanes[LANE.unit][LANE.name]: self.lanes[LANE.unit][LANE.name]['index'] = LANE.index
                if 'material' not in self.lanes[LANE.unit][LANE.name]: self.lanes[LANE.unit][LANE.name]['material']=''
                if 'spool_id' not in self.lanes[LANE.unit][LANE.name]: self.lanes[LANE.unit][LANE.name]['spool_id']=''
                if 'color' not in self.lanes[LANE.unit][LANE.name]: self.lanes[LANE.unit][LANE.name]['color']=''
                if 'tool_loaded' not in self.lanes[LANE.unit][LANE.name]: self.lanes[LANE.unit][LANE.name]['tool_loaded'] = False
                if 'hub_loaded' not in self.lanes[LANE.unit][LANE.name]: self.lanes[LANE.unit][LANE.name]['hub_loaded'] = False
                if self.lanes[LANE.unit][LANE.name]['tool_loaded'] == True: self.current = LANE.name
        tmp=[]
        for UNIT in self.lanes.keys():
            for lanecheck in self.lanes[UNIT].keys():
                if lanecheck not in temp: tmp.append(lanecheck)
            for erase in tmp:
                del self.lanes[UNIT][erase]
        self.save_vars()
        if self.Type == 'Box_Turtle':
            logo ='R  _____     ____\n'
            logo+='E /      \  |  o | \n'
            logo+='A |       |/ ___/ \n'
            logo+='D |_________/     \n'
            logo+='Y |_|_| |_|_|\n'
            logo_error ='E  _ _   _ _\n'
            logo_error+='R |_|_|_|_|_|\n'
            logo_error+='R |         \____\n'
            logo_error+='O |              \ \n'
            logo_error+='R |          |\ X |\n'
            logo_error+='! \_________/ |___|\n'
            for UNIT in self.lanes.keys():
                self.gcode.respond_info(self.Type + ' ' + UNIT +' Prepping lanes')
                for LANE in self.lanes[UNIT].keys():
                    CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
                    CUR_LANE.extruder_stepper.sync_to_extruder(None)
                    CUR_LANE.move( -5, self.short_moves_speed, self.short_moves_accel, True)
                    CUR_LANE.move( 5, self.short_moves_speed, self.short_moves_accel, True)
                    # create T codes for macro use
                    self.gcode.register_mux_command('T' + str(CUR_LANE.index - 1), "LANE", CUR_LANE.name, self.cmd_CHANGE_TOOL, desc=self.cmd_CHANGE_TOOL_help)
                    if CUR_LANE.prep_state == False: self.afc_led(self.led_not_ready, CUR_LANE.led_index)

            error_string = "Error: Filament switch sensor {} not found in config file"
            try: self.hub=self.printer.lookup_object('filament_switch_sensor hub').runout_helper
            except: self.respond_error(error_string.format("hub"), raise_error=True)
            try: self.tool=self.printer.lookup_object('filament_switch_sensor tool').runout_helper
            except: self.respond_error(error_string.format("tool"), raise_error=True)
            check_success = False
            if self.current == None:
                for UNIT in self.lanes.keys():
                    for LANE in self.lanes[UNIT].keys():
                        check_success = True
                        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
                        CUR_LANE.do_enable(True)
                        if self.hub.filament_present == True and CUR_LANE.load_state == True:
                            num_tries = 0
                            while CUR_LANE.load_state == True:
                                CUR_LANE.move( self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
                                num_tries += 1
                                #callout if filament can't be retracted before extruder load switch
                                if num_tries > (self.afc_bowden_length/self.short_move_dis) + 3:
                                    message = (' FAILED TO RESET EXTRUDER\n||=====||=x--||-----||\nTRG   LOAD   HUB   TOOL')
                                    self.handle_lane_failure(CUR_LANE, message)
                                    check_success = False
                                    break
                            num_tries = 0
                            while CUR_LANE.load_state == False:
                                CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                                num_tries += 1
                                #callout if filament is past trigger but can't be brought past extruder
                                if num_tries > 20:
                                    message = (' FAILED TO RELOAD, CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                                    self.handle_lane_failure(CUR_LANE, message)
                                    check_success = False
                                    break
                            if check_success == True:
                                self.afc_led(self.led_ready, CUR_LANE.led_index)
                        else:
                            if CUR_LANE.prep_state == True:
                                num_tries = 0
                                while CUR_LANE.load_state == False:
                                    CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                                    num_tries += 1
                                    #callout if filament is past trigger but can't be brought past extruder
                                    if num_tries > 20:
                                        message = (' CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                                        self.handle_lane_failure(CUR_LANE, message)
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
                                    CUR_LANE.status = 'Loaded'
                                    msg +=" AND LOADED"
                                else:
                                    msg +=" NOT LOADED"
                            else:
                                if CUR_LANE.load_state == True:
                                    CUR_LANE.status = None
                                    msg +=" NOT READY"
                                    CUR_LANE.do_enable(False)
                                    msg = 'CHECK FILAMENT Prep: False - Load: True'
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
                        if self.current == CUR_LANE.name:
                            if self.tool.filament_present == False and self.hub.filament_present == True:
                                untool_attempts = 0
                                while CUR_LANE.load_state == True:
                                    CUR_LANE.move( self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
                                    untool_attempts += 1
                                    if untool_attempts > (self.afc_bowden_length/self.short_move_dis)+3:
                                        message = (' FAILED TO CLEAR LINE, ' + CUR_LANE.name.upper() +' CHECK FILAMENT PATH\n')
                                        self.gcode.respond_info(message)
                                        break
                                CUR_LANE.status = None
                                self.current = None
                                num_tries = 0
                                while CUR_LANE.load_state == False:
                                    CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                                    if num_tries > 20:
                                        message = (' FAILED TO LOAD ' + CUR_LANE.name.upper() + ' CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                                        self.gcode.respond_info(message)
                                        break
                                if CUR_LANE.load_state:
                                    CUR_LANE.status = 'Loaded'
                                self.current = None
                            else:
                                CUR_LANE.status = 'Tooled'
                                CUR_LANE = self.printer.lookup_object('AFC_stepper ' + self.current)
                                CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
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
                                    CUR_LANE.do_enable(False)
                                    msg = 'CHECK FILAMENT Prep: False - Load: True'
                                else:
                                    msg += 'EMPTY READY FOR SPOOL'
                            if self.current == lane:
                                msg += ' IN TOOL'
                            # Setting lane to prepped so that loading will happen once user tries to load filament
                            CUR_LANE.set_afc_prep_done()
                            CUR_LANE.do_enable(False)
                            self.gcode.respond_info(CUR_LANE.name.upper() + ' ' + msg)
        if check_success == True:
            self.gcode.respond_info(logo)
        else:
            self.gcode.respond_info(logo_error)
        # Call out if all lanes are clear but hub is not
        if self.hub.filament_present == True and self.tool.filament_present == False:
            msg = ('LANES READY, HUB NOT CLEAR\n||-----||----|x|-----||\nTRG   LOAD   HUB   TOOL')
            self.respond_error(msg, raise_error=False)

    # HUB COMMANDS
    cmd_HUB_LOAD_help = "Load lane into hub"
    def cmd_HUB_LOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        if CUR_LANE.load_state == False:
            CUR_LANE.do_enable(True)
            while CUR_LANE.load_state == False:
                CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
        CUR_LANE.move(CUR_LANE.dist_hub, self.short_moves_speed, self.short_moves_accel)
        while self.hub.filament_present == False:
            CUR_LANE.move(self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
        while self.hub.filament_present == True:
            CUR_LANE.move(self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
        CUR_LANE.status = 'Hubed'
        CUR_LANE.do_enable(False)

    cmd_LANE_UNLOAD_help = "Unload lane from extruder"
    def cmd_LANE_UNLOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        CUR_LANE = self.printer.lookup_object('AFC_stepper '+ lane)
        if CUR_LANE.name != self.current:
            CUR_LANE.do_enable(True)
            if CUR_LANE.dist_hub:
                CUR_LANE.move(CUR_LANE.dist_hub * -1, self.short_moves_speed, self.short_moves_accel)
            CUR_LANE.dist_hub = False
            while CUR_LANE.load_state == True:
               CUR_LANE.move( self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
            CUR_LANE.move( self.hub_move_dis * -5, self.short_moves_speed, self.short_moves_accel)
            CUR_LANE.do_enable(False)
            CUR_LANE.status = None
        else:
            self.gcode.respond_info('LANE ' + CUR_LANE.name + ' IS TOOL LOADED')

    def TOOL_LOAD(self, CUR_LANE):
        if CUR_LANE == None:
            return
        self.failure = False
        extruder = self.toolhead.get_extruder() #Get extruder
        self.heater = extruder.get_heater() #Get extruder heater
        CUR_LANE.status = 'loading'
        self.afc_led(self.led_loading, CUR_LANE.led_index)
        if CUR_LANE.load_state == True and self.hub.filament_present == False:
            if self.hub_cut_active:
                self.hub_cut(CUR_LANE.name)
            if not self.heater.can_extrude: #Heat extruder if not at min temp
                if self.heater.target_temp >= self.heater.min_extrude_temp:
                    self.gcode.respond_info('Extruder temp is still below min_extrude_temp, waiting for it to finish heating.')
                    self.gcode.run_script_from_command('M109 S' + str((self.heater.target_temp)))
                else:
                    self.gcode.respond_info('Extruder below min_extrude_temp, heating to 5 degrees above min')
                    self.gcode.run_script_from_command('M109 S' + str((self.heater.min_extrude_temp) + 5))
            CUR_LANE.do_enable(True)
            if CUR_LANE.hub_load == False:
                CUR_LANE.move(CUR_LANE.dist_hub, self.short_moves_speed, self.short_moves_accel)
            hub_attempts = 0
            while self.hub.filament_present == False:
                CUR_LANE.move( self.short_move_dis, self.short_moves_speed, self.short_moves_accel)
                hub_attempts += 1
                #callout if filament doesn't go past hub during load
                if hub_attempts > 20:
                    self.pause_print()
                    message = (' PAST HUB, CHECK FILAMENT PATH\n||=====||==>--||-----||\nTRG   LOAD   HUB   TOOL')
                    self.handle_lane_failure(CUR_LANE, message)
                    return
            CUR_LANE.move( self.afc_bowden_length, self.long_moves_speed, self.long_moves_accel)
            CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
            tool_attempts = 0
            while self.tool.filament_present == False:
                tool_attempts += 1
                pos = self.toolhead.get_position()
                pos[3] += self.short_move_dis
                self.toolhead.manual_move(pos, self.tool_load_speed)
                self.toolhead.wait_moves()
                #callout if filament doesn't reach toolhead
                if tool_attempts > 20:
                    message = (' FAILED TO LOAD ' + CUR_LANE.name.upper() + ' TO TOOL, CHECK FILAMENT PATH\n||=====||====||==>--||\nTRG   LOAD   HUB   TOOL')
                    self.gcode.respond_info(message)
                    self.gcode.respond_info('unloading ' + CUR_LANE.name.upper())
                    untool_attempts = 0
                    while self.hub.filament_present == True:
                        untool_attempts += 1
                        pos = self.toolhead.get_position()
                        pos[3] += self.short_move_dis * -1
                        self.toolhead.manual_move(pos, self.tool_load_speed)
                        self.toolhead.wait_moves()
                        if untool_attempts > (self.afc_bowden_length/self.short_move_dis)+3:
                            message = (' FAILED TO CLEAR LINE, ' + CUR_LANE.name.upper() + ' CHECK FILAMENT PATH\n')
                            self.gcode.respond_info(message)
                            self.failure = True
                            break
                    self.failure = True
                    CUR_LANE.extruder_stepper.sync_to_extruder(None)
                    if CUR_LANE.load_state == True:
                        x = 0
                        while CUR_LANE.load_state == True:
                            CUR_LANE.move( self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
                            x += 1
                            #callout if filament can't be retracted before extruder load switch
                            if x > 30:
                                message = (' FAILED TO RESET EXTRUDER\n||=====||=x--||-----||\nTRG   LOAD   HUB   TOOL')
                                self.handle_lane_failure(CUR_LANE, message)
                                break
                        x = 0
                        while CUR_LANE.load_state == False:
                            CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                            x += 1
                            #callout if filament is past trigger but can't be brought past extruder
                            if x > 10:
                                message = (' FAILED TO RELOAD, CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                                self.handle_lane_failure(CUR_LANE, message)
                                break
                    break
            if self.failure == False:
                CUR_LANE.status = 'Tooled'
                pos = self.toolhead.get_position()
                pos[3] += self.tool_stn
                self.toolhead.manual_move(pos, self.tool_load_speed)
                self.toolhead.wait_moves()
                self.printer.lookup_object('AFC_stepper ' + CUR_LANE.name).status = 'tool'
                self.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = True
                self.save_vars()
                self.current = CUR_LANE.name
                self.afc_led(self.led_tool_loaded, CUR_LANE.led_index)
                if self.poop:
                    self.gcode.run_script_from_command(self.poop_cmd)
                    if self.wipe:
                        self.gcode.run_script_from_command(self.wipe_cmd)
                if self.kick:
                    self.gcode.run_script_from_command(self.kick_cmd)
                if self.wipe:
                    self.gcode.run_script_from_command(self.wipe_cmd)
            if self.failure:
                self.pause_print()
                self.afc_led(self.led_fault, CUR_LANE.led_index)
        else:
            #callout if hub is triggered when trying to load
            if self.hub.filament_present == True:
                msg = ('HUB NOT CLEAR TRYING TO LOAD ' + CUR_LANE.name.upper() + '\n||-----||----|x|-----||\nTRG   LOAD   HUB   TOOL')
                self.respond_error(msg, raise_error=False)
                self.gcode.run_script_from_command('PAUSE')
                self.afc_led(self.led_ready, CUR_LANE.led_index)
            #callout if lane is not ready when trying to load
            if CUR_LANE.load_state == False:
                msg = (CUR_LANE.name.upper() + ' NOT READY' + '\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                self.respond_error(msg, raise_error=False)
                self.gcode.run_script_from_command('PAUSE')
                self.afc_led(self.led_not_ready, CUR_LANE.led_index)

    def TOOL_UNLOAD(self, CUR_LANE):
        if CUR_LANE == None:
            return
        #self.toolhead = self.printer.lookup_object('toolhead')
        pos = self.toolhead.get_position()
        pos[3] -= 2
        self.toolhead.manual_move(pos, self.tool_unload_speed)
        self.toolhead.wait_moves()
        pos[2] += self.z_hop
        self.toolhead.manual_move(pos, self.tool_unload_speed)
        self.toolhead.wait_moves()
        extruder = self.toolhead.get_extruder() #Get extruder
        self.heater = extruder.get_heater() #Get extruder heater
        CUR_LANE.status = 'unloading'
        self.afc_led(self.led_unloading, CUR_LANE.led_index)
        CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
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
        num_tries = 0
        while self.tool.filament_present == True:
            num_tries += 1
            if num_tries > self.tool_max_unload_attempts:
                self.pause_print()
                msg = ('FAILED TO UNLOAD ' + CUR_LANE.name.upper() + '. FILAMENT STUCK IN TOOLHEAD.\n||=====||====||====|x|\nTRG   LOAD   HUB   TOOL')
                self.handle_lane_failure(CUR_LANE, msg)
                return
            pos = self.toolhead.get_position()
            pos[3] += self.tool_stn_unload * -1
            self.toolhead.manual_move(pos, self.tool_unload_speed)
            self.toolhead.wait_moves()
        if self.tool_sensor_after_extruder >0:
            pos = self.toolhead.get_position()
            pos[3] += self.tool_sensor_after_extruder * -1
            self.toolhead.manual_move(pos, self.tool_unload_speed)
            self.toolhead.wait_moves()
        CUR_LANE.extruder_stepper.sync_to_extruder(None)
        CUR_LANE.move( self.afc_bowden_length * -1, self.long_moves_speed, self.long_moves_accel, True)
        num_tries = 0
        while self.hub.filament_present == True:
            CUR_LANE.move(self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel, True)
            num_tries += 1
            # callout if while unloading, filament doesn't move past HUB
            if num_tries > (self.afc_bowden_length/self.short_move_dis):
                self.pause_print()
                msg = (' HUB NOT CLEARING' + '\n||=====||====|x|-----||\nTRG   LOAD   HUB   TOOL')
                self.handle_lane_failure(CUR_LANE, msg)
                return

        # retract a little more...helps to clear strings from the hub
        # ...until either we've moved park_dist OR we passed the load switch
        move_dist = 0
        while CUR_LANE.load_state == True and move_dist < CUR_LANE.park_dist:
            move_dist += min(self.short_move_dis, CUR_LANE.park_dist - move_dist)
            CUR_LANE.move(self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel, True)

        CUR_LANE.hub_load = True
        self.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = False
        self.save_vars()
        num_tries = 0
        while CUR_LANE.load_state == False and CUR_LANE.prep_state == True:
            CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
            num_tries += 1
            #callout if filament is past trigger but can't be brought past extruder
            if num_tries > 10:
                self.pause_print()
                message = (' FAILED TO RELOAD CHECK FILAMENT AT TRIGGER\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                self.handle_lane_failure(CUR_LANE, message)
                return
        self.afc_led(self.led_ready, CUR_LANE.led_index)
        CUR_LANE.status = None
        self.current = None
        CUR_LANE.do_enable(False)

    cmd_CHANGE_TOOL_help = "change filaments in tool head"
    def cmd_CHANGE_TOOL(self, gcmd):
        #self.toolhead = self.printer.lookup_object('toolhead')
        lane = gcmd.get('LANE', None)
        if lane != self.current:
            store_pos = self.toolhead.get_position()
            if self.is_printing() and not self.is_paused():
                self.change_tool_pos = store_pos
            if self.current != None:
                CUR_LANE = self.printer.lookup_object('AFC_stepper ' + self.current)
                self.TOOL_UNLOAD(CUR_LANE)
            CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
            self.TOOL_LOAD(CUR_LANE)
            newpos = self.toolhead.get_position()
            newpos[2] = store_pos[2]
            self.toolhead.manual_move(newpos, self.tool_unload_speed)
            self.toolhead.wait_moves()
            if self.is_printing() and not self.is_paused():
                self.change_tool_pos = None

    cmd_RESTORE_CHANGE_TOOL_POS_help = "change filaments in tool head"
    def cmd_RESTORE_CHANGE_TOOL_POS(self, gcmd):
        if self.change_tool_pos:
            restore_pos = self.change_tool_pos[:3]
            self.toolhead.manual_move(restore_pos, self.tool_unload_speed)
            self.toolhead.wait_moves()

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

    def pause_print(self):
        if self.is_printing() and not self.is_paused():
            self.gcode.run_script_from_command('PAUSE')

    def is_printing(self):
        eventtime = self.reactor.monotonic()
        idle_timeout = self.printer.lookup_object("idle_timeout")
        return idle_timeout.get_status(eventtime)["state"] == "Printing"

    def is_paused(self):
        eventtime = self.reactor.monotonic()
        pause_resume = self.printer.lookup_object("pause_resume")
        return bool(pause_resume.get_status(eventtime)["is_paused"])

    def afc_led (self, status, idx=None):
        afc_object = 'AFC_led '+ idx.split(':')[0]
        # Try to find led object, if not found print error to console for user to see
        try: led = self.printer.lookup_object(afc_object)
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
            if hasattr(led.led_helper, "_set_color"):
                set_color_fn = led.led_helper._set_color
                check_transmit_fn = led.led_helper._check_transmit
            else:
                set_color_fn = led.led_helper.set_color
                check_transmit_fn = led.led_helper.check_transmit
            set_color_fn(index, colors)
            if transmit:
                check_transmit_fn(print_time)
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.register_lookahead_callback(lookahead_bgfunc)

def load_config(config):
    return afc(config)
