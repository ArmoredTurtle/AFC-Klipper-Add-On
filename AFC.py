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


def calc_move_time(dist, speed, accel):
    """
    Calculate the movement time and parameters for a given distance, speed, and acceleration.

    This function computes the axis direction, acceleration time, cruise time, and cruise speed
    required to move a specified distance with given speed and acceleration.

    Parameters:
    dist (float): The distance to move.
    speed (float): The speed of the movement.
    accel (float): The acceleration of the movement.

    Returns:
    tuple: A tuple containing:
        - axis_r (float): The direction of the axis (1 for positive, -1 for negative).
        - accel_t (float): The time spent accelerating.
        - cruise_t (float): The time spent cruising at constant speed.
        - speed (float): The cruise speed.
    """
    axis_r = 1.
    if dist < 0.:
        axis_r = -1.
        dist = -dist
    if not accel or not dist:
        return axis_r, 0., dist / speed, speed
    max_cruise_v2 = dist * accel
    if max_cruise_v2 < speed**2:
        speed = math.sqrt(max_cruise_v2)
    accel_t = speed / accel
    accel_decel_d = accel_t * speed
    cruise_t = (dist - accel_decel_d) / speed
    return axis_r, accel_t, cruise_t, speed

class afc:
    def __init__(self, config):
        self.config = config
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        ffi_main, ffi_lib = chelper.get_ffi()
        self.trapq = ffi_main.gc(ffi_lib.trapq_alloc(), ffi_lib.trapq_free)
        self.trapq_append = ffi_lib.trapq_append
        self.trapq_finalize_moves = ffi_lib.trapq_finalize_moves
        self.stepper_kinematics = ffi_main.gc(
            ffi_lib.cartesian_stepper_alloc(b'x'), ffi_lib.free)

        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        self.gcode = self.printer.lookup_object('gcode')
        self.VarFile = config.get('VarFile')
        self.Type = config.get('Type')
        self.current = ''
        self.lanes = {}
        
        # SPOOLMAN
        
        self.spoolman = config.getboolean('spoolman', False)
        if self.spoolman:
            self.spoolman_filament={}
            #response = urlopen("http://192.168.1.50:7912/api/v1/filament")
            #data=json.loads(response.read())
            #for x in range(len(data)):
            #    self.spoolman_filament[str(data[x]['id'])]={"name": data[x]['name'],"material": data[x]['material'],"color": data[x]['color_hex']}
                
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
        self.hub_clear = config.getfloat("hub_clear", 50)
        self.hub = ''

        # HUB CUTTER
        self.hub_cut_active = config.getfloat("hub_cut_active", 0)
        self.hub_cut_dist = config.getfloat("hub_cut_dist", 200)
        self.hub_cut_clear = config.getfloat("hub_cut_clear", 120)
        self.hub_cut_min_length = config.getfloat("hub_cut_min_length", 200)
        self.hub_cut_servo_pass_angle = config.getfloat("hub_cut_servo_pass_angle", 0)
        self.hub_cut_servo_clip_angle = config.getfloat("hub_cut_servo_clip_angle", 160)
        self.hub_cut_servo_prep_angle = config.getfloat("hub_cut_servo_prep_angle", 75)
        self.hub_cut_active = config.getfloat("hub_cut_active", 0)

        # TOOL Cutting Settings
        self.tool = ''
        self.tool_cut_active = config.getfloat("tool_cut_active", 0)
        self.tool_cut_cmd = config.get('tool_cut_cmd')

        # CHOICES
        self.park = config.getfloat("park", 0)
        self.park_cmd = config.get('park_cmd', None)
        self.kick = config.getfloat("kick", 0)
        self.kick_cmd = config.get('kick_cmd', None)
        self.wipe = config.getfloat("wipe", 0)
        self.wipe_cmd = config.get('wipe_cmd', None)
        self.poop = config.getfloat("poop", 0)
        self.poop_cmd = config.get('poop_cmd', None)
        self.form_tip = config.getfloat("form_tip", 0)
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


        self.gcode.register_command('HUB_LOAD', self.cmd_HUB_LOAD, desc=self.cmd_HUB_LOAD_help)
        if self.Type == 'Box_Turtle':
            self.gcode.register_command('LANE_UNLOAD', self.cmd_LANE_UNLOAD, desc=self.cmd_LANE_UNLOAD_help)

        self.gcode.register_command('TOOL_LOAD', self.cmd_TOOL_LOAD, desc=self.cmd_TOOL_LOAD_help)
        self.gcode.register_command('TOOL_UNLOAD', self.cmd_TOOL_UNLOAD, desc=self.cmd_TOOL_UNLOAD_help)
        self.gcode.register_command('CHANGE_TOOL', self.cmd_CHANGE_TOOL, desc=self.cmd_CHANGE_TOOL_help)
        self.gcode.register_command('PREP', self.cmd_PREP, desc=self.cmd_PREP_help)

        self.gcode.register_command('TEST', self.cmd_TEST, desc=self.cmd_TEST_help)
        self.gcode.register_command('HUB_CUT_TEST', self.cmd_HUB_CUT_TEST, desc=self.cmd_HUB_CUT_TEST_help)

        self.VarFile = config.get('VarFile')
        
        # Get debug and cast to boolean
        self.debug = True == config.get('debug', 0)
    
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

    cmd_TEST_help = "Load lane into hub"
    def cmd_TEST(self, gcmd):
        lane = gcmd.get('LANE', None)
        self.gcode.respond_info('TEST ROUTINE')
        LANE = self.printer.lookup_object('AFC_stepper '+lane)
        self.gcode.respond_info('Testing at full speed')
        self.rewind(LANE,-1)
        time.sleep(4)
        assit_motor=LANE.afc_motor_rwd
        if assit_motor.is_pwm:
            self.gcode.respond_info('Testing at 50 percent speed')
            self.rewind(LANE,-.5)
            time.sleep(4)
            self.gcode.respond_info('Testing at 30 percent speed')
            self.rewind(LANE,-.3)
            time.sleep(4)
            self.gcode.respond_info('Testing at 10 percent speed')
            self.rewind(LANE,-.1)
            time.sleep(4)
            
        self.gcode.respond_info('Test routine complete')
        self.rewind(LANE,0)
        
    def rewind(self, lane, value, is_resend=False):
        if lane.afc_motor_rwd is None:
            return
        if value < 0:
            value *= -1
            assit_motor=lane.afc_motor_rwd
        else:
            if lane.afc_motor_fwd is None:
                assit_motor=lane.afc_motor_rwd
            else:
                assit_motor=lane.afc_motor_fwd
        value /= assit_motor.scale
        if not assit_motor.is_pwm and value not in [0., 1.]:
            if value > 0:
                value = 1
        # Obtain print_time and apply requested settings
        toolhead = self.printer.lookup_object('toolhead')
        if lane.afc_motor_enb is not None:
            if value != 0:
                enable = 1
            else:
                enable = 0
            toolhead.register_lookahead_callback(
            lambda print_time: lane.afc_motor_enb._set_pin(print_time, enable))
            
        toolhead.register_lookahead_callback(
            lambda print_time: assit_motor._set_pin(print_time, value))
        
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

    def afc_move(self, lane, distance, speed, accel):
        """
        Move the specified lane a given distance with specified speed and acceleration.

        This function calculates the movement parameters and commands the stepper motor
        to move the lane accordingly.

        Parameters:
        lane (str): The lane identifier.
        distance (float): The distance to move.
        speed (float): The speed of the movement.
        accel (float): The acceleration of the movement.
        """
        name = 'AFC_stepper ' + lane
        LANE = self.printer.lookup_object(name).extruder_stepper
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.flush_step_generation()
        prev_sk = LANE.stepper.set_stepper_kinematics(self.stepper_kinematics)
        prev_trapq = LANE.stepper.set_trapq(self.trapq)
        LANE.stepper.set_position((0., 0., 0.))
        axis_r, accel_t, cruise_t, cruise_v = calc_move_time(distance, speed, accel)
        print_time = toolhead.get_last_move_time()
        self.trapq_append(self.trapq, print_time, accel_t, cruise_t, accel_t,
                          0., 0., 0., axis_r, 0., 0., 0., cruise_v, accel)
        print_time = print_time + accel_t + cruise_t + accel_t
        LANE.stepper.generate_steps(print_time)
        self.trapq_finalize_moves(self.trapq, print_time + 99999.9,
                                  print_time + 99999.9)
        LANE.stepper.set_trapq(prev_trapq)
        LANE.stepper.set_stepper_kinematics(prev_sk)
        toolhead.note_mcu_movequeue_activity(print_time)
        toolhead.dwell(accel_t + cruise_t + accel_t)
        toolhead.flush_step_generation()

    cmd_PREP_help = "Load lane into hub"
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
                if LANE.name not in self.lanes:
                    self.lanes[LANE.name]={}
                if 'material' not in self.lanes[LANE.name]:
                    self.lanes[LANE.name]['material']=''
                if 'spool_id' not in self.lanes[LANE.name]:
                    self.lanes[LANE.name]['spool_id']=''
                if 'color' not in self.lanes[LANE.name]:
                    self.lanes[LANE.name]['color']=''
                if 'tool_loaded' not in self.lanes[LANE.name]:
                    self.lanes[LANE.name]['tool_loaded']=False
                if self.lanes[LANE.name]['tool_loaded'] == True:
                    self.current = LANE.name
        tmp=[]

        for lanecheck in self.lanes.keys():
            if lanecheck not in temp:
                tmp.append(lanecheck)
        for erase in tmp:
            del self.lanes[erase]
            
        self.save_vars()
        
        if self.Type == 'Box_Turtle':
            logo ='R  _____     ____\n'
            logo+='E /      \  |  o | \n'
            logo+='A |       |/ ___/ \n'
            logo+='D |_________/     \n'
            logo+='Y |_|_| |_|_|\n'

            self.gcode.respond_info(self.Type + ' Prepping lanes')
            for lane in self.lanes.keys():
                CUR_LANE = self.printer.lookup_object('AFC_stepper '+lane)
                CUR_LANE.extruder_stepper.sync_to_extruder(None)
                self.afc_move(lane, -5, self.short_moves_speed, self.short_moves_accel)
                self.afc_move(lane, 5, self.short_moves_speed, self.short_moves_accel)
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

            if self.current == '':
                for lane in self.lanes.keys():
                    CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=1')
                    if self.hub.filament_present == True and CUR_LANE.load_state == True:
                        # TODO put a timeout here and print error to console as this could sit here forever
                        while CUR_LANE.load_state == True:
                            self.rewind(CUR_LANE, -1)
                            self.afc_move(lane, self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
                        self.rewind(CUR_LANE, 0)

                        # TODO put a timeout here and print error to console as this could sit here forever
                        while CUR_LANE.load_state == False:
                            self.afc_move(lane, self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                    else:
                        if CUR_LANE.prep_state== True:
                            # TODO put a timeout here and print error to console as this could sit here forever
                            while CUR_LANE.load_state == False:
                                self.afc_move(lane, self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                            self.afc_led(self.led_ready, CUR_LANE.led_index)
                        else:
                            self.afc_led(self.led_fault, CUR_LANE.led_index)
                            
                    # Setting lane to prepped so that loading will happen once user tries to load filament
                    CUR_LANE.set_afc_prep_done()
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=0')
                    self.gcode.respond_info(lane.upper() + ' READY')
                
            else:
                for lane in self.lanes:
                    CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=1')
                    if self.current == lane:
                        if self.tool.filament_present == False:
                            while CUR_LANE.load_state == True:
                                self.rewind(CUR_LANE, -1)
                                self.afc_move(lane, self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
                            self.rewind(CUR_LANE, 0)
                            CUR_LANE.status = ''
                            self.current = ''
                            while CUR_LANE.load_state == False:
                                self.afc_move(lane, self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                            
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
                                self.afc_move(lane, self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                                num_tries += 1
                            if 20 == num_tries: self.gcode._respond_error("Could not load {} to load filament sensor, remove and reinsert to load correctly".format(CUR_LANE.name))
                            
                        if CUR_LANE.prep_state == True and CUR_LANE.load_state == True:
                            self.afc_led(self.led_ready, CUR_LANE.led_index)
                    
                    # Setting lane to prepped so that loading will happen once user tries to load filament
                    CUR_LANE.set_afc_prep_done()
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=0')
                    self.gcode.respond_info('LANE ' + lane[-1] + ' READY')
        self.gcode.respond_info(logo)

    # HUB COMMANDS
    cmd_HUB_LOAD_help = "Load lane into hub"
    def cmd_HUB_LOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        if LANE.load_state == False:
            self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=1')
            while LANE.load_state == False:
                self.afc_move(lane, self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
            self.afc_move(lane, self.hub_move_dis * -1 , self.short_moves_speed, self.short_moves_accel)
            self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=0')

    cmd_LANE_UNLOAD_help = "Unload lane from extruder"
    def cmd_LANE_UNLOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        LANE = self.printer.lookup_object('AFC_stepper '+ lane)
        if lane != self.current:
            self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=1')
            while LANE.load_state == True:
                self.afc_move(lane, self.hub_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
            self.afc_move(lane, self.hub_move_dis * -5, self.short_moves_speed, self.short_moves_accel)
            self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=0')
        else:
            self.gcode.respond_info('LANE ' + lane + ' IS TOOL LOADED')

    cmd_TOOL_LOAD_help = "Load lane into tool"
    def cmd_TOOL_LOAD(self, gcmd):
        self.toolhead = self.printer.lookup_object('toolhead')
        lane = gcmd.get('LANE', None)
        LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        LANE.status = 'loading'
        led_cont=LANE.led_index.split(':')
        self.afc_led(self.led_loading, LANE.led_index)
        if LANE.load_state == True and self.hub.filament_present == False:
            if self.hub_cut_active == 1:
                self.hub_cut(lane)
            self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=1')
            self.afc_move(lane, LANE.dist_hub, self.short_moves_speed, self.short_moves_accel)
            while self.hub.filament_present == False:
                self.afc_move(lane, self.short_move_dis, self.short_moves_speed, self.short_moves_accel)
            self.afc_move(lane, self.afc_bowden_length, self.long_moves_speed, self.long_moves_accel)
            LANE.extruder_stepper.sync_to_extruder(LANE.extruder_name)
            while self.tool.filament_present == False:
                pos = self.toolhead.get_position()
                pos[3] += self.short_move_dis
                self.toolhead.manual_move(pos, self.tool_load_speed)
                self.toolhead.wait_moves()
            pos = self.toolhead.get_position()
            pos[3] += self.tool_stn
            self.toolhead.manual_move(pos, self.tool_load_speed)
            self.toolhead.wait_moves()
            self.printer.lookup_object('AFC_stepper ' + lane).status = 'tool'
            self.lanes[lane]['tool_loaded'] = True

            self.save_vars()

            self.current = lane
            LANE = self.printer.lookup_object('AFC_stepper ' + lane)
            self.afc_led(self.led_tool_loaded, LANE.led_index)
            if self.poop == 1:
                if self.wipe == 1:
                    self.gcode.run_script_from_command(self.wipe_cmd)
                self.gcode.run_script_from_command(self.poop_cmd)
                if self.wipe == 1:
                    self.gcode.run_script_from_command(self.wipe_cmd)
            if self.kick == 1:
                self.gcode.run_script_from_command(self.kick_cmd)
            if self.wipe == 1:
                self.gcode.run_script_from_command(self.wipe_cmd)
        else:
            if self.hub.filament_present == True:
                self.gcode.respond_info("HUB NOT CLEAR")
                self.gcode.run_script_from_command('PAUSE')
            if LANE.load_state == False:
                self.gcode.respond_info(lane + ' NOT READY')
                self.gcode.run_script_from_command('PAUSE')

    cmd_TOOL_UNLOAD_help = "Unload lane to before hub"
    def cmd_TOOL_UNLOAD(self, gcmd):
        self.toolhead = self.printer.lookup_object('toolhead')
        lane = gcmd.get('LANE', None)
        LANE = self.printer.lookup_object('AFC_stepper '+ lane)
        LANE.status = 'unloading'
        led_cont = LANE.led_index.split(':')
        self.afc_led(self.led_unloading, LANE.led_index)
        LANE.extruder_stepper.sync_to_extruder(LANE.extruder_name)
        
        if self.tool_cut_active == 1:
            self.gcode.run_script_from_command(self.tool_cut_cmd)
            if self.park == 1:
                self.gcode.run_script_from_command(self.park_cmd)

        if self.form_tip == 1:
            if self.park == 1: self.gcode.run_script_from_command(self.park_cmd)
            
            self.gcode.run_script_from_command(self.form_tip_cmd)
        while self.tool.filament_present == True:
            pos = self.toolhead.get_position()
            pos[3] += self.tool_stn_unload * -1
            self.toolhead.manual_move(pos, self.tool_unload_speed)
            self.toolhead.wait_moves()
        if self.tool_sensor_after_extruder >0:
            pos = self.toolhead.get_position()
            pos[3] += self.tool_sensor_after_extruder * -1
            self.toolhead.manual_move(pos, self.tool_unload_speed)
            self.toolhead.wait_moves()
            
        LANE.extruder_stepper.sync_to_extruder(None)
        self.rewind(LANE, -1)
        self.afc_move(lane, self.afc_bowden_length * -1, self.long_moves_speed, self.long_moves_accel)
        x=0
        while self.hub.filament_present == True:
            self.afc_move(lane, self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
            x +=1
            if x> 20:
                self.gcode.respond_info('HUB NOT CLEARING ' + lane)
                self.rewind(LANE, 0)
                return
        self.rewind(LANE, 0)
        self.lanes[lane]['tool_loaded'] = False
        self.save_vars()
        self.printer.lookup_object('AFC_stepper ' + lane).status = 'tool'
        time.sleep(1)
        while LANE.load_state == False and LANE.prep_state == True:
            self.afc_move(lane, self.short_move_dis , self.short_moves_speed, self.short_moves_accel)
        self.afc_led(self.led_ready, LANE.led_index)
        LANE.status = ''
        self.current = ''
        self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane + '" ENABLE=0')
    
    cmd_CHANGE_TOOL_help = "Load lane into hub"
    def cmd_CHANGE_TOOL(self, gcmd):
        self.toolhead = self.printer.lookup_object('toolhead')
        lane = gcmd.get('LANE', None)
        if lane != self.current:
            if self.current != '':
                self.gcode.run_script_from_command('TOOL_UNLOAD LANE=' + self.current)
            self.gcode.run_script_from_command('TOOL_LOAD LANE=' + lane)

    def hub_cut(self, lane):
        LANE=self.printer.lookup_object('AFC_stepper '+lane)
        # Prep the servo for cutting.
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_prep_angle))
        # Load the lane until the hub is triggered.
        while self.hub.filament_present == False:
            self.afc_move(lane, self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
        # Go back, to allow the `hub_cut_dist` to be accurate.
        self.afc_move(lane, -self.hub_move_dis*4, self.short_moves_speed, self.short_moves_accel)
        # Feed the `hub_cut_dist` amount.
        self.afc_move(lane, self.hub_cut_dist, self.short_moves_speed, self.short_moves_accel)
        # Have a snooze
        self.sleepCmd(0.5)
        # Choppy Chop
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_clip_angle))
        # Longer Snooze
        self.sleepCmd(1)
        # Align bowden tube (reset)
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_pass_angle))
        # Retract lane by `hub_cut_clear`.
        self.afc_move(lane, -self.hub_cut_clear, self.short_moves_speed, self.short_moves_accel)

    cmd_HUB_CUT_TEST_help = "Test the cutting sequence of the hub cutter, expects LANE=legN"
    def cmd_HUB_CUT_TEST(self, gcmd):
        lane = gcmd.get('LANE', None)
        self.gcode.respond_info('Testing Hub Cut on Lane: ' + lane)
        self.hub_cut(lane)
        self.gcode.respond_info('Done!')

    def sleepCmd(self, timeSeconds):
        self.gcode.run_script_from_command('G4 P' + str(timeSeconds * 1000))
        
    def get_status(self, eventtime):
        str = {}
        
        # Try to get hub filament sensor, if lookup fails default to None
        try: self.hub = self.printer.lookup_object('filament_switch_sensor hub').runout_helper
        except: self.hub = None
        
        # Try to get tool filament sensor, if lookup fails default to None
        try: self.tool=self.printer.lookup_object('filament_switch_sensor tool').runout_helper
        except: self.tool = None

        for NAME in self.lanes.keys():
            LANE=self.printer.lookup_object('AFC_stepper '+NAME)
            str[NAME]={}
            str[NAME]["load"] = bool(LANE.load_state)
            str[NAME]["prep"]=bool(LANE.prep_state)
            str[NAME]["material"]=self.lanes[NAME]['material']
            str[NAME]["spool_id"]=self.lanes[NAME]['spool_id']
            str[NAME]["color"]=self.lanes[NAME]['color']
        str["system"]={}   
        str["system"]['current_load']= self.current
        # Set status of filament sensors if they exist, false if sensors are not found
        str["system"]['tool_loaded'] = True == self.tool.filament_present if self.tool is not None else False
        str["system"]['hub_loaded']  = True == self.hub.filament_present  if self.hub is not None else False

        str["system"]['num_lanes'] = len(self.lanes)
        return str
    
    cmd_SPOOL_ID_help = "LINK SPOOL into hub"
    def cmd_SPOOL_ID(self, gcmd):
        return
        
def load_config(config):         
    return afc(config)
