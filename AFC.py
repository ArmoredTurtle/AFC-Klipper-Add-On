# 8 Track Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import math, logging
import chelper
import copy
import os 
import time
import toolhead
import stepper
from kinematics import extruder
from . import stepper_enable, output_pin

def calc_move_time(dist, speed, accel):
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
        self.current ='lane0'
        self.LANES=[]

        #LED SETTINGS
        self.ind_lights=None
        self.led_name = config.get('led_name')
        self.led_fault =config.get('led_fault')
        self.led_ready = config.get('led_ready')
        self.led_not_ready = config.get('led_not_ready')
        self.led_loading = config.get('led_loading')
        self.led_tool_loaded = config.get('led_tool_loaded')

        # HUB
        self.hub_dis = config.getfloat("hub_dis", 45)
        self.hub_move_dis = config.getfloat("hub_move_dis", 50)
        self.hub_clear = config.getfloat("hub_clear", 50)
        self.hub=''

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
        self.tool=''
        self.tool_cut_active = config.getfloat("tool_cut_active", 0)
        self.tool_cut_cmd = config.get('tool_cut_cmd')

        # CHOICES
        self.park = config.getfloat("park", 0)
        self.park_cmd = config.get('park_cmd')
        self.kick = config.getfloat("kick", 0)
        self.kick_cmd = config.get('kick_cmd')
        self.wipe = config.getfloat("wipe", 0)
        self.wipe_cmd = config.get('wipe_cmd')
        self.poop = config.getfloat("poop", 0)
        self.poop_cmd = config.get('poop_cmd')
        self.form_tip = config.getfloat("form_tip", 0)

        self.tool_stn = config.getfloat("tool_stn", 120)
        self.afc_bowden_length = config.getfloat("afc_bowden_length", 900)
        

        # MOVE SETTINGS
        self.long_moves_speed = config.getfloat("long_moves_speed", 100)
        self.long_moves_accel = config.getfloat("long_moves_accel", 400)
        self.short_moves_speed = config.getfloat("short_moves_speed", 25)
        self.short_moves_accel = config.getfloat("short_moves_accel", 400)
        self.short_move =' VELOCITY=' + str(self.short_moves_speed) + ' ACCEL='+ str(self.short_moves_accel)
        self.long_move =' VELOCITY=' + str(self.long_moves_speed) + ' ACCEL='+ str(self.long_moves_accel)
        self.short_move_dis = config.getfloat("short_move_dis", 10)


        self.gcode.register_command('HUB_LOAD', self.cmd_HUB_LOAD, desc=self.cmd_HUB_LOAD_help)
        if self.Type == 'Box_Turtle':
            self.gcode.register_command('LANE_UNLOAD', self.cmd_LANE_UNLOAD, desc=self.cmd_LANE_UNLOAD_help)

        self.gcode.register_command('TOOL_LOAD', self.cmd_TOOL_LOAD, desc=self.cmd_TOOL_LOAD_help)
        self.gcode.register_command('TOOL_UNLOAD', self.cmd_TOOL_UNLOAD, desc=self.cmd_TOOL_UNLOAD_help)
        self.gcode.register_command('CHANGE_TOOL', self.cmd_CHANGE_TOOL, desc=self.cmd_CHANGE_TOOL_help)
        self.gcode.register_command('PREP', self.cmd_PREP, desc=self.cmd_PREP_help)

        self.gcode.register_command('TEST', self.cmd_TEST, desc=self.cmd_TEST_help)

        self.VarFile = config.get('VarFile')

    def handle_connect(self):
        self.toolhead = self.printer.lookup_object('toolhead')

    cmd_TEST_help = "Load lane into hub"
    def cmd_TEST(self, gcmd):
        self.gcode.respond_info('TEST ROUTINE')
        LANE=self.printer.lookup_object('AFC_stepper leg4')
        self.rewind(LANE,1)
        time.sleep(4)
        self.gcode.respond_info('half speed')
        self.rewind(LANE,.5)
        time.sleep(4)
        self.gcode.respond_info('third speed')
        self.rewind(LANE,.3)
        time.sleep(4)
        self.gcode.respond_info('10 percent speed')
        self.rewind(LANE,.1)
        time.sleep(4)
        self.gcode.respond_info('Done')
        self.rewind(LANE,0)
        
    def rewind(self, lane, value, is_resend=False):
        if lane.respooler is None:
            return
        value /= lane.respooler.scale
        if not lane.respooler.is_pwm and value not in [0., 1.]:
            if value>0:
                value=1
        # Obtain print_time and apply requested settings
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.register_lookahead_callback(
            lambda print_time: lane.respooler._set_pin(print_time, value))
        
    def afc_led (self, status, idx=None):
        if self.ind_lights is None:
            return
        led = self.ind_lights
        colors=list(map(float,status.split(',')))
        transmit =1
        if idx is not None:
            index=int(idx)
        else:
            index=None

        def lookahead_bgfunc(print_time):
            led.led_helper.set_color(index, colors)
            if transmit:
                led.led_helper.check_transmit(print_time) 
        
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.register_lookahead_callback(lookahead_bgfunc)

    def afc_move(self, lane, distance, speed, accel):
        name = 'AFC_stepper '+lane
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
        self.afc_led(self.led_fault, None)
        time.sleep(3)
        for PO in self.printer.objects:
            if 'AFC_stepper' in PO and 'tmc' not in PO:
                name=PO.split(' ')[1]
                self.LANES.append(name)
            if 'AFC_led' in PO:
                self.ind_lights=self.printer.lookup_object(PO)
        newline=''
        try:
            content=open(self.VarFile).read()

            for lanes in self.LANES:
                if lanes not in content:
                    content += lanes +':tool=0\n'
            
            file=open(self.VarFile, 'w')
            file.write(content)
            file.close
            
            for lanes in content.splitlines():
                lane=lanes.split(':')[0]
                tool=lanes.split(':')[1]
                if '1' in tool:
                    self.current=lane
                    self.printer.lookup_object('AFC_stepper '+lane).status='tool'

        except IOError:
            newline=''
            for line in self.LANES:
                newline += line + ':tool=0\n'
            file=open(self.VarFile, 'w')
            file.write(newline)
            file.close
        
        if self.Type == 'Box_Turtle':
            logo ='R  _____     ____\n'
            logo+='E /      \  |  o | \n'
            logo+='A |       |/ ___/ \n'
            logo+='D |_________/     \n'
            logo+='Y |_|_| |_|_|\n'

            self.gcode.respond_info(self.Type + ' Prepping lanes')
            for NAME in self.LANES:
                LANE=self.printer.lookup_object('AFC_stepper '+NAME)
                LANE.extruder_stepper.sync_to_extruder(None)
                led_cont=LANE.led_index.split(':')
                self.afc_move(NAME,-5,self.short_moves_speed,self.short_moves_accel)
                self.afc_move(NAME,5,self.short_moves_speed,self.short_moves_accel)
                if LANE.prep_state == False:
                    self.afc_led(self.led_not_ready, led_cont[1])
            self.hub=self.printer.lookup_object('filament_switch_sensor hub').runout_helper
            self.tool=self.printer.lookup_object('filament_switch_sensor tool').runout_helper
            if self.current == 'lane0':
                for NAME in self.LANES:
                    LANE=self.printer.lookup_object('AFC_stepper '+NAME)
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+NAME +'" ENABLE=1')
                    led_cont=LANE.led_index.split(':')
                    if self.hub.filament_present == True and LANE.load_state == True:
                        while LANE.load_state == True:
                            self.rewind(LANE,1)
                            self.afc_move(NAME,self.hub_move_dis * -1,self.short_moves_speed,self.short_moves_accel)
                        self.rewind(LANE,0)
                        while LANE.load_state == False:
                            self.afc_move(NAME,self.hub_move_dis,self.short_moves_speed,self.short_moves_accel)
                    else:
                        if LANE.prep_state== True:
                            while LANE.load_state == False:
                                self.afc_move(NAME,self.hub_move_dis,self.short_moves_speed,self.short_moves_accel)
                            
                            self.afc_led(self.led_ready, led_cont[1])
                        else:
                            self.afc_led(self.led_fault, led_cont[1])
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + NAME + '" ENABLE=0')
                    self.gcode.respond_info(NAME.upper() + ' READY')
                
            else:
                for NAME in self.LANES:
                    LANE=self.printer.lookup_object('AFC_stepper '+NAME)
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+NAME +'" ENABLE=1')
                    led_cont=LANE.led_index.split(':')
                    if self.current == NAME:
                        LANE=self.printer.lookup_object('AFC_stepper '+ self.current)
                        led_cont=LANE.led_index.split(':')
                        LANE.extruder_stepper.sync_to_extruder(LANE.extruder_name)
                        self.gcode.respond_info(self.current + " Tool Loaded")
                        self.afc_led(self.led_tool_loaded, led_cont[1])
                    else:
                        if LANE.prep_state == True and LANE.load_state == False:
                            while LaneHub.last_state == False:
                                self.afc_move(NAME,self.hub_move_dis,self.short_moves_speed,self.short_moves_accel)
                        if LANE.prep_state == True and LANE.load_state == True:
                            self.afc_led(self.led_ready, led_cont[1])
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+NAME +'" ENABLE=0')
                    self.gcode.respond_info('LANE '+NAME[-1] + ' READY')

        elif self.Type == 'Raven':
            logo ='R              __ \n'
            logo+='E             /`{> \n'
            logo+='A         ____) (____ \n'
            logo+='D       // --;   ;-- \\\\ \n'
            logo+='Y      ///////\_/\\\\\\\\\\\\\\ \n'
            logo+='!             m m \n'
        self.gcode.respond_info(logo)
    
    def TOOL_VAR_CHANGE(self, lane, tool):
        newline=''
        try:
            with open(self.VarFile, 'r') as file: 
                data = file.readlines()
                for line in data:
                    if lane in line:
                        newline += lane +':tool=' + tool + '\n'
                    else:
                        newline += line
        except IOError:
            self.gcode.respond_info("no file found " + self.VarFile)

        file=open(self.VarFile, 'w')
        file.write(newline)
        file.close

    # HUB COMMANDS
    cmd_HUB_LOAD_help = "Load lane into hub"
    def cmd_HUB_LOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        LANE=self.printer.lookup_object('AFC_stepper '+ lane)
        if LANE.load_state == False:
            self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+ lane +'" ENABLE=1')
            while LANE.load_state == False:
                self.afc_move(lane,self.hub_move_dis,self.short_moves_speed,self.short_moves_accel)
            self.afc_move(lane,self.hub_move_dis * -1 ,self.short_moves_speed,self.short_moves_accel)
            self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+ lane +'" ENABLE=0')

    cmd_LANE_UNLOAD_help = "Load lane into hub"
    def cmd_LANE_UNLOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        LANE=self.printer.lookup_object('AFC_stepper '+ lane)
        self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+ lane +'" ENABLE=1')
        while LANE.load_state == True:
            self.rewind(LANE,1)
            self.afc_move(lane,self.hub_move_dis * -1,self.short_moves_speed,self.short_moves_accel)
        self.afc_move(lane,self.hub_move_dis * -5,self.short_moves_speed,self.short_moves_accel)
        self.rewind(LANE,0)
        self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+lane +'" ENABLE=0')

    cmd_TOOL_LOAD_help = "Load lane into tool"
    def cmd_TOOL_LOAD(self, gcmd):
        self.toolhead = self.printer.lookup_object('toolhead')
        lane = gcmd.get('LANE', None)
        LANE=self.printer.lookup_object('AFC_stepper '+ lane)
        if LANE.load_state == True and self.hub.filament_present == False:
            self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+ lane +'" ENABLE=1')
            while self.hub.filament_present == False:
                self.afc_move(lane, self.short_move_dis, self.short_moves_speed, self.short_moves_accel)
            self.afc_move(lane, self.afc_bowden_length, self.long_moves_speed, self.long_moves_accel)
            LANE.extruder_stepper.sync_to_extruder(LANE.extruder_name)
            while self.tool.filament_present == False:
                pos = self.toolhead.get_position()
                pos[3] += self.short_move_dis
                self.toolhead.manual_move(pos, 5)
                self.toolhead.wait_moves()
            pos = self.toolhead.get_position()
            pos[3] += self.tool_stn
            self.toolhead.manual_move(pos, 5)
            self.toolhead.wait_moves()
            self.printer.lookup_object('AFC_stepper '+ lane).status = 'tool'
            self.TOOL_VAR_CHANGE(lane,'1')
            self.current=lane
            LANE=self.printer.lookup_object('AFC_stepper '+lane)
            led_cont=LANE.led_index.split(':')
            self.afc_led(self.led_tool_loaded, led_cont[1])
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
            if LANE.load_state == False:
                self.gcode.respond_info(lane + ' NOT READY')

    cmd_TOOL_UNLOAD_help = "Load lane into hub"
    def cmd_TOOL_UNLOAD(self, gcmd):
        self.toolhead = self.printer.lookup_object('toolhead')
        lane = gcmd.get('LANE', None)
        LANE=self.printer.lookup_object('AFC_stepper '+lane)
        LANE.status = 'unloading'
        led_cont=LANE.led_index.split(':')
        self.afc_led(self.led_loading, led_cont[1])
        LANE.extruder_stepper.sync_to_extruder(LANE.extruder_name)
        
        if self.tool_cut_active == 1:
            for cut in range(2):
                self.gcode.run_script_from_command('CUT')
            if self.park == 1:
                self.gcode.run_script_from_command(self.park_cmd)
        while self.tool.filament_present == True:
            pos = self.toolhead.get_position()
            pos[3] += self.tool_stn *-1
            self.toolhead.manual_move(pos, 5)
            self.toolhead.wait_moves()
        LANE.extruder_stepper.sync_to_extruder(None)
        self.rewind(LANE,1)
        self.afc_move(lane, self.afc_bowden_length * -1, self.long_moves_speed, self.long_moves_accel)
        x=0
        while self.hub.filament_present == True:
            self.afc_move(lane, self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel)
            x +=1
            if x> 20:
                self.gcode.respond_info('HUB NOT CLEARING')
                self.rewind(LANE,0)
                return
              
        self.rewind(LANE,0)
        self.afc_move(lane, self.hub_dis * -1, self.short_moves_speed, self.short_moves_accel)
        self.TOOL_VAR_CHANGE(lane,'0')
        self.printer.lookup_object('AFC_stepper '+ lane).status = 'tool'
        self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper ' + lane +'" ENABLE=0')
        led = self.led_ready.split(',')
        self.afc_led(self.led_ready, led_cont[1])
        LANE.status = ''
        self.current= 'lane0'
    
    cmd_CHANGE_TOOL_help = "Load lane into hub"
    def cmd_CHANGE_TOOL(self, gcmd):
        self.toolhead = self.printer.lookup_object('toolhead')
        lane = gcmd.get('LANE', None)
        if lane != self.current:
            if self.current != 'lane0':
                self.gcode.run_script_from_command('TOOL_UNLOAD LANE=' + self.current)
            if self.hub_cut_active == 1 and self.current== 'lane0':
                self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + self.hub_cut_servo_prep_angle)
                while self.hub.filament_present == False:
                    self.afc_move(lane, self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
                self.afc_move(lane, self.hub_cut_dist, self.short_moves_speed, self.short_moves_accel)
                time.sleep(2)
                self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE='+self.hub_cut_servo_clip_angle)
                time.sleep(2)
                self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE='+self.hub_cut_servo_pass_angle)
                time.sleep(2)
            self.gcode.run_script_from_command('TOOL_LOAD LANE=' + lane)

def load_config(config):         
    return afc(config)
