# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import os
import json
import urllib.request

from configparser import Error as error

class afc:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode_move = self.printer.load_object(config, 'gcode_move')
        self.VarFile = config.get('VarFile')
        self.current = None
        self.failure = False
        self.lanes = {}
        self.extruders = {}
        self.afc_monitoring = False

        # tool position when tool change was requested
        self.change_tool_pos = None
        self.in_toolchange = False
        self.tool_start = None
        self.base_position = [0.0, 0.0, 0.0, 0.0]
        self.last_gcode_position = [0.0, 0.0, 0.0, 0.0]
        self.last_toolhead_position = [0.0, 0.0, 0.0, 0.0]
        self.homing_position = [0.0, 0.0, 0.0, 0.0]
        self.speed = 25.
        # SPOOLMAN
        self.spoolman_ip = config.get('spoolman_ip', None)
        self.spoolman_port = config.get('spoolman_port', None)
        
        #LED SETTINGS
        self.ind_lights = None
        self.led_name = config.get('led_name')
        self.led_fault =config.get('led_fault','1,0,0,0')
        self.led_ready = config.get('led_ready','1,1,1,1')
        self.led_not_ready = config.get('led_not_ready','1,0,0,0')
        self.led_loading = config.get('led_loading','1,1,0,0')
        self.led_unloading = config.get('led_unloading','1,1,.5,0')
        self.led_tool_loaded = config.get('led_tool_loaded','1,1,0,0')
        self.led_advancing = config.get('led_buffer_advancing','0,0,1,0')
        self.led_trailing = config.get('led_buffer_trailing','0,1,0,0')
        self.led_buffer_disabled = config.get('led_buffer_disable', '0,0,0,0.25')

        # TOOL Cutting Settings
        self.tool = ''
        self.tool_cut = config.getboolean("tool_cut", False)
        self.tool_cut_cmd = config.get('tool_cut_cmd', None)

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

        # MOVE SETTINGS
        self.tool_sensor_after_extruder = config.getfloat("tool_sensor_after_extruder", 0)
        self.long_moves_speed = config.getfloat("long_moves_speed", 100)
        self.long_moves_accel = config.getfloat("long_moves_accel", 400)
        self.short_moves_speed = config.getfloat("short_moves_speed", 25)
        self.short_moves_accel = config.getfloat("short_moves_accel", 400)
        self.short_move_dis = config.getfloat("short_move_dis", 10)
        self.tool_max_unload_attempts = config.getint('tool_max_unload_attempts', 2)
        self.z_hop =config.getfloat("z_hop", 0)
        self.xy_resume =config.getboolean("xy_resume", False)
        self.resume_speed =config.getfloat("resume_speed", 0)
        self.resume_z_speed = config.getfloat("resume_z_speed", 0)
        self.gcode.register_command('HUB_LOAD', self.cmd_HUB_LOAD, desc=self.cmd_HUB_LOAD_help)
        self.gcode.register_command('LANE_UNLOAD', self.cmd_LANE_UNLOAD, desc=self.cmd_LANE_UNLOAD_help)
        self.gcode.register_command('TOOL_LOAD', self.cmd_TOOL_LOAD, desc=self.cmd_TOOL_LOAD_help)
        self.gcode.register_command('TOOL_UNLOAD', self.cmd_TOOL_UNLOAD, desc=self.cmd_TOOL_UNLOAD_help)
        self.gcode.register_command('CHANGE_TOOL', self.cmd_CHANGE_TOOL, desc=self.cmd_CHANGE_TOOL_help)
        self.gcode.register_command('LANE_MOVE', self.cmd_LANE_MOVE, desc=self.cmd_LANE_MOVE_help)
        self.gcode.register_command('TEST', self.cmd_TEST, desc=self.cmd_TEST_help)
        self.gcode.register_command('HUB_CUT_TEST', self.cmd_HUB_CUT_TEST, desc=self.cmd_HUB_CUT_TEST_help)
        self.gcode.register_command('RESET_FAILURE', self.cmd_CLEAR_ERROR, desc=self.cmd_CLEAR_ERROR_help)
        self.gcode.register_command('AFC_RESUME', self.cmd_AFC_RESUME, desc=self.cmd_AFC_RESUME_help)
        self.gcode.register_mux_command('SET_BOWDEN_LENGTH', 'AFC', None, self.cmd_SET_BOWDEN_LENGTH, desc=self.cmd_SET_BOWDEN_LENGTH_help)
        self.gcode.register_mux_command('SET_COLOR',None,None, self.cmd_SET_COLOR, desc=self.cmd_SET_COLOR_help)
        self.gcode.register_mux_command('SET_SPOOL_ID',None,None, self.cmd_SET_SPOOLID, desc=self.cmd_SET_SPOOLID_help)
        self.gcode.register_command('AFC_STATUS', self.cmd_AFC_STATUS, desc=self.cmd_AFC_STATUS_help)
        self.VarFile = config.get('VarFile')
        # Get debug and cast to boolean
        #self.debug = True == config.get('debug', 0)
        self.debug = False

    cmd_AFC_STATUS_help = "Return current status of AFC"
    def cmd_AFC_STATUS(self, gcmd):
        status_msg = ''

        for UNIT in self.lanes.keys():
            # Find the maximum length of lane names to determine the column width
            max_lane_length = max(len(lane) for lane in self.lanes[UNIT].keys())

            status_msg += '<span class=info--text>{} Status</span>\n'.format(UNIT)

            # Create a dynamic format string that adjusts based on lane name length
            header_format = '{:<{}} | Prep | Load | Hub | Tool |\n'
            status_msg += header_format.format("LANE", max_lane_length)

            for LANE in self.lanes[UNIT].keys():
                lane_msg = ''
                CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
                CUR_HUB = self.printer.lookup_object('AFC_hub '+ UNIT)
                CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
                if self.current != None:
                    if self.current == CUR_LANE.name:
                        if not CUR_EXTRUDER.tool_start_state or not CUR_HUB.state:
                            lane_msg += '<span class=warning--text>{:<{}} </span>'.format(CUR_LANE.name.upper(), max_lane_length)
                        else:
                            lane_msg += '<span class=success--text>{:<{}} </span>'.format(CUR_LANE.name.upper(), max_lane_length)
                    else:
                        lane_msg += '{:<{}} '.format(CUR_LANE.name.upper(),max_lane_length)
                else:
                    lane_msg += '{:<{}} '.format(CUR_LANE.name.upper(),max_lane_length)

                if CUR_LANE.prep_state == True:
                    lane_msg += '| <span class=success--text><--></span> |'
                else:
                    lane_msg += '|  <span class=error--text>xx</span>  |'
                if CUR_LANE.load_state == True:
                    lane_msg += ' <span class=success--text><--></span> |'
                else:
                    lane_msg += '  <span class=error--text>xx</span>  |'

                if self.current != None:
                    if self.current == CUR_LANE.name:
                        if CUR_HUB.state == True:
                            lane_msg += ' <span class=success--text><-></span> |'
                        else:
                            lane_msg += '  <span class=error--text>xx</span>  |'
                        if CUR_EXTRUDER.tool_start_state == True:
                            lane_msg += ' <span class=success--text><--></span> |\n'
                        else:
                            lane_msg += '  <span class=error--text>xx</span>  |\n'
                    else:
                        lane_msg += '  <span class=error--text>x</span>  |'
                        lane_msg += '  <span class=error--text>xx</span>  |\n'
                else:
                    lane_msg += '  <span class=error--text>x</span>  |'
                    lane_msg += '  <span class=error--text>xx</span>  |\n'
                status_msg += lane_msg
        self.gcode.respond_raw(status_msg)

    cmd_SET_BOWDEN_LENGTH_help = "Helper to dynamically set length of bowden between hub and toolhead. Pass in HUB if using multiple box turtles"
    def cmd_SET_BOWDEN_LENGTH(self, gcmd):
        hub           = gcmd.get("HUB", None )
        length_param  = gcmd.get('LENGTH', None)

        # If hub is not passed in try and get hub if a lane is currently loaded
        if hub is None and self.current is not None:
            CUR_LANE= self.printer.lookup_object('AFC_stepper ' + self.current)
            hub     = CUR_LANE.unit
        elif hub is None and self.current is None:
            self.gcode.respond_info("A lane is not loaded please specify hub to adjust bowden length")
            return

        CUR_HUB       = self.printer.lookup_object('AFC_hub '+ hub )
        config_bowden = CUR_HUB.afc_bowden_length

        if length_param is None or length_param.strip() == '':
            bowden_length = CUR_HUB.config_bowden_length
        else:
            if length_param[0] in ('+', '-'):
                bowden_value = float(length_param)
                bowden_length = config_bowden + bowden_value
            else:
                bowden_length = float(length_param)

        CUR_HUB.afc_bowden_length = bowden_length
        msg =  '// Hub : {}\n'.format( hub )
        msg += '//   Config Bowden Length:   {}\n'.format(CUR_HUB.config_bowden_length)
        msg += '//   Previous Bowden Length: {}\n'.format(config_bowden)
        msg += '//   New Bowden Length:      {}\n'.format(bowden_length)
        msg += '\n// TO SAVE BOWDEN LENGTH afc_bowden_length MUST BE UPDATED IN AFC_Hardware.cfg for each hub if there are multiple'
        self.gcode.respond_raw(msg)

    cmd_LANE_MOVE_help = "Lane Manual Movements"
    def cmd_LANE_MOVE(self, gcmd):
        lane = gcmd.get('LANE', None)
        distance = gcmd.get_float('DISTANCE', 0)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_LANE.move(distance, self.short_moves_speed, self.short_moves_accel)

    cmd_CLEAR_ERROR_help = "CLEAR STATUS ERROR"
    def cmd_CLEAR_ERROR(self, gcmd):
        self.set_error_state(False)

    def save_pos(self):
        # Only save previous location on the first toolchange call to keep an error state from overwriting the location
        if self.in_toolchange == False:
            if self.failure == False:
                self.last_toolhead_position = self.toolhead.get_position()
                self.base_position = self.gcode_move.base_position
                self.last_gcode_position = self.gcode_move.last_position
                self.homing_position = self.gcode_move.homing_position
                self.speed = self.gcode_move.speed

    def restore_pos(self):
        newpos = self.toolhead.get_position()
        newpos[2] = self.last_gcode_position[2] + self.z_hop

        speed = self.resume_speed * 60 if self.resume_speed > 0 else self.speed
        speedz = self.resume_z_speed * 60 if self.resume_z_speed > 0 else self.speed
        # Update GCODE STATE variables
        self.gcode_move.base_position = self.base_position
        self.gcode_move.last_position[:3] = self.last_gcode_position[:3]
        self.gcode_move.homing_position = self.homing_position

        # Restore the relative E position
        e_diff = newpos[3] - self.last_gcode_position[3]
        self.gcode_move.base_position[3] += e_diff

        # Move toolhead to previous z location with zhop added
        self.gcode_move.move_with_transform(newpos, speedz)

        # Move to previous x,y location
        newpos[:2] = self.last_gcode_position[:2]
        self.gcode_move.move_with_transform(newpos, speed)

        # Drop to previous z
        newpos[2] = self.last_gcode_position[2]
        self.gcode_move.move_with_transform(newpos, speedz)

    def pause_print(self):
        if self.is_homed() and not self.is_paused():
            self.save_pos()
            self.gcode.respond_info ('PAUSING')
            self.gcode.run_script_from_command('PAUSE')

    def set_error_state(self, state):
        # Only save position on first error state call
        if state == True and self.failure == False:
            self.save_pos()
        self.failure = state

    def AFC_error(self, msg, pause=True):
        # Handle AFC errors
        self.gcode._respond_error( msg )
        if pause: self.pause_print()

    handle_lane_failure_help = "Get load errors, stop stepper and respond error"
    def handle_lane_failure(self, CUR_LANE, message, pause=True):
        # Disable the stepper for this lane
        CUR_LANE.do_enable(False)
        msg = (CUR_LANE.name.upper() + ' NOT READY' + message)
        self.AFC_error(msg, pause)
        self.afc_led(self.led_fault, CUR_LANE.led_index)

    # Helper function to write variables to file. Prints with indents to make it more readable for users
    def save_vars(self):
        """
        save_vars function saves lane variables to var file and prints with indents to
                  make it more readable for users
        """
        with open(self.VarFile+ '.unit', 'w') as f:
            f.write(json.dumps(self.lanes, indent=4))
        with open(self.VarFile+ '.tool', 'w') as f:
            f.write(json.dumps(self.extruders, indent=4))

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up the toolhead object
        and assigns it to the instance variable `self.toolhead`.
        """
        self.toolhead = self.printer.lookup_object('toolhead')

    cmd_AFC_RESUME_help = "Clear error state and restores position before resuming the print"
    def cmd_AFC_RESUME(self, gcmd):
        self.set_error_state(False)
        self.in_toolchange = False
        self.gcode.run_script_from_command('RESUME')
        self.restore_pos()

    cmd_HUB_CUT_TEST_help = "Test the cutting sequence of the hub cutter, expects LANE=legN"
    def cmd_HUB_CUT_TEST(self, gcmd):
        lane = gcmd.get('LANE', None)
        self.gcode.respond_info('Testing Hub Cut on Lane: ' + lane)
        CUR_LANE = self.printer.lookup_object('AFC_stepper '+ lane)
        CUR_HUB = self.printer.lookup_object('AFC_hub '+ CUR_LANE.unit)
        CUR_HUB.hub_cut(CUR_LANE)
        self.gcode.respond_info('Hub cut Done!')

    cmd_TEST_help = "Test Assist Motors"
    def cmd_TEST(self, gcmd):
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.AFC_error('Must select LANE', False)
            return
        self.gcode.respond_info('TEST ROUTINE')
        try:
            CUR_LANE = self.printer.lookup_object('AFC_stepper '+lane)
        except error as e:
            self.AFC_error(str(e), False)
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

    # HUB COMMANDS
    cmd_HUB_LOAD_help = "Load lane into hub"
    def cmd_HUB_LOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_HUB = self.printer.lookup_object('AFC_hub '+ CUR_LANE.unit)
        if CUR_LANE.prep_state == False: return

        if CUR_LANE.load_state == False:
            CUR_LANE.do_enable(True)
            while CUR_LANE.load_state == False:
                CUR_LANE.move( CUR_HUB.move_dis, self.short_moves_speed, self.short_moves_accel)
        if CUR_LANE.hub_load == False:
            CUR_LANE.move(CUR_LANE.dist_hub, CUR_LANE.dist_hub_move_speed, CUR_LANE.dist_hub_move_accel, True if CUR_LANE.dist_hub > 200 else False)
        while CUR_HUB.state == False:
            CUR_LANE.move(CUR_HUB.move_dis, self.short_moves_speed, self.short_moves_accel)
        while CUR_HUB.state == True:
            CUR_LANE.move(CUR_HUB.move_dis * -1, self.short_moves_speed, self.short_moves_accel)
        CUR_LANE.status = 'Hubed'
        CUR_LANE.do_enable(False)
        CUR_LANE.hub_load = True
        self.lanes[CUR_LANE.unit][CUR_LANE.name]['hub_loaded'] = CUR_LANE.hub_load
        self.save_vars()

    cmd_LANE_UNLOAD_help = "Unload lane from extruder"
    def cmd_LANE_UNLOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        CUR_LANE = self.printer.lookup_object('AFC_stepper '+ lane)
        CUR_HUB = self.printer.lookup_object('AFC_hub '+ CUR_LANE.unit)
        if CUR_LANE.name != self.current:
            CUR_LANE.do_enable(True)
            if CUR_LANE.hub_load:
                CUR_LANE.move(CUR_LANE.dist_hub * -1, CUR_LANE.dist_hub_move_speed, CUR_LANE.dist_hub_move_accel, True if CUR_LANE.dist_hub > 200 else False)
            CUR_LANE.hub_load = False
            while CUR_LANE.load_state == True:
               CUR_LANE.move( CUR_HUB.move_dis * -1, self.short_moves_speed, self.short_moves_accel)
            CUR_LANE.move( CUR_HUB.move_dis * -5, self.short_moves_speed, self.short_moves_accel)
            CUR_LANE.do_enable(False)
            self.lanes[CUR_LANE.unit][CUR_LANE.name]['hub_loaded'] = CUR_LANE.hub_load
            self.save_vars()
            CUR_LANE.status = None
        else:
            self.gcode.respond_info('LANE ' + CUR_LANE.name + ' IS TOOL LOADED')

    cmd_TOOL_LOAD_help = "Load lane into tool"
    def cmd_TOOL_LOAD(self, gcmd):
        lane = gcmd.get('LANE', None)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        self.TOOL_LOAD(CUR_LANE)

    def TOOL_LOAD(self, CUR_LANE):
        if CUR_LANE == None:
            return
        # Try to get bypass filament sensor, if lookup fails default to None
        try:
            bypass = self.printer.lookup_object('filament_switch_sensor bypass').runout_helper
            if bypass.filament_present == True:
                return
        except: bypass = None

        CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        CUR_HUB = self.printer.lookup_object('AFC_hub '+ CUR_LANE.unit)
        self.set_error_state(False)
        extruder = self.toolhead.get_extruder() #Get extruder
        self.heater = extruder.get_heater() #Get extruder heater
        CUR_LANE.status = 'loading'
        self.afc_led(self.led_loading, CUR_LANE.led_index)
        if CUR_LANE.load_state == True and CUR_HUB.state == False:
            if not self.heater.can_extrude: #Heat extruder if not at min temp
                extruder = self.printer.lookup_object('toolhead').get_extruder()
                pheaters = self.printer.lookup_object('heaters')
                wait = True
                if self.heater.target_temp <= self.heater.min_extrude_temp:
                    self.gcode.respond_info('Extruder below min_extrude_temp, heating to 5 degrees above min')
                    pheaters.set_temperature(extruder.get_heater(), self.heater.min_extrude_temp + 5, wait)
            CUR_LANE.do_enable(True)
            if CUR_LANE.hub_load == False:
                CUR_LANE.move(CUR_LANE.dist_hub, CUR_LANE.dist_hub_move_speed, CUR_LANE.dist_hub_move_accel,  True if CUR_LANE.dist_hub > 200 else False)
            CUR_LANE.hub_load = True
            hub_attempts = 0
            while CUR_HUB.state == False:
                if hub_attempts == 0:
                    CUR_LANE.move( CUR_HUB.move_dis, self.short_moves_speed, self.short_moves_accel)
                else:
                    CUR_LANE.move( self.short_move_dis, self.short_moves_speed, self.short_moves_accel)
                hub_attempts += 1
                #callout if filament doesn't go past hub during load
                if hub_attempts > 20:
                    self.pause_print()
                    message = (' PAST HUB, CHECK FILAMENT PATH\n||=====||==>--||-----||\nTRG   LOAD   HUB   TOOL')
                    self.handle_lane_failure(CUR_LANE, message)
                    return
            CUR_LANE.move( CUR_HUB.afc_bowden_length, self.long_moves_speed, self.long_moves_accel, True)
            tool_attempts = 0
            if CUR_EXTRUDER.tool_start != None:
                while CUR_EXTRUDER.tool_start_state == False:
                    tool_attempts += 1
                    CUR_LANE.move( self.short_move_dis, CUR_EXTRUDER.tool_load_speed, self.long_moves_accel)
                    #callout if filament doesn't reach toolhead
                    if tool_attempts > 20:
                        message = (' FAILED TO LOAD ' + CUR_LANE.name.upper() + ' TO TOOL, CHECK FILAMENT PATH\n||=====||====||==>--||\nTRG   LOAD   HUB   TOOL')
                        self.AFC_error(message)
                        self.set_error_state(True)
                        break

            if self.failure == False:
                CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
                CUR_LANE.status = 'Tooled'
                pos = self.toolhead.get_position()
                pos[3] += CUR_EXTRUDER.tool_stn
                self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_load_speed)
                self.toolhead.wait_moves()
                self.printer.lookup_object('AFC_stepper ' + CUR_LANE.name).status = 'tool'
                self.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = True

                self.current = CUR_LANE.name
                if CUR_EXTRUDER.buffer_name != None:
                    CUR_EXTRUDER.buffer.enable_buffer()

                self.afc_led(self.led_tool_loaded, CUR_LANE.led_index)
                if self.poop:
                    self.gcode.run_script_from_command(self.poop_cmd)
                    if self.wipe:
                        self.gcode.run_script_from_command(self.wipe_cmd)
                if self.kick:
                    self.gcode.run_script_from_command(self.kick_cmd)
                if self.wipe:
                    self.gcode.run_script_from_command(self.wipe_cmd)
            # Setting hub loaded outside of failure check since this could be true
            self.lanes[CUR_LANE.unit][CUR_LANE.name]['hub_loaded'] = True
            self.extruders[CUR_LANE.extruder_name]['lane_loaded'] = 'CUR_LANE.name'
            self.set_active_spool(self.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'])
            self.afc_led(self.led_tool_loaded, CUR_LANE.led_index)
            self.save_vars() # Always save variables even if a failure happens
            if self.failure == True:
                self.pause_print()
                self.afc_led(self.led_fault, CUR_LANE.led_index)
        else:
            #callout if hub is triggered when trying to load
            if CUR_HUB.state == True:
                msg = ('HUB NOT CLEAR TRYING TO LOAD ' + CUR_LANE.name.upper() + '\n||-----||----|x|-----||\nTRG   LOAD   HUB   TOOL')
                self.AFC_error(msg)
                self.afc_led(self.led_ready, CUR_LANE.led_index)
            #callout if lane is not ready when trying to load
            if CUR_LANE.load_state == False:
                msg = (CUR_LANE.name.upper() + ' NOT READY' + '\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                self.AFC_error(msg)
                self.afc_led(self.led_not_ready, CUR_LANE.led_index)

    cmd_TOOL_UNLOAD_help = "Unload from tool head"
    def cmd_TOOL_UNLOAD(self, gcmd):
        lane = gcmd.get('LANE', self.current)
        if lane == None:
            return
        CUR_LANE = self.printer.lookup_object('AFC_stepper '+ lane)
        self.TOOL_UNLOAD(CUR_LANE)

    def TOOL_UNLOAD(self, CUR_LANE):
        if CUR_LANE == None:
            return
        CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        CUR_HUB = self.printer.lookup_object('AFC_hub '+ CUR_LANE.unit)
        pos = self.toolhead.get_position()
        pos[3] -= 2
        self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
        self.toolhead.wait_moves()
        pos[2] += self.z_hop
        self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
        self.toolhead.wait_moves()
        extruder = self.toolhead.get_extruder() #Get extruder
        self.heater = extruder.get_heater() #Get extruder heater
        CUR_LANE.status = 'unloading'

        if CUR_EXTRUDER.buffer_name != None:
            CUR_EXTRUDER.buffer.disable_buffer()

        self.afc_led(self.led_unloading, CUR_LANE.led_index)
        CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
        extruder = self.printer.lookup_object('toolhead').get_extruder()
        pheaters = self.printer.lookup_object('heaters')
        wait = True
        if self.heater.target_temp <= self.heater.min_extrude_temp:
            self.gcode.respond_info('Extruder below min_extrude_temp, heating to 5 degrees above min')
            pheaters.set_temperature(extruder.get_heater(), self.heater.min_extrude_temp + 5, wait)
        CUR_LANE.do_enable(True)
        if self.tool_cut:
            self.gcode.run_script_from_command(self.tool_cut_cmd)
            if self.park:
                self.gcode.run_script_from_command(self.park_cmd)
        if self.form_tip:
            if self.park: self.gcode.run_script_from_command(self.park_cmd)
            if self.form_tip_cmd == "AFC":
                self.AFC_tip = self.printer.lookup_object('AFC_form_tip')
                self.AFC_tip.tip_form()
            else:
                self.gcode.run_script_from_command(self.form_tip_cmd)
        num_tries = 0
        while CUR_EXTRUDER.tool_start_state:
            num_tries += 1
            if num_tries > self.tool_max_unload_attempts:
                self.set_error_state(True)
                msg = ('FAILED TO UNLOAD ' + CUR_LANE.name.upper() + '. FILAMENT STUCK IN TOOLHEAD.\n||=====||====||====|x|\nTRG   LOAD   HUB   TOOL')
                self.AFC_error(msg)
                return
            pos = self.toolhead.get_position()
            pos[3] += CUR_EXTRUDER.tool_stn_unload * -1
            self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
            self.toolhead.wait_moves()
        if CUR_EXTRUDER.tool_sensor_after_extruder >0:
            pos = self.toolhead.get_position()
            pos[3] += CUR_EXTRUDER.tool_sensor_after_extruder * -1
            self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
            self.toolhead.wait_moves()
        CUR_LANE.extruder_stepper.sync_to_extruder(None)
        CUR_LANE.move( CUR_HUB.afc_bowden_length * -1, self.long_moves_speed, self.long_moves_accel, True)
        num_tries = 0
        while CUR_HUB.state == True:
            CUR_LANE.move(self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel, True)
            num_tries += 1
            # callout if while unloading, filament doesn't move past HUB
            if num_tries > (CUR_HUB.afc_bowden_length/self.short_move_dis):
                self.set_error_state(True)
                msg = (' HUB NOT CLEARING' + '\n||=====||====|x|-----||\nTRG   LOAD   HUB   TOOL')
                self.AFC_error(msg)
                return
        CUR_LANE.move( CUR_HUB.move_dis * -1, self.short_moves_speed, self.short_moves_accel)
        if CUR_HUB.cut:
            if CUR_HUB.cut_cmd == 'AFC':
                CUR_HUB.hub_cut(CUR_LANE)
            else:
                self.gcode.run_script_from_command(CUR_HUB.cut_cmd)
        while CUR_HUB.state == True:
            CUR_LANE.move(self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel, True)
            num_tries += 1
            # callout if while unloading, filament doesn't move past HUB
            if num_tries > (CUR_HUB.afc_bowden_length/self.short_move_dis):
                self.set_error_state(True)
                msg = (' HUB NOT CLEARING' + '\n||=====||====|x|-----||\nTRG   LOAD   HUB   TOOL')
                self.AFC_error(msg)
                return
        CUR_LANE.hub_load = True
        self.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = False
        self.lanes[CUR_LANE.unit][CUR_LANE.name]['hub_loaded'] = CUR_LANE.hub_load
        self.extruders[CUR_LANE.extruder_name]['lane_loaded'] = ''
        self.save_vars()
        self.afc_led(self.led_ready, CUR_LANE.led_index)
        CUR_LANE.status = None
        self.current = None
        CUR_LANE.do_enable(False)

    cmd_CHANGE_TOOL_help = "change filaments in tool head"
    def cmd_CHANGE_TOOL(self, gcmd):
        lane = gcmd.get('LANE', None)
        # Try to get bypass filament sensor, if lookup fails default to None
        try:
            bypass = self.printer.lookup_object('filament_switch_sensor bypass').runout_helper
            if bypass.filament_present == True:
                return
        except: bypass = None

        if lane != self.current:
            # Create save state
            self.save_pos()
            # Set in_toolchange flag so if there is a failure it doesnt overwrite the saved position
            self.in_toolchange = True
            CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
            if CUR_LANE._afc_prep_done == True:
                self.gcode.respond_info(" Tool Change - " + str(self.current) + " -> " + lane)
                if self.current != None:
                    CUR_LANE = self.printer.lookup_object('AFC_stepper ' + self.current)
                    self.TOOL_UNLOAD(CUR_LANE)
                    if self.failure:
                        msg = (' UNLOAD ERROR NOT CLEARED')
                        self.AFC_error(msg)
                        return
                CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
                #CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
                self.TOOL_LOAD(CUR_LANE)
                # Restore state
            if self.failure == False:
                self.restore_pos()
                self.in_toolchange = False

    cmd_SET_COLOR_help = "change filaments color"
    def cmd_SET_COLOR(self, gcmd):
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.gcode.respond_info("No LANE Defined")
            return
        color = gcmd.get('COLOR', '#000000')
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_LANE.color = '#' + color
        self.lanes[CUR_LANE.unit][CUR_LANE.name]['color'] ='#'+ color
        self.save_vars()
    
    def set_active_spool(self, ID):
        webhooks = self.printer.lookup_object('webhooks')
        args = {'spool_id' : int(ID)}
        try:
            webhooks.call_remote_method("spoolman_set_active_spool", **args)
        except self.printer.command_error:
            if self.spoolman_ip !=None:
                self.gcode._respond_error("Error trying to set active spool")

    cmd_SET_SPOOLID_help = "change filaments ID"
    def cmd_SET_SPOOLID(self, gcmd):
        if self.spoolman_ip !=None:
            lane = gcmd.get('LANE', None)
            if lane == None:
                self.gcode.respond_info("No LANE Defined")
                return
            SpoolID = gcmd.get('SPOOL_ID', '')
            CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
            if SpoolID !='':
                url = 'http://' + self.spoolman_ip + ':'+ self.spoolman_port +"/api/v1/spool/" + SpoolID
                result = json.load(urllib.request.urlopen(url))
                self.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'] = SpoolID
                self.lanes[CUR_LANE.unit][CUR_LANE.name]['material'] = result['filament']['material']
                self.lanes[CUR_LANE.unit][CUR_LANE.name]['color'] = '#' + result['filament']['color_hex']
                if hasattr(result, 'weight'):
                    self.lanes[CUR_LANE.unit][CUR_LANE.name]['weight'] =  result['filament']['remaining_weight']
                else:
                    self.lanes[CUR_LANE.unit][CUR_LANE.name]['weight'] = ''
            else:
                self.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'] = ''
                self.lanes[CUR_LANE.unit][CUR_LANE.name]['material'] = ''
                self.lanes[CUR_LANE.unit][CUR_LANE.name]['color'] = ''
                self.lanes[CUR_LANE.unit][CUR_LANE.name]['weight'] = ''
            self.save_vars()

    def get_status(self, eventtime):
        str = {}

        numoflanes = 0
        for UNIT in self.lanes.keys():
            try:
                screen_mac = self.printer.lookup_object('AFC_screen ' + UNIT).mac
            except error:
                screen_mac = 'None'
            str[UNIT]={}
            for NAME in self.lanes[UNIT].keys():
                LANE=self.printer.lookup_object('AFC_stepper '+ NAME)
                str[UNIT][NAME]={}
                str[UNIT][NAME]['LANE'] = LANE.index
                str[UNIT][NAME]['Command'] = LANE.gcode_cmd
                str[UNIT][NAME]['load'] = bool(LANE.load_state)
                str[UNIT][NAME]["prep"] =bool(LANE.prep_state)
                str[UNIT][NAME]["loaded_to_hub"] = self.lanes[UNIT][NAME]['hub_loaded']
                str[UNIT][NAME]["material"]=self.lanes[UNIT][NAME]['material']
                str[UNIT][NAME]["spool_id"]=self.lanes[UNIT][NAME]['spool_id']
                str[UNIT][NAME]["color"]=self.lanes[UNIT][NAME]['color']
                str[UNIT][NAME]["weight"]=self.lanes[UNIT][NAME]['weight']
                numoflanes +=1
            str[UNIT]['system']={}
            str[UNIT]['system']['hub_loaded']  = True == self.printer.lookup_object('AFC_hub '+ UNIT).state
            str[UNIT]['system']['can_cut']  = True == self.printer.lookup_object('AFC_hub '+ UNIT).cut
            str[UNIT]['system']['screen'] = screen_mac

        str["system"]={}
        str["system"]['current_load']= self.current
        str["system"]['num_units'] = len(self.lanes)
        str["system"]['num_lanes'] = numoflanes
        str["system"]['num_extruders'] = len(self.extruders)
        str["system"]["extruders"]={}

        for EXTRUDE in self.extruders.keys():

            str["system"]["extruders"][EXTRUDE]={}
            CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + EXTRUDE)
            str["system"]["extruders"][EXTRUDE]['lane_loaded'] = self.extruders[LANE.extruder_name]['lane_loaded']
            str["system"]["extruders"][EXTRUDE]['tool_start_sensor'] = True == CUR_EXTRUDER.tool_start_state if CUR_EXTRUDER.tool_start is not None else False
            str["system"]["extruders"][EXTRUDE]['tool_end_sensor']   = True == CUR_EXTRUDER.tool_end_state   if CUR_EXTRUDER.tool_end   is not None else False
            if CUR_EXTRUDER.buffer_name != None:
                str["system"]["extruders"][EXTRUDE]['buffer']   = CUR_EXTRUDER.buffer_name
                str["system"]["extruders"][EXTRUDE]['buffer_status']   = CUR_EXTRUDER.buffer.buffer_status()
            else:
                str["system"]["extruders"][EXTRUDE]['buffer']   = 'None'

        return str

    def is_homed(self):
        curtime = self.reactor.monotonic()
        kin_status = self.toolhead.get_kinematics().get_status(curtime)
        if ('x' not in kin_status['homed_axes'] or 'y' not in kin_status['homed_axes'] or 'z' not in kin_status['homed_axes']):
            return False
        else:
            return True

    def is_printing(self):
        eventtime = self.reactor.monotonic()
        idle_timeout = self.printer.lookup_object("idle_timeout")
        if idle_timeout.get_status(eventtime)["state"] == "Printing":
            return True
        else:
            False

    def is_paused(self):
        eventtime = self.reactor.monotonic()
        pause_resume = self.printer.lookup_object("pause_resume")
        return bool(pause_resume.get_status(eventtime)["is_paused"])

    def afc_led (self, status, idx=None):
        if idx == None:
            return
        # Try to find led object, if not found print error to console for user to see
        try: led = self.printer.lookup_object('AFC_led '+ idx.split(':')[0])
        except:
            error_string = "Error: Cannot find [{}] in config, make sure led_index in config is correct for AFC_stepper {}".format(afc_object, idx.split(':')[-1])
            self.AFC_error( error_string)
        led.led_change(int(idx.split(':')[1]), status)

def load_config(config):
    return afc(config)
