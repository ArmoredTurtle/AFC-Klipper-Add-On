# Armored Turtle Automated Filament Control
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import json
try:
    from urllib.request import urlopen
except:
    # Python 2.7 support
    from urllib2 import urlopen

AFC_VERSION="1.0.0"

# Class for holding different states so its clear what all valid states are
class State:
    INIT            = "Initialized"
    IDLE            = "Idle"
    ERROR           = "Error"
    LOADING         = "Loading"
    UNLOADING       = "Unloading"
    EJECTING_LANE   = "Ejecting"
    MOVING_LANE     = "Moving"
    RESTORING_POS   = "Restoring"

def load_config(config):
    return afc(config)

class afc:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.webhooks = self.printer.lookup_object('webhooks')
        self.printer.register_event_handler("klippy:connect",self.handle_connect)

        # Registering stepper callback so that mux macro can be set properly with valid lane names
        self.printer.register_event_handler("afc_stepper:register_macros",self.register_lane_macros)
        # Registering webhooks endpoint for <ip_address>/printer/afc/status
        self.webhooks.register_endpoint("afc/status", self._webhooks_status)

        self.SPOOL = self.printer.load_object(config,'AFC_spool')
        self.ERROR = self.printer.load_object(config,'AFC_error')
        self.FUNCTION = self.printer.load_object(config,'AFC_functions')
        self.IDLE = self.printer.load_object(config,'idle_timeout')
        self.gcode = self.printer.lookup_object('gcode')

        self.gcode_move = self.printer.load_object(config, 'gcode_move')

        
        self.current        = None
        self.current_loading= None
        self.next_lane_load = None
        self.error_state    = False
        self.current_state  = State.INIT
        self.spoolman = None

        # Objects for everything configured for AFC
        self.units      = {}
        self.tools      = {}
        self.lanes      = {}
        self.hubs       = {}
        self.buffers    = {}
        self.tool_cmds  = {}
        self.monitoring = False
        self.number_of_toolchanges  = 0
        self.current_toolchange     = 0

        # tool position when tool change was requested
        self.change_tool_pos = None
        self.in_toolchange = False
        self.tool_start = None

        # Save/resume pos variables
        self.base_position = [0.0, 0.0, 0.0, 0.0]
        self.last_gcode_position = [0.0, 0.0, 0.0, 0.0]
        self.last_toolhead_position = [0.0, 0.0, 0.0, 0.0]
        self.homing_position = [0.0, 0.0, 0.0, 0.0]
        self.speed = 25.
        self.absolute_coord = True

        # Config get section
        self.unit_order_list = config.get('unit_order_list','')
        self.VarFile = config.get('VarFile','../printer_data/config/AFC/') 			# Path to the variables file for AFC configuration.
        self.cfgloc = self._remove_after_last(self.VarFile,"/")
        self.default_material_temps = config.getlists("default_material_temps", None) # Default temperature to set extruder when loading/unloading lanes. Material needs to be either manually set or uses material from spoolman if extruder temp is not set in spoolman.

        

        #LED SETTINGS
        self.ind_lights = None
        # led_name is not used, either use or needs to be removed
        self.led_name = config.get('led_name',None)
        self.led_fault =config.get('led_fault','1,0,0,0')                           # LED color to set when faults occur in lane        (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_ready = config.get('led_ready','1,1,1,1')                          # LED color to set when lane is ready               (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_not_ready = config.get('led_not_ready','1,1,0,0')                  # LED color to set when lane not ready              (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_loading = config.get('led_loading','1,0,0,0')                      # LED color to set when lane is loading             (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_prep_loaded = config.get('led_loading','1,1,0,0')                  # LED color to set when lane is loaded              (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_unloading = config.get('led_unloading','1,1,.5,0')                 # LED color to set when lane is unloading           (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_tool_loaded = config.get('led_tool_loaded','1,1,0,0')              # LED color to set when lane is loaded into tool    (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_advancing = config.get('led_buffer_advancing','0,0,1,0')           # LED color to set when buffer is advancing         (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_trailing = config.get('led_buffer_trailing','0,1,0,0')             # LED color to set when buffer is trailing          (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_buffer_disabled = config.get('led_buffer_disable', '0,0,0,0.25')   # LED color to set when buffer is disabled          (R,G,B,W) 0 = off, 1 = full brightness.

        # TOOL Cutting Settings
        self.tool = ''
        self.tool_cut = config.getboolean("tool_cut", False)                        # Set to True to enable toolhead cutting
        self.tool_cut_cmd = config.get('tool_cut_cmd', None)                        # Macro to use when doing toolhead cutting. Change macro name if you would like to use your own cutting macro

        # CHOICES
        self.park = config.getboolean("park", False)                                # Set to True to enable parking during unload
        self.park_cmd = config.get('park_cmd', None)                                # Macro to use when parking. Change macro name if you would like to use your own park macro
        self.kick = config.getboolean("kick", False)                                # Set to True to enable poop kicking after lane loads
        self.kick_cmd = config.get('kick_cmd', None)                                # Macro to use when kicking. Change macro name if you would like to use your own kick macro
        self.wipe = config.getboolean("wipe", False)                                # Set to True to enable nozzle wiping after lane loads
        self.wipe_cmd = config.get('wipe_cmd', None)                                # Macro to use when nozzle wiping. Change macro name if you would like to use your own wipe macro
        self.poop = config.getboolean("poop", False)                                # Set to True to enable pooping(purging color) after lane loads
        self.poop_cmd = config.get('poop_cmd', None)                                # Macro to use when pooping. Change macro name if you would like to use your own poop/purge macro

        self.form_tip = config.getboolean("form_tip", False)                        # Set to True to tip forming when unloading lanes
        self.form_tip_cmd = config.get('form_tip_cmd', None)                        # Macro to use when tip forming. Change macro name if you would like to use your own tip forming macro

        # MOVE SETTINGS
        self.long_moves_speed = config.getfloat("long_moves_speed", 100)            # Speed in mm/s to move filament when doing long moves
        self.long_moves_accel = config.getfloat("long_moves_accel", 400)            # Acceleration in mm/s squared when doing long moves
        self.short_moves_speed = config.getfloat("short_moves_speed", 25)           # Speed in mm/s to move filament when doing short moves
        self.short_moves_accel = config.getfloat("short_moves_accel", 400)          # Acceleration in mm/s squared when doing short moves
        self.short_move_dis = config.getfloat("short_move_dis", 10)                 # Move distance in mm for failsafe moves.
        self.tool_max_unload_attempts = config.getint('tool_max_unload_attempts', 2)# Max number of attempts to unload filament from toolhead when using buffer as ramming sensor
        self.tool_max_load_checks = config.getint('tool_max_load_checks', 4)        # Max number of attempts to check to make sure filament is loaded into toolhead extruder when using buffer as ramming sensor

        self.z_hop =config.getfloat("z_hop", 0)                                     # Height to move up before and after a tool change completes
        self.xy_resume =config.getboolean("xy_resume", False)                       # Need description or remove as this is currently an unused variable
        self.resume_speed =config.getfloat("resume_speed", 0)                       # Speed mm/s of resume move. Set to 0 to use gcode speed
        self.resume_z_speed = config.getfloat("resume_z_speed", 0)                  # Speed mm/s of resume move in Z. Set to 0 to use gcode speed

        self.global_print_current = config.getfloat("global_print_current", None)   # Global variable to set steppers current to a specified current when printing. Going lower than 0.6 may result in TurtleNeck buffer's not working correctly

        self.enable_sensors_in_gui = config.getboolean("enable_sensors_in_gui", False) # Set to True to show all sensor switches as filament sensors in mainsail/fluidd gui
        self.load_to_hub        = config.getboolean("load_to_hub", True)            # Fast loads filament to hub when inserted, set to False to disable. This is a global setting and can be overridden at AFC_stepper
        self._update_trsync(config)

        # Get debug and cast to boolean
        #self.debug = True == config.get('debug', 0)
        self.debug = False

        # Printing here will not display in console but it will go to klippy.log
        self.print_version()

        self.BASE_UNLOAD_FILAMENT    = 'UNLOAD_FILAMENT'
        self.RENAMED_UNLOAD_FILAMENT = '_AFC_RENAMED_{}_'.format(self.BASE_UNLOAD_FILAMENT)

    def _remove_after_last(self, string, char):
        last_index = string.rfind(char)
        if last_index != -1:
            return string[:last_index + 1]
        else:
            return string

    def _update_trsync(self, config):
        # Logic to update trsync values
        update_trsync = config.getboolean("trsync_update", False)                   # Set to true to enable updating trsync value in klipper mcu. Enabling this and updating the timeouts can help with Timer Too Close(TTC) errors
        if update_trsync:
            try:
                import mcu
                trsync_value = config.getfloat("trsync_timeout", 0.05)              # Timeout value to update in klipper mcu. Klippers default value is 0.025
                trsync_single_value = config.getfloat("trsync_single_timeout", 0.5) # Single timeout value to update in klipper mcu. Klippers default value is 0.250
                self.gcode.respond_info("Applying TRSYNC update")

                # Making sure value exists as kalico(danger klipper) does not have TRSYNC_TIMEOUT value
                if( hasattr(mcu, "TRSYNC_TIMEOUT")): mcu.TRSYNC_TIMEOUT = max(mcu.TRSYNC_TIMEOUT, trsync_value)
                else : self.gcode.respond_info("TRSYNC_TIMEOUT does not exist in mcu file, not updating")

                if( hasattr(mcu, "TRSYNC_SINGLE_MCU_TIMEOUT")): mcu.TRSYNC_SINGLE_MCU_TIMEOUT = max(mcu.TRSYNC_SINGLE_MCU_TIMEOUT, trsync_single_value)
                else : self.gcode.respond_info("TRSYNC_SINGLE_MCU_TIMEOUT does not exist in mcu file, not updating")
            except Exception as e:
                self.gcode.respond_info("Unable to update TRSYNC_TIMEOUT: {}".format(e))

    def register_lane_macros(self, lane_obj):
        """
        Callback function to register macros with proper lane names so that klipper errors out correctly when users supply lanes that
        are not valid

        :param lane_obj: object for lane to register
        """
        self.gcode.register_mux_command('LANE_MOVE',    "LANE", lane_obj.name, self.cmd_LANE_MOVE,      desc=self.cmd_LANE_MOVE_help)
        self.gcode.register_mux_command('LANE_UNLOAD',  "LANE", lane_obj.name, self.cmd_LANE_UNLOAD,    desc=self.cmd_LANE_UNLOAD_help)
        self.gcode.register_mux_command('HUB_LOAD',     "LANE", lane_obj.name, self.cmd_HUB_LOAD,       desc=self.cmd_HUB_LOAD_help)
        self.gcode.register_mux_command('TOOL_LOAD',    "LANE", lane_obj.name, self.cmd_TOOL_LOAD,      desc=self.cmd_TOOL_LOAD_help)

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up the toolhead object
        and assigns it to the instance variable `self.toolhead`.
        """
        self.toolhead = self.printer.lookup_object('toolhead')
        
        # SPOOLMAN
        try:
            self.moonraker = json.load(urlopen('http://localhost/server/config'))
            self.spoolman = self.moonraker['result']['orig']['spoolman']['server']     # check for spoolman and grab url
        except:
            self.spoolman = None                      # set to none if not found


        # GCODE REGISTERS
        self.gcode.register_command('TOOL_UNLOAD',          self.cmd_TOOL_UNLOAD,           desc=self.cmd_TOOL_UNLOAD_help)
        self.gcode.register_command('CHANGE_TOOL',          self.cmd_CHANGE_TOOL,           desc=self.cmd_CHANGE_TOOL_help)
        self.gcode.register_command('AFC_STATUS',           self.cmd_AFC_STATUS,            desc=self.cmd_AFC_STATUS_help)
        self.gcode.register_command('SET_AFC_TOOLCHANGES',  self.cmd_SET_AFC_TOOLCHANGES,   desc=self.cmd_SET_AFC_TOOLCHANGES_help)
        self.current_state = State.IDLE

    def print_version(self):
        """
        Calculated AFC git version and displays to console and log
        """
        import subprocess
        import os
        afc_dir  = os.path.dirname(os.path.realpath(__file__))
        git_hash = subprocess.check_output(['git', '-C', '{}'.format(afc_dir), 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
        git_commit_num = subprocess.check_output(['git', '-C', '{}'.format(afc_dir), 'rev-list', 'HEAD', '--count']).decode('ascii').strip()
        self.gcode.respond_info("AFC Version: v{}-{}-{}".format(AFC_VERSION, git_commit_num, git_hash))

    def _get_default_material_temps(self, CUR_LANE):
        """
        Helper function to get material temperatures

        Defaults to min extrude temperature + 5 if nothing is found.

        Returns value that user has inputted if using spoolman, or tries to parse manually entered values
        in AFC.cfg and sees if a temperature exists for filament material.

        :param CUR_LANE: Current lane object
        :return truple : float for temperature to heat extruder to,
                         bool True if user is using min_extruder_temp value
        """
        temp_value = self.heater.min_extrude_temp + 5
        using_min_value = True  # Set it true if default temp/spoolman temps are not being used
        if CUR_LANE.extruder_temp is not None:
            temp_value = CUR_LANE.extruder_temp
            using_min_value = False
        elif self.default_material_temps is not None and CUR_LANE.material is not None:
            for mat in self.default_material_temps:
                m = mat.split(":")
                if m[0] in CUR_LANE.material:
                    temp_value = m[1]
                    using_min_value = False
                    break
        return float(temp_value), using_min_value

    def _check_extruder_temp(self, CUR_LANE):
        """
        Helper function that check to see if extruder needs to be heated, and wait for hotend to get to temp if needed
        """
        # Prepare extruder and heater.
        # This will need to be done a different way for multiple toolhead extruders
        extruder = self.toolhead.get_extruder()
        self.heater = extruder.get_heater()

        pheaters = self.printer.lookup_object('heaters')
        target_temp, using_min_value = self._get_default_material_temps(CUR_LANE)

        # Check to make sure temp is with +/-5 of target temp, not setting if temp is over target temp and using min_extrude_temp value
        if self.heater.target_temp <= (target_temp-5) or (self.heater.target_temp >= (target_temp+5) and not using_min_value):
            wait = False if self.heater.target_temp >= (target_temp+5) else True

            self.gcode.respond_info('Setting extruder temperature to {} {}'.format(target_temp, "and waiting for extruder to reach temperature" if wait else ""))
            pheaters.set_temperature(extruder.get_heater(), target_temp, wait=wait)

    def _check_bypass(self, unload=False):
        """
        Helper function that checks if bypass has filament loaded

        :param unload: Set True if user is trying to unload, when set to True and filament is loaded AFC runs users renamed stock UNLOAD_FILAMENT macro
        :return        Returns true if filament is present in sensor
        """
        try:
            bypass = self.printer.lookup_object('filament_switch_sensor bypass').runout_helper
            if bypass.filament_present:
                if unload:
                    self.gcode.respond_info("Bypass detected, calling manual unload filament routine")
                    self.gcode.run_script_from_command(self.RENAMED_UNLOAD_FILAMENT)
                    self.gcode.respond_info("Filament unloaded")
                else:
                    self.gcode.respond_info("Filament loaded in bypass, not doing tool load")
                return True
        except:
            pass
        return False

    cmd_SET_AFC_TOOLCHANGES_help = "Sets number of toolchanges for AFC to keep track of"
    def cmd_SET_AFC_TOOLCHANGES(self, gcmd):
        """
        This macro can be used to set total number of toolchanges from slicer. AFC will keep track of tool changes and print out
        current tool change number when a T(n) command is called from gcode

        This call can be added to the slicer by adding the following lines to Change filament G-code section in your slicer.
        You may already have `T[next_extruder]`, just make sure the toolchange call is after your T(n) call
        ```
        T[next_extruder]
        { if toolchange_count == 1 }SET_AFC_TOOLCHANGES TOOLCHANGES=[total_toolchanges]{endif }
        ```

        The following can also be added to your `PRINT_END` section in your slicer to set number of toolchanges back to zero
        `SET_AFC_TOOLCHANGES TOOLCHANGES=0`

        Usage: `SET_AFC_TOOLCHANGES TOOLCHANGES=<number>`
        Example: `SET_AFC_TOOLCHANGES TOOLCHANGES=100`

        Args:
            gcmd: The G-code command object containing the parameters for the command.

        Returns:
            None
        """
        self.number_of_toolchanges  = gcmd.get_int("TOOLCHANGES")
        self.current_toolchange     = 0 # Reset back to one
        if self.number_of_toolchanges > 0:
            self.gcode.respond_info("Total number of toolchanges set to {}".format(self.number_of_toolchanges))

    cmd_LANE_MOVE_help = "Lane Manual Movements"
    def cmd_LANE_MOVE(self, gcmd):
        """
        This function handles the manual movement of a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and moves it by the distance specified by the 'DISTANCE' parameter.

        Usage: `LANE_MOVE LANE=<lane> DISTANCE=<distance>`
        Example: `LANE_MOVE LANE=leg1 DISTANCE=100`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  - LANE: The name of the lane to be moved.
                  - DISTANCE: The distance to move the lane.

        NO_DOC: True

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        distance = gcmd.get_float('DISTANCE', 0)
        if lane not in self.lanes:
            self.gcode.respond_info('{} Unknown'.format(lane))
            return
        CUR_LANE = self.lanes[lane]
        self.current_state = State.MOVING_LANE
        CUR_LANE.set_load_current() # Making current is set correctly when doing lane moves
        CUR_LANE.do_enable(True)
        CUR_LANE.move(distance, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
        CUR_LANE.do_enable(False)
        self.current_state = State.IDLE

    def save_pos(self):
        """
        Only save previous location on the first toolchange call to keep an error state from overwriting the location
        """
        if self.in_toolchange == False:
            if self.error_state == False:
                self.last_toolhead_position = self.toolhead.get_position()
                self.base_position          = self.gcode_move.base_position
                self.last_gcode_position    = self.gcode_move.last_position
                self.homing_position        = self.gcode_move.homing_position
                self.speed                  = self.gcode_move.speed
                self.absolute_coord         = self.gcode_move.absolute_coord

    def restore_pos(self):
        """
        restore_pos function restores the previous saved position, speed and coord type. The resume uses
        the z_hop value to lift, move to previous x,y coords, then lower to saved z position.
        """
        self.current_state = State.RESTORING_POS
        newpos = self.toolhead.get_position()
        newpos[2] = self.last_gcode_position[2] + self.z_hop

        # Restore absolute coords
        self.gcode_move.absolute_coord = self.absolute_coord

        speed = self.resume_speed if self.resume_speed > 0 else self.speed
        speedz = self.resume_z_speed if self.resume_z_speed > 0 else self.speed
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
        self.current_state = State.IDLE

    def save_vars(self):
        """
        save_vars function saves lane variables to var file and prints with indents to
                  make it more readable for users
        """
        str = {}
        for UNIT in self.units.keys():
            CUR_UNIT=self.units[UNIT]
            str[CUR_UNIT.name]={}
            name=[]
            for NAME in CUR_UNIT.lanes:
                CUR_LANE=self.lanes[NAME]
                str[CUR_UNIT.name][CUR_LANE.name]=CUR_LANE.get_status()
                name.append(CUR_LANE.name)

        str["system"]={}
        str["system"]['current_load']= self.current
        str["system"]['num_units'] = len(self.units)
        str["system"]['num_lanes'] = len(self.lanes)
        str["system"]['num_extruders'] = len(self.tools)
        str["system"]["extruders"]={}

        for EXTRUDE in self.tools.keys():
            CUR_EXTRUDER = self.tools[EXTRUDE]
            str["system"]["extruders"][CUR_EXTRUDER.name]={}
            str["system"]["extruders"][CUR_EXTRUDER.name]['lane_loaded'] = CUR_EXTRUDER.lane_loaded

        with open(self.VarFile+ '.unit', 'w') as f:
            f.write(json.dumps(str, indent=4))

    # HUB COMMANDS
    cmd_HUB_LOAD_help = "Load lane into hub"
    def cmd_HUB_LOAD(self, gcmd):
        """
        This function handles the loading of a specified lane into the hub. It performs
        several checks and movements to ensure the lane is properly loaded.

        Usage: `HUB_LOAD LANE=<lane>`
        Example: `HUB_LOAD LANE=leg1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameter:
                  - LANE: The name of the lane to be loaded.

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane not in self.lanes:
            self.gcode.respond_info('{} Unknown'.format(lane))
            return
        CUR_LANE = self.lanes[lane]
        CUR_HUB = CUR_LANE.hub_obj
        if CUR_LANE.prep_state == False: return
        CUR_LANE.status = 'HUB Loading'
        if CUR_LANE.load_state == False:
            CUR_LANE.do_enable(True)
            while CUR_LANE.load_state == False:
                CUR_LANE.move( CUR_HUB.move_dis, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
        if CUR_LANE.loaded_to_hub == False:
            CUR_LANE.move(CUR_LANE.dist_hub, CUR_LANE.dist_hub_move_speed, CUR_LANE.dist_hub_move_accel, True if CUR_LANE.dist_hub > 200 else False)
        while CUR_HUB.state == False:
            CUR_LANE.move(CUR_HUB.move_dis, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
        while CUR_HUB.state == True:
            CUR_LANE.move(CUR_HUB.move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
        CUR_LANE.status = None
        CUR_LANE.do_enable(False)
        CUR_LANE.loaded_to_hub = True
        self.save_vars()

    cmd_LANE_UNLOAD_help = "Unload lane from extruder"
    def cmd_LANE_UNLOAD(self, gcmd):
        """
        This function handles the unloading of a specified lane from the extruder. It performs
        several checks and movements to ensure the lane is properly unloaded.

        Usage: `LANE_UNLOAD LANE=<lane>`
        Example: `LANE_UNLOAD LANE=leg1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameter:
                  - LANE: The name of the lane to be unloaded.

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane not in self.lanes:
            self.gcode.respond_info('{} Unknown'.format(lane))
            return
        CUR_LANE = self.lanes[lane]
        CUR_HUB = CUR_LANE.hub_obj

        self.current_state = State.EJECTING_LANE

        if CUR_LANE.name != self.current and CUR_LANE.hub != 'direct':
            # Setting status as ejecting so if filament is removed and de-activates the prep sensor while
            # extruder motors are still running it does not trigger infinite spool or pause logic
            # once user removes filament lanes status will go to None
            CUR_LANE.status = 'ejecting'
            self.save_vars()
            CUR_LANE.do_enable(True)
            if CUR_LANE.loaded_to_hub:
                CUR_LANE.move(CUR_LANE.dist_hub * -1, CUR_LANE.dist_hub_move_speed, CUR_LANE.dist_hub_move_accel, True if CUR_LANE.dist_hub > 200 else False)
            CUR_LANE.loaded_to_hub = False
            while CUR_LANE.load_state == True:
               CUR_LANE.move( CUR_HUB.move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
            CUR_LANE.move( CUR_HUB.move_dis * -5, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
            CUR_LANE.do_enable(False)
            CUR_LANE.status = None
            self.save_vars()

            # Removing spool from vars since it was ejected
            self.SPOOL.set_spoolID( CUR_LANE, "")
            self.gcode.respond_info("LANE {} eject done".format(CUR_LANE.name))

        elif CUR_LANE.name == self.current:
            self.gcode.respond_info("LANE {} is loaded in toolhead, can't unload.".format(CUR_LANE.name))
        
        elif CUR_LANE.hub == 'direct':
            self.gcode.respond_info("LANE {} is a direct lane must be tool unloaded.".format(CUR_LANE.name))

        self.current_state = State.IDLE

    cmd_TOOL_LOAD_help = "Load lane into tool"
    def cmd_TOOL_LOAD(self, gcmd):
        """
        This function handles the loading of a specified lane into the tool. It retrieves
        the lane specified by the 'LANE' parameter and calls the TOOL_LOAD method to perform
        the loading process.

        Usage: `TOOL_LOAD LANE=<lane>`
        Example: `TOOL_LOAD LANE=leg1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameter:
                  - LANE: The name of the lane to be loaded.

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane not in self.lanes:
            self.gcode.respond_info('{} Unknown'.format(lane))
            return

        if self.current is not None:
            self.ERROR.AFC_error("Cannot load {}, {} currently loaded".format(lane, self.current), pause=False)
            return
        CUR_LANE = self.lanes[lane]
        self.TOOL_LOAD(CUR_LANE)

    def TOOL_LOAD(self, CUR_LANE):
        """
        This function handles the loading of a specified lane into the tool. It performs
        several checks and movements to ensure the lane is properly loaded.

        Usage: `TOOL_LOAD LANE=<lane>`
        Example: `TOOL_LOAD LANE=leg1`

        Args:
            CUR_LANE: The lane object to be loaded into the tool.

        Returns:
            bool: True if load was successful, False if an error occurred.
        """
        if not self.FUNCTION.is_homed():
            self.ERROR.AFC_error("Please home printer before doing a tool load", False)
            return False

        if CUR_LANE is None:
            # Exit early if no lane is provided.
            return False

        # Check if the bypass filament sensor is triggered; abort loading if filament is already present.
        if self._check_bypass(): return False

        self.gcode.respond_info("Loading {}".format(CUR_LANE.name))

        # Lookup extruder and hub objects associated with the lane.
        CUR_HUB = CUR_LANE.hub_obj

        CUR_EXTRUDER = CUR_LANE.extruder_obj
        self.current_state = State.LOADING
        self.current_loading = CUR_LANE.name

        # Set the lane status to 'loading' and activate the loading LED.
        CUR_LANE.status = 'Tool Loading'
        self.save_vars()
        self.FUNCTION.afc_led(CUR_LANE.led_loading, CUR_LANE.led_index)

        # Check if the lane is in a state ready to load and hub is clear.
        if (CUR_LANE.load_state and not CUR_HUB.state) or CUR_LANE.hub == 'direct':

            self._check_extruder_temp(CUR_LANE)

            # Enable the lane for filament movement.
            CUR_LANE.do_enable(True)

            # Move filament to the hub if it's not already loaded there.
            if not CUR_LANE.loaded_to_hub or CUR_LANE.hub == 'direct':
                CUR_LANE.move(CUR_LANE.dist_hub, CUR_LANE.dist_hub_move_speed, CUR_LANE.dist_hub_move_accel, CUR_LANE.dist_hub > 200)

            CUR_LANE.loaded_to_hub = True
            hub_attempts = 0

            # Ensure filament moves past the hub.
            while not CUR_HUB.state and CUR_LANE.hub != 'direct':
                if hub_attempts == 0:
                    CUR_LANE.move(CUR_HUB.move_dis, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
                else:
                    CUR_LANE.move(CUR_LANE.short_move_dis, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
                hub_attempts += 1
                if hub_attempts > 20:
                    message = ('PAST HUB, CHECK FILAMENT PATH\n||=====||==>--||-----||\nTRG   LOAD   HUB   TOOL')
                    self.ERROR.handle_lane_failure(CUR_LANE, message)
                    return False

            # Move filament towards the toolhead.
            if CUR_LANE.hub != 'direct':
                CUR_LANE.move(CUR_HUB.afc_bowden_length, CUR_LANE.long_moves_speed, CUR_LANE.long_moves_accel, True)

            # Ensure filament reaches the toolhead.
            tool_attempts = 0
            if CUR_EXTRUDER.tool_start:
                while not CUR_LANE.get_toolhead_sensor_state():
                    tool_attempts += 1
                    CUR_LANE.move(CUR_LANE.short_move_dis, CUR_EXTRUDER.tool_load_speed, CUR_LANE.long_moves_accel)
                    if tool_attempts > 20:
                        message = ('FAILED TO LOAD TO TOOL, CHECK FILAMENT PATH\n||=====||====||==>--||\nTRG   LOAD   HUB   TOOL')
                        self.ERROR.handle_lane_failure(CUR_LANE, message)
                        return False

            # Synchronize lane's extruder stepper and finalize tool loading.
            CUR_LANE.status = 'Tool Loaded'
            self.save_vars()
            CUR_LANE.sync_to_extruder()

            if CUR_EXTRUDER.tool_end:
                pos = self.toolhead.get_position()
                while not CUR_EXTRUDER.tool_end_state:
                    tool_attempts += 1
                    pos[3] += CUR_LANE.short_move_dis
                    self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_load_speed)
                    self.toolhead.wait_moves()
                    if tool_attempts > 20:
                        message = ('FAILED TO LOAD TO TOOL END, CHECK FILAMENT PATH\n||=====||====||==>--||\nTRG   LOAD   HUB   TOOL')
                        self.ERROR.handle_lane_failure(CUR_LANE, message)
                        return False

            # Adjust tool position for loading.
            pos = self.toolhead.get_position()
            pos[3] += CUR_EXTRUDER.tool_stn
            self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_load_speed)
            self.toolhead.wait_moves()

            # Check if ramming is enabled, if it is go through ram load sequence.
            # Lane will load until Advance sensor is True
            # After the tool_stn distance the lane will retract off the sensor to confirm load and reset buffer
            if CUR_EXTRUDER.tool_start == "buffer":
                CUR_LANE.unsync_to_extruder()
                load_checks = 0
                while CUR_LANE.get_toolhead_sensor_state() == True:
                    CUR_LANE.move( CUR_LANE.short_move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel )
                    load_checks += 1
                    self.reactor.pause(self.reactor.monotonic() + 0.1)
                    if load_checks > self.tool_max_load_checks:
                        msg = ''
                        msg += "Buffer did not become compressed after {} short moves.\n".format(self.tool_max_load_checks)
                        msg += "Tool may not be loaded"
                        self.gcode.respond_info("<span class=warning--text>{}</span>".format(msg))
                        break
                CUR_LANE.sync_to_extruder()
            # Update tool and lane status.
            CUR_LANE.set_loaded()
            CUR_LANE.enable_buffer()

            # Activate the tool-loaded LED and handle filament operations if enabled.
            self.FUNCTION.afc_led(CUR_LANE.led_tool_loaded, CUR_LANE.led_index)
            if self.poop:
                self.gcode.run_script_from_command(self.poop_cmd)
                if self.wipe:
                    self.gcode.run_script_from_command(self.wipe_cmd)
            if self.kick:
                self.gcode.run_script_from_command(self.kick_cmd)
            if self.wipe:
                self.gcode.run_script_from_command(self.wipe_cmd)

            # Update lane and extruder state for tracking.
            CUR_EXTRUDER.lane_loaded = CUR_LANE.name
            self.SPOOL.set_active_spool(CUR_LANE.spool_id)
            self.FUNCTION.afc_led(CUR_LANE.led_tool_loaded, CUR_LANE.led_index)
            self.save_vars()
            self.current_state = State.IDLE
        else:
            # Handle errors if the hub is not clear or the lane is not ready for loading.
            if CUR_HUB.state:
                message = ('HUB NOT CLEAR WHEN TRYING TO LOAD\n||-----||----|x|-----||\nTRG   LOAD   HUB   TOOL')
                self.ERROR.handle_lane_failure(CUR_LANE, message)
                return False
            if not CUR_LANE.load_state:
                message = ('NOT READY, LOAD TRIGGER NOT TRIGGERED\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                self.ERROR.handle_lane_failure(CUR_LANE, message)
                return False
        return True

    cmd_TOOL_UNLOAD_help = "Unload from tool head"
    def cmd_TOOL_UNLOAD(self, gcmd):
        """
        This function handles the unloading of a specified lane from the tool head. It retrieves
        the lane specified by the 'LANE' parameter or uses the currently loaded lane if no parameter
        is provided, and calls the TOOL_UNLOAD method to perform the unloading process.

        Usage: `TOOL_UNLOAD [LANE=<lane>]`
        Example: `TOOL_UNLOAD LANE=leg1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameter:
                  - LANE: The name of the lane to be unloaded (optional, defaults to the current lane).

        Returns:
            None
        """
        lane = gcmd.get('LANE', self.current)
        if lane == None:
            return
        if lane not in self.lanes:
            self.gcode.respond_info('{} Unknown'.format(lane))
            return
        CUR_LANE = self.lanes[lane]
        self.TOOL_UNLOAD(CUR_LANE)

        # User manually unloaded spool from toolhead, remove spool from active status
        self.SPOOL.set_active_spool( None )

    def TOOL_UNLOAD(self, CUR_LANE):
        """
        This function handles the unloading of a specified lane from the tool. It performs
        several checks and movements to ensure the lane is properly unloaded.

        Usage: `TOOL_UNLOAD LANE=<lane>`
        Example: `TOOL_UNLOAD LANE=leg1`
        Args:
            CUR_LANE: The lane object to be unloaded from the tool.

        Returns:
            bool: True if unloading was successful, False if an error occurred.
        """
        # Check if the bypass filament sensor detects filament; if so unload filament and abort the tool load.
        if self._check_bypass(unload=True): return False

        if not self.FUNCTION.is_homed():
            self.ERROR.AFC_error("Please home printer before doing a tool unload", False)
            return False

        if CUR_LANE is None:
            # If no lane is provided, exit the function early with a failure.
            return False

        self.current_state  = State.UNLOADING
        self.current_loading = CUR_LANE.name
        self.gcode.respond_info("Unloading {}".format(CUR_LANE.name))
        CUR_LANE.status = 'Tool Unloading'
        self.save_vars()
        # Lookup current extruder and hub objects using the lane's information.
        CUR_HUB = CUR_LANE.hub_obj
        CUR_EXTRUDER = CUR_LANE.extruder_obj

        # Prepare the extruder and heater for unloading.
        self._check_extruder_temp( CUR_LANE )

        # Quick pull to prevent oozing.
        pos = self.toolhead.get_position()
        pos[3] -= 2
        self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
        self.toolhead.wait_moves()

        # Perform Z-hop to avoid collisions during unloading.
        pos[2] += self.z_hop
        self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
        self.toolhead.wait_moves()

        # Disable the buffer if it's active.
        CUR_LANE.disable_buffer()

        # Activate LED indicator for unloading.
        self.FUNCTION.afc_led(CUR_LANE.led_unloading, CUR_LANE.led_index)

        if CUR_LANE.extruder_stepper.motion_queue != CUR_LANE.extruder_name:
            # Synchronize the extruder stepper with the lane.
            CUR_LANE.sync_to_extruder()

        # Enable the lane for unloading operations.
        CUR_LANE.do_enable(True)

        # Perform filament cutting and parking if specified.
        if self.tool_cut:
            self.gcode.run_script_from_command(self.tool_cut_cmd)
            if self.park:
                self.gcode.run_script_from_command(self.park_cmd)

        # Form filament tip if necessary.
        if self.form_tip:
            if self.park:
                self.gcode.run_script_from_command(self.park_cmd)
            if self.form_tip_cmd == "AFC":
                self.tip = self.printer.lookup_object('AFC_form_tip')
                self.tip.tip_form()
            else:
                self.gcode.run_script_from_command(self.form_tip_cmd)

        # Attempt to unload the filament from the extruder, retrying if needed.
        num_tries = 0
        if CUR_EXTRUDER.tool_start == "buffer":
            # if ramming is enabled, AFC will retract to collapse buffer before unloading
            CUR_LANE.unsync_to_extruder()
            while CUR_LANE.get_trailing() == False:
                # attempt to return buffer to trailng pin
                CUR_LANE.move( CUR_LANE.short_move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel )
                num_tries += 1
                self.reactor.pause(self.reactor.monotonic() + 0.1)
                if num_tries > self.tool_max_unload_attempts:
                    msg = ''
                    msg += "Buffer did not become compressed after {} short moves.\n".format(self.tool_max_unload_attempts)
                    msg += "Increasing 'tool_max_unload_attempts' may improve loading reliablity"
                    self.gcode.respond_info("<span class=warning--text>{}</span>".format(msg))
                    break
            CUR_LANE.sync_to_extruder(False)
            pos = self.toolhead.get_position()
            pos[3] -= CUR_EXTRUDER.tool_stn_unload
            self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
            self.toolhead.wait_moves()
        else:
            while CUR_LANE.get_toolhead_sensor_state():
                num_tries += 1
                if num_tries > self.tool_max_unload_attempts:
                    # Handle failure if the filament cannot be unloaded.
                    message = ('FAILED TO UNLOAD. FILAMENT STUCK IN TOOLHEAD.')
                    self.ERROR.handle_lane_failure(CUR_LANE, message)
                    return False
                CUR_LANE.sync_to_extruder()
                pos = self.toolhead.get_position()
                pos[3] -= CUR_EXTRUDER.tool_stn_unload
                self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
                self.toolhead.wait_moves()

        # Move filament past the sensor after the extruder, if applicable.
        if CUR_EXTRUDER.tool_sensor_after_extruder > 0:
            pos = self.toolhead.get_position()
            pos[3] -= CUR_EXTRUDER.tool_sensor_after_extruder
            self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
            self.toolhead.wait_moves()
        self.save_vars()
        # Synchronize and move filament out of the hub.
        CUR_LANE.unsync_to_extruder()
        if CUR_LANE.hub !='direct':
            CUR_LANE.move(CUR_HUB.afc_bowden_length * -1, CUR_LANE.long_moves_speed, CUR_LANE.long_moves_accel, True)
        else:
            CUR_LANE.move(CUR_LANE.dist_hub * -1, CUR_LANE.dist_hub_move_speed, CUR_LANE.dist_hub_move_accel, CUR_LANE.dist_hub > 200)

        # Clear toolhead's loaded state for easier error handling later.
        CUR_LANE.set_unloaded()

        self.save_vars()

        # Ensure filament is fully cleared from the hub.
        num_tries = 0
        while CUR_HUB.state:
            CUR_LANE.move(CUR_LANE.short_move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
            num_tries += 1
            if num_tries > (CUR_HUB.afc_bowden_length / CUR_LANE.short_move_dis):
                # Handle failure if the filament doesn't clear the hub.
                message = 'HUB NOT CLEARING\n'
                self.ERROR.handle_lane_failure(CUR_LANE, message)
                return False

        #Move to make sure hub path is clear based on the move_clear_dis var
        if CUR_LANE.hub !='direct':
            CUR_LANE.move( CUR_HUB.hub_clear_move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)

        # Cut filament at the hub, if configured.
            if CUR_HUB.cut:
                if CUR_HUB.cut_cmd == 'AFC':
                    CUR_HUB.hub_cut(CUR_LANE)
                else:
                    self.gcode.run_script_from_command(CUR_HUB.cut_cmd)

                # Confirm the hub is clear after the cut.
                while CUR_HUB.state:
                    CUR_LANE.move(CUR_LANE.short_move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
                    num_tries += 1
                    # TODO: Figure out max number of tries
                    if num_tries > (CUR_HUB.afc_bowden_length / CUR_LANE.short_move_dis):
                        message = 'HUB NOT CLEARING after hub cut\n'
                        self.ERROR.handle_lane_failure(CUR_LANE, message)
                        return False

        # Finalize unloading and reset lane state.
        CUR_LANE.loaded_to_hub = True
        self.FUNCTION.afc_led(CUR_LANE.led_ready, CUR_LANE.led_index)
        CUR_LANE.status = None

        if CUR_LANE.hub =='direct':
            while CUR_LANE.prep_state:
                CUR_LANE.move( CUR_LANE.short_move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)

        CUR_LANE.do_enable(False)
        self.save_vars()
        self.gcode.respond_info("LANE {} unload done".format(CUR_LANE.name))
        self.current_state = State.IDLE
        return True

    cmd_CHANGE_TOOL_help = "change filaments in tool head"
    def cmd_CHANGE_TOOL(self, gcmd):
        """
        This function handles the tool change process. It retrieves the lane specified by the 'LANE' parameter,
        checks the filament sensor, saves the current position, and performs the tool change by unloading the
        current lane and loading the new lane.

        Usage: `CHANGE_TOOL LANE=<lane>`
        Example: `CHANGE_TOOL LANE=leg1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameter:
                  - LANE: The name of the lane to be loaded.

        Returns:
            None
        """

        # Check if the bypass filament sensor detects filament; if so, abort the tool change.
        if self._check_bypass(unload=False): return

        if not self.FUNCTION.is_homed():
            self.ERROR.AFC_error("Please home printer before doing a tool change", False)
            return

        tmp = gcmd.get_commandline()
        cmd = tmp.upper()
        Tcmd = ''
        if 'CHANGE' in cmd:
            lane = gcmd.get('LANE', None)
            for key in self.tool_cmds.keys():
                if self.tool_cmds[key].upper() == lane.upper():
                    Tcmd = key
                    break
        else:
            Tcmd = cmd

        if Tcmd == '':
            self.gcode.respond_info("I did not understand the change -- " +cmd)
            return
        self.CHANGE_TOOL(self.lanes[self.tool_cmds[Tcmd]])

    def CHANGE_TOOL(self, CUR_LANE):
        # Check if the bypass filament sensor detects filament; if so, abort the tool change.
        if self._check_bypass(unload=False): return

        self.next_lane_load = CUR_LANE.name

        # If the requested lane is not the current lane, proceed with the tool change.
        if CUR_LANE.name != self.current:
            # Save the current toolhead position to allow restoration after the tool change.
            self.save_pos()
            # Set the in_toolchange flag to prevent overwriting the saved position during potential failures.
            self.in_toolchange = True

            # Check if the lane has completed the preparation process required for tool changes.
            if CUR_LANE._afc_prep_done:
                # Log the tool change operation for debugging or informational purposes.
                self.gcode.respond_info("Tool Change - {} -> {}".format(self.current, CUR_LANE.name))
                if not self.error_state and self.number_of_toolchanges != 0 and self.current_toolchange != self.number_of_toolchanges:
                    self.current_toolchange += 1
                    self.gcode.respond_raw("//      Change {} out of {}".format(self.current_toolchange, self.number_of_toolchanges))

                # If a current lane is loaded, unload it first.
                if self.current is not None:
                    if self.current not in self.lanes:
                        self.gcode.respond_info('{} Unknown'.format(self.current))
                        return
                    if not self.TOOL_UNLOAD(self.lanes[self.current]):
                        # Abort if the unloading process fails.
                        msg = (' UNLOAD ERROR NOT CLEARED')
                        self.ERROR.fix(msg, self.lanes[self.current])  #send to error handling
                        return
            # Load the new lane and restore the toolhead position if successful.
            if self.TOOL_LOAD(CUR_LANE) and not self.error_state:
                self.gcode.respond_info("{} is now loaded in toolhead".format(CUR_LANE.name))
                self.restore_pos()
                self.in_toolchange = False
                # Setting next lane load as none since toolchange was successful
                self.next_lane_load = None
        else:
            self.gcode.respond_info("{} already loaded".format(CUR_LANE.name))
            if not self.error_state and self.number_of_toolchanges != 0 and self.current_toolchange != self.number_of_toolchanges:
                self.current_toolchange += 1

    def get_status(self, eventtime=None):
        """
        Displays current status of AFC for webhooks
        """
        str = {}
        str['current_load']             = self.current
        str['current_lane']             = self.current_loading
        str['next_lane']                = self.next_lane_load
        str['current_state']            = self.current_state
        str["current_toolchange"]       = self.current_toolchange
        str["number_of_toolchanges"]    = self.number_of_toolchanges
        str['spoolman']             = self.spoolman
        unitdisplay =[]
        for UNIT in self.units.keys():
            CUR_UNIT=self.units[UNIT]
            type  =CUR_UNIT.type.replace(" ","_")
            unitdisplay.append(type.replace("'","") + " " + CUR_UNIT.name)
        str['units'] = list(unitdisplay)
        str['lanes'] = list(self.lanes.keys())
        str["extruders"] = list(self.tools.keys())
        str["hubs"] = list(self.hubs.keys())
        str["buffers"] = list(self.buffers.keys())
        return str

    def _webhooks_status(self, web_request):
        """
        Webhooks callback for <ip_address>/printer/afc/status, and displays current AFC status for everything
        """
        str = {}
        numoflanes = 0
        for unit in self.units.values():
            str.update({unit.name: { "system": {}}})
            name=[]
            for lane in unit.lanes.values():
                str[unit.name][lane.name]=lane.get_status()
                numoflanes +=1
                name.append(lane.name)
            str[unit.name]['system']['type'] = unit.type
            str[unit.name]['system']['hub_loaded'] = unit.hub_obj.state

        str["system"]={}
        str["system"]['current_load']= self.current
        str["system"]['num_units'] = len(self.units)
        str["system"]['num_lanes'] = numoflanes
        str["system"]['num_extruders'] = len(self.tools)
        str["system"]["extruders"]={}
        str["system"]["hubs"] = {}
        str["system"]["buffers"] = {}
        str["current_toolchange"]       = self.current_toolchange
        str["number_of_toolchanges"]    = self.number_of_toolchanges

        for extruder in self.tools.values():
            str["system"]["extruders"][extruder.name] = extruder.get_status()

        for hub in self.hubs.values():
            str["system"]["hubs"][hub.name] = hub.get_status()

        for buffer in self.buffers.values():
            str["system"]["buffers"][buffer.name] = buffer.get_status()

        web_request.send( {"status:" : {"AFC": str}})

    cmd_AFC_STATUS_help = "Return current status of AFC"
    def cmd_AFC_STATUS(self, gcmd):
        """
        This function generates a status message for each unit and lane, indicating the preparation,
        loading, hub, and tool states. The status message is formatted with HTML tags for display.

        Usage: `AFC_STATUS`
        Example: `AFC_STATUS`

        Args:
            gcmd: The G-code command object containing the parameters for the command.

        Returns:
            None
        """
        status_msg = ''

        for UNIT in self.units.values():
            # Find the maximum length of lane names to determine the column width
            max_lane_length = max(len(lane) for lane in UNIT.lanes.keys())

            status_msg += '<span class=info--text>{} Status</span>\n'.format(UNIT.name)

            # Create a dynamic format string that adjusts based on lane name length
            header_format = '{:<{}} | Prep | Load |\n'
            status_msg += header_format.format("LANE", max_lane_length)

            for CUR_LANE in UNIT.lanes.values():
                lane_msg = ''
                if self.current != None:
                    if self.current == CUR_LANE.name:
                        if not CUR_LANE.get_toolhead_sensor_state() or not CUR_LANE.hub_obj.state:
                            lane_msg += '<span class=warning--text>{:<{}} </span>'.format(CUR_LANE.name, max_lane_length)
                        else:
                            lane_msg += '<span class=success--text>{:<{}} </span>'.format(CUR_LANE.name, max_lane_length)
                    else:
                        lane_msg += '{:<{}} '.format(CUR_LANE.name,max_lane_length)
                else:
                    lane_msg += '{:<{}} '.format(CUR_LANE.name,max_lane_length)

                if CUR_LANE.prep_state == True:
                    lane_msg += '| <span class=success--text><--></span> |'
                else:
                    lane_msg += '|  <span class=error--text>xx</span>  |'
                if CUR_LANE.load_state == True:
                    lane_msg += ' <span class=success--text><--></span> |\n'
                else:
                    lane_msg += '  <span class=error--text>xx</span>  |\n'
                status_msg += lane_msg

            if CUR_LANE.hub_obj.state == True:
                status_msg += 'HUB: <span class=success--text><-></span>'
            else:
                status_msg += 'HUB: <span class=error--text>x</span>'

            extruder_msg = '  Tool: <span class=error--text>x</span>'
            if CUR_LANE.extruder_obj.tool_start != "buffer":
                if CUR_LANE.extruder_obj.tool_start_state == True:
                    extruder_msg = '  Tool: <span class=success--text><-></span>'
            else:
                if CUR_LANE.tool_loaded and CUR_LANE.extruder_obj.lane_loaded in self.units[UNIT]:
                    if CUR_LANE.get_toolhead_sensor_state() == True:
                        extruder_msg = '  Tool: <span class=success--text><-></span>'

            status_msg += extruder_msg
            if CUR_LANE.extruder_obj.tool_start == 'buffer':
                status_msg += '\n<span class=info--text>Ram sensor enabled</span>\n'

        self.gcode.respond_raw(status_msg)
