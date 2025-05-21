# Armored Turtle Automated Filament Control
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import json
import re
from configfile import error
from typing import Any

from extras.AFC_lane import AFCLaneState, SpeedMode, AssistActive

try:
    from urllib.request import urlopen
except:
    # Python 2.7 support
    from urllib2 import urlopen

try: from extras.AFC_logger import AFC_logger
except: raise error("Error trying to import AFC_logger, please rerun install-afc.sh script in your AFC-Klipper-Add-On directory then restart klipper")

try: from extras.AFC_functions import afcDeltaTime
except: raise error("Error trying to import afcDeltaTime, please rerun install-afc.sh script in your AFC-Klipper-Add-On directory then restart klipper")

try: from extras.AFC_utils import add_filament_switch
except: raise error("Error trying to import AFC_utils, please rerun install-afc.sh script in your AFC-Klipper-Add-On directory then restart klipper")

AFC_VERSION="1.0.12"

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
        self.logger  = AFC_logger(self.printer, self)

        self.spool      = self.printer.load_object(config, 'AFC_spool')
        self.error      = self.printer.load_object(config, 'AFC_error')
        self.function   = self.printer.load_object(config, 'AFC_functions')
        self.gcode      = self.printer.lookup_object('gcode')

        # Registering stepper callback so that mux macro can be set properly with valid lane names
        self.printer.register_event_handler("afc_stepper:register_macros",self.register_lane_macros)
        # Registering for sdcard reset file so that error_state can be reset when starting a print
        self.printer.register_event_handler("virtual_sdcard:reset_file", self.error.reset_failure)
        # Registering webhooks endpoint for <ip_address>/printer/afc/status
        self.webhooks.register_endpoint("afc/status", self._webhooks_status)

        self.current        = None
        self.current_loading= None
        self.next_lane_load = None
        self.error_state    = False
        self.current_state  = State.INIT
        self.position_saved = False
        self.spoolman       = None
        self.prep_done      = False         # Variable used to hold of save_vars function from saving too early and overriding save before prep can be ran

        # Objects for everything configured for AFC
        self.units      = {}
        self.tools      = {}
        self.lanes      = {}
        self.hubs       = {}
        self.buffers    = {}
        self.tool_cmds  = {}
        self.led_obj    = {}
        self.bypass     = None
        self.bypass_last_state = False
        self.message_queue = []
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
        self.speed              = 25.
        self.speed_factor       = 1./60.
        self.absolute_coord     = True
        self.absolute_extrude   = True
        self.extrude_factor     = 1.

        # Config get section
        self.moonraker_port         = config.get("moonraker_port", None)             # Port to connect to when interacting with moonraker. Used when there are multiple moonraker/klipper instances on a single host
        self.unit_order_list        = config.get('unit_order_list','')
        self.VarFile                = config.get('VarFile','../printer_data/config/AFC/')# Path to the variables file for AFC configuration.
        self.cfgloc                 = self._remove_after_last(self.VarFile,"/")
        self.default_material_temps = config.getlists("default_material_temps", None)# Default temperature to set extruder when loading/unloading lanes. Material needs to be either manually set or uses material from spoolman if extruder temp is not set in spoolman.
        self.default_material_temps = list(self.default_material_temps) if self.default_material_temps is not None else None
        self.default_material_type  = config.get("default_material_type", None)     # Default material type to assign to a spool once loaded into a lane

        #LED SETTINGS
        self.ind_lights = None
        # led_name is not used, either use or needs to be removed
        self.led_name               = config.get('led_name',None)
        self.led_fault              = config.get('led_fault','1,0,0,0')             # LED color to set when faults occur in lane        (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_ready              = config.get('led_ready','1,1,1,1')             # LED color to set when lane is ready               (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_not_ready          = config.get('led_not_ready','1,1,0,0')         # LED color to set when lane not ready              (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_loading            = config.get('led_loading','1,0,0,0')           # LED color to set when lane is loading             (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_prep_loaded        = config.get('led_loading','1,1,0,0')           # LED color to set when lane is loaded              (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_unloading          = config.get('led_unloading','1,1,.5,0')        # LED color to set when lane is unloading           (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_tool_loaded        = config.get('led_tool_loaded','1,1,0,0')       # LED color to set when lane is loaded into tool    (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_advancing          = config.get('led_buffer_advancing','0,0,1,0')  # LED color to set when buffer is advancing         (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_trailing           = config.get('led_buffer_trailing','0,1,0,0')   # LED color to set when buffer is trailing          (R,G,B,W) 0 = off, 1 = full brightness.
        self.led_buffer_disabled    = config.get('led_buffer_disable', '0,0,0,0.25')# LED color to set when buffer is disabled          (R,G,B,W) 0 = off, 1 = full brightness.

        # TOOL Cutting Settings
        self.tool                   = ''
        self.tool_cut               = config.getboolean("tool_cut", False)          # Set to True to enable toolhead cutting
        self.tool_cut_cmd           = config.get('tool_cut_cmd', None)              # Macro to use when doing toolhead cutting. Change macro name if you would like to use your own cutting macro

        # CHOICES
        self.park                   = config.getboolean("park", False)              # Set to True to enable parking during unload
        self.park_cmd               = config.get('park_cmd', None)                  # Macro to use when parking. Change macro name if you would like to use your own park macro
        self.kick                   = config.getboolean("kick", False)              # Set to True to enable poop kicking after lane loads
        self.kick_cmd               = config.get('kick_cmd', None)                  # Macro to use when kicking. Change macro name if you would like to use your own kick macro
        self.wipe                   = config.getboolean("wipe", False)              # Set to True to enable nozzle wiping after lane loads
        self.wipe_cmd               = config.get('wipe_cmd', None)                  # Macro to use when nozzle wiping. Change macro name if you would like to use your own wipe macro
        self.poop                   = config.getboolean("poop", False)              # Set to True to enable pooping(purging color) after lane loads
        self.poop_cmd               = config.get('poop_cmd', None)                  # Macro to use when pooping. Change macro name if you would like to use your own poop/purge macro

        self.form_tip               = config.getboolean("form_tip", False)          # Set to True to tip forming when unloading lanes
        self.form_tip_cmd           = config.get('form_tip_cmd', None)              # Macro to use when tip forming. Change macro name if you would like to use your own tip forming macro

        # MOVE SETTINGS
        self.quiet_mode             = False                                         # Flag indicating if quiet move is enabled or not
        self.show_quiet_mode        = config.getboolean("show_quiet_mode", True)   # Flag indicating if quiet move is enabled or not
        self.quiet_moves_speed      = config.getfloat("quiet_moves_speed", 50)      # Max speed in mm/s to move filament during quietmode
        self.long_moves_speed       = config.getfloat("long_moves_speed", 100)      # Speed in mm/s to move filament when doing long moves
        self.long_moves_accel       = config.getfloat("long_moves_accel", 400)      # Acceleration in mm/s squared when doing long moves
        self.short_moves_speed      = config.getfloat("short_moves_speed", 25)      # Speed in mm/s to move filament when doing short moves
        self.short_moves_accel      = config.getfloat("short_moves_accel", 400)     # Acceleration in mm/s squared when doing short moves
        self.short_move_dis         = config.getfloat("short_move_dis", 10)         # Move distance in mm for failsafe moves.
        self.tool_homing_distance   = config.getfloat("tool_homing_distance", 200)  # Distance over which toolhead homing is to be attempted.
        self.max_move_dis           = config.getfloat("max_move_dis", 999999)       # Maximum distance to move filament. AFC breaks filament moves over this number into multiple moves. Useful to lower this number if running into timer too close errors when doing long filament moves.
        self.n20_break_delay_time   = config.getfloat("n20_break_delay_time", 0.200)# Time to wait between breaking n20 motors(nSleep/FWD/RWD all 1) and then releasing the break to allow coasting.

        self.tool_max_unload_attempts= config.getint('tool_max_unload_attempts', 2) # Max number of attempts to unload filament from toolhead when using buffer as ramming sensor
        self.tool_max_load_checks   = config.getint('tool_max_load_checks', 4)      # Max number of attempts to check to make sure filament is loaded into toolhead extruder when using buffer as ramming sensor

        self.rev_long_moves_speed_factor 	= config.getfloat("rev_long_moves_speed_factor", 1.)     # scalar speed factor when reversing filamentalist

        self.z_hop                  = config.getfloat("z_hop", 0)                   # Height to move up before and after a tool change completes
        self.xy_resume              = config.getboolean("xy_resume", False)         # Need description or remove as this is currently an unused variable
        self.resume_speed           = config.getfloat("resume_speed", self.speed)   # Speed mm/s of resume move. Set to 0 to use gcode speed
        self.resume_z_speed         = config.getfloat("resume_z_speed", self.speed) # Speed mm/s of resume move in Z. Set to 0 to use gcode speed

        self.global_print_current   = config.getfloat("global_print_current", None) # Global variable to set steppers current to a specified current when printing. Going lower than 0.6 may result in TurtleNeck buffer's not working correctly

        self.enable_sensors_in_gui  = config.getboolean("enable_sensors_in_gui", False) # Set to True to show all sensor switches as filament sensors in mainsail/fluidd gui
        self.load_to_hub            = config.getboolean("load_to_hub", True)        # Fast loads filament to hub when inserted, set to False to disable. This is a global setting and can be overridden at AFC_stepper
        self.assisted_unload        = config.getboolean("assisted_unload", True)    # If True, the unload retract is assisted to prevent loose windings, especially on full spools. This can prevent loops from slipping off the spool
        self.bypass_pause           = config.getboolean("pause_when_bypass_active", False) # When true AFC pauses print when change tool is called and bypass is loaded
        self.unload_on_runout       = config.getboolean("unload_on_runout", False)  # When True AFC will unload lane and then pause when runout is triggered and spool to swap to is not set(infinite spool)

        self.debug                  = config.getboolean('debug', False)             # Setting to True turns on more debugging to show on console
        # Get debug and cast to boolean
        self.logger.set_debug( self.debug )
        self._update_trsync(config)

        # Setup pin so a virtual filament sensor can be added for bypass and quiet mode
        self.printer.lookup_object("pins").register_chip("afc_virtual_bypass", self)
        self.printer.lookup_object("pins").register_chip("afc_quiet_mode", self)

        # Printing here will not display in console but it will go to klippy.log
        self.print_version()

        self.BASE_UNLOAD_FILAMENT    = 'UNLOAD_FILAMENT'
        self.RENAMED_UNLOAD_FILAMENT = '_AFC_RENAMED_{}_'.format(self.BASE_UNLOAD_FILAMENT)

        self.afcDeltaTime = afcDeltaTime(self)

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
                self.logger.info("Applying TRSYNC update")

                # Making sure value exists as kalico(danger klipper) does not have TRSYNC_TIMEOUT value
                if hasattr(mcu, "TRSYNC_TIMEOUT"): mcu.TRSYNC_TIMEOUT = max(mcu.TRSYNC_TIMEOUT, trsync_value)
                else : self.logger.info("TRSYNC_TIMEOUT does not exist in mcu file, not updating")

                if hasattr(mcu, "TRSYNC_SINGLE_MCU_TIMEOUT"): mcu.TRSYNC_SINGLE_MCU_TIMEOUT = max(mcu.TRSYNC_SINGLE_MCU_TIMEOUT, trsync_single_value)
                else : self.logger.info("TRSYNC_SINGLE_MCU_TIMEOUT does not exist in mcu file, not updating")
            except Exception as e:
                self.logger.info("Unable to update TRSYNC_TIMEOUT: {}".format(e))

    def register_config_callback(self, option):
        # Function needed for virtual pins, does nothing
        return

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
        self.toolhead   = self.printer.lookup_object('toolhead')
        self.idle       = self.printer.lookup_object('idle_timeout')
        self.gcode_move = self.printer.lookup_object('gcode_move')

        moonraker_port = ""
        if self.moonraker_port is not None: moonraker_port = ":{}".format(self.moonraker_port)

        # SPOOLMAN
        try:
            self.moonraker = json.load(urlopen('http://localhost{port}/server/config'.format( port=moonraker_port )))
            self.spoolman = self.moonraker['result']['orig']['spoolman']['server']     # check for spoolman and grab url
        except:
            self.spoolman = None                      # set to none if not found

        # Check if hardware bypass is configured, if not create a virtual bypass sensor
        try:
            self.bypass = self.printer.lookup_object('filament_switch_sensor bypass').runout_helper
        except:
            self.bypass = add_filament_switch("filament_switch_sensor virtual_bypass", "afc_virtual_bypass:virtual_bypass", self.printer ).runout_helper

        if self.show_quiet_mode:
            self.quiet_switch = add_filament_switch("filament_switch_sensor quiet_mode", "afc_quiet_mode:afc_quiet_mode", self.printer ).runout_helper

        # GCODE REGISTERS
        self.gcode.register_command('AFC_QUIET_MODE',           self.cmd_AFC_QUIET_MODE,        desc=self.cmd_AFC_QUIET_MODE_help)
        self.gcode.register_command('TOOL_UNLOAD',          self.cmd_TOOL_UNLOAD,           desc=self.cmd_TOOL_UNLOAD_help)
        self.gcode.register_command('CHANGE_TOOL',          self.cmd_CHANGE_TOOL,           desc=self.cmd_CHANGE_TOOL_help)
        self.gcode.register_command('AFC_STATUS',           self.cmd_AFC_STATUS,            desc=self.cmd_AFC_STATUS_help)
        self.gcode.register_command('SET_AFC_TOOLCHANGES',  self.cmd_SET_AFC_TOOLCHANGES,   desc=self.cmd_SET_AFC_TOOLCHANGES_help)
        self.gcode.register_command('UNSET_LANE_LOADED',    self.cmd_UNSET_LANE_LOADED,     desc=self.cmd_UNSET_LANE_LOADED_help)
        self.gcode.register_command('TURN_OFF_AFC_LED',     self.cmd_TURN_OFF_AFC_LED,      desc=self.cmd_TURN_OFF_AFC_LED_help)
        self.gcode.register_command('TURN_ON_AFC_LED',      self.cmd_TURN_ON_AFC_LED,       desc=self.cmd_TURN_ON_AFC_LED_help)
        self.current_state = State.IDLE

    def print_version(self, console_only=False):
        """
        Calculated AFC git version and displays to console and log
        """
        import subprocess
        import os
        afc_dir  = os.path.dirname(os.path.realpath(__file__))
        git_hash = subprocess.check_output(['git', '-C', '{}'.format(afc_dir), 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
        git_commit_num = subprocess.check_output(['git', '-C', '{}'.format(afc_dir), 'rev-list', 'HEAD', '--count']).decode('ascii').strip()
        string  = "AFC Version: v{}-{}-{}".format(AFC_VERSION, git_commit_num, git_hash)

        self.logger.info(string, console_only)

    def _get_default_material_temps(self, cur_lane):
        """
        Helper function to get material temperatures

        Defaults to min extrude temperature + 5 if nothing is found.

        Returns value that user has inputted if using spoolman, or tries to parse manually entered values
        in AFC.cfg and sees if a temperature exists for filament material.

        :param cur_lane: Current lane object
        :return truple : float for temperature to heat extruder to,
                         bool True if user is using min_extruder_temp value
        """
        try:
            # Try to get default value from list, if it does not exist then default to min_extrude_temp + 5
            temp_value = [val for val in self.default_material_temps if 'default' in val][0].split(":")[1]
        except:
            temp_value = self.heater.min_extrude_temp + 5

        using_min_value = True  # Set it true if default temp/spoolman temps are not being used
        if cur_lane.extruder_temp is not None:
            temp_value = cur_lane.extruder_temp
            using_min_value = False
        elif self.default_material_temps is not None and cur_lane.material is not None:
            for mat in self.default_material_temps:
                m = mat.split(":")
                if m[0] in cur_lane.material:
                    temp_value = m[1]
                    using_min_value = False
                    break
        return float(temp_value), using_min_value

    def _check_extruder_temp(self, cur_lane):
        """
        Helper function that check to see if extruder needs to be heated, and wait for hotend to get to temp if needed
        """

        # Prepare extruder and heater.
        # This will need to be done a different way for multiple toolhead extruders
        extruder = self.toolhead.get_extruder()
        self.heater = extruder.get_heater()
        pheaters = self.printer.lookup_object('heaters')
        wait = False

        # If extruder can extruder and printing return and do not update temperature, don't want to modify extruder temperature during prints
        if self.heater.can_extrude and self.function.is_printing():
            return
        target_temp, using_min_value = self._get_default_material_temps(cur_lane)

        current_temp = self.heater.get_temp(self.reactor.monotonic())

        # Check if the current temp is below the set temp, if it is heat to set temp
        if current_temp[0] < (self.heater.target_temp-5):
            wait = False
            pheaters.set_temperature(extruder.get_heater(), current_temp[0], wait=wait)
            self.logger.info('Current temp {:.1f} is below set temp {}'.format(current_temp[0], target_temp))

        # Check to make sure temp is with +/-5 of target temp, not setting if temp is over target temp and using min_extrude_temp value
        if self.heater.target_temp <= (target_temp-5) or (self.heater.target_temp >= (target_temp+5) and not using_min_value):
            wait = False if self.heater.target_temp >= (target_temp+5) else True

            self.logger.info('Setting extruder temperature to {} {}'.format(target_temp, "and waiting for extruder to reach temperature" if wait else ""))
            pheaters.set_temperature(extruder.get_heater(), target_temp, wait=wait)

        return wait

    def _set_quiet_mode(self, val):
        """
        Helper function to set quiet mode to on or off

        :param val: on or off switch
        """
        if self.show_quiet_mode:
            self.quiet_switch.sensor_enabled = val
            self.quiet_switch.filament_present = val
        else:
            self.quiet_mode = val

    def _get_quiet_mode(self):
        """
        Helper function to return if quiet is on or off

        :return Returns current state of quiet switch
        """
        if self.show_quiet_mode:
            try:
                state = self.quiet_switch.sensor_enabled
                self.quiet_switch.filament_present = state
                return state
            except:
                return False
        else:
            return self.quiet_mode

    def _get_bypass_state(self):
        """
        Helper function to return if filament is present in bypass sensor

        :return Returns current state of bypass sensor. If bypass sensor does not exist, always returns False
        """
        bypass_state = False

        try:
            if 'virtual' in self.bypass.name:
                bypass_state = self.bypass.sensor_enabled
                # Update filament present to match enable button so it updates in guis
                self.bypass.filament_present = bypass_state

                if self.bypass_last_state != bypass_state:
                    self.bypass_last_state = bypass_state
                    self.save_vars()

            else:
                bypass_state = self.bypass.filament_present
        except:
            pass

        return bypass_state

    def _check_bypass(self, unload=False):
        """
        Helper function that checks if bypass has filament loaded

        :param unload: Set True if user is trying to unload, when set to True and filament is loaded AFC runs users renamed stock UNLOAD_FILAMENT macro
        :return        Returns true if filament is present in sensor
        """
        try:
            if self._get_bypass_state():
                if unload:
                    self.logger.info("Bypass detected, calling manual unload filament routine")
                    self.gcode.run_script_from_command(self.RENAMED_UNLOAD_FILAMENT)
                    self.logger.info("Filament unloaded")
                else:
                    msg = "Filament loaded in bypass, not doing tool load"
                    # If printing report as error, only pause if in a print and bypass_pause variable is True
                    self.error.AFC_error(msg, pause= (self.function.in_print() and self.bypass_pause))
                return True
        except:
            pass
        return False


    cmd_AFC_QUIET_MODE_help = "Set quiet mode speed and enable/disable quiet mode"
    def cmd_AFC_QUIET_MODE(self, gcmd):
        """
        Set lower speed on any filament moves.

        Mainly this would be used to turn down motor noise during late quiet runs. Only exceptions are during bowden calibration and lane reset, which are manually triggered

        Usage
        -------
        `AFC_QUIET_MODE SPEED=<new quietmode speed> ENABLE=<1 or 0>`

        Example
        -------
        ```
        AFC_QUIET_MODE SPEED=75 ENABLE=1
        ```
        """
        self._set_quiet_mode(bool(gcmd.get_int("ENABLE", self._get_quiet_mode(), minval=0, maxval=1)))
        self.quiet_moves_speed = gcmd.get_float("SPEED", self.quiet_moves_speed, minval=10, maxval=400)
        self.logger.info("QuietMode {}, max speed of {} mm/sec".format(self._get_quiet_mode(), self.quiet_moves_speed))


    cmd_UNSET_LANE_LOADED_help = "Removes active lane loaded from toolhead loaded status"
    def cmd_UNSET_LANE_LOADED(self, gcmd):
        """
        Unsets the current lane from AFC loaded status.

        Mainly this would be used if AFC thinks that there is a lane loaded into the toolhead but nothing is actually
        loaded.

        Usage
        -------
        `UNSET_LANE_LOADED`

        Example
        -------
        ```
        UNSET_LANE_LOADED
        ```
        """
        self.function.unset_lane_loaded()

    cmd_SET_AFC_TOOLCHANGES_help = "Sets number of toolchanges for AFC to keep track of"
    def cmd_SET_AFC_TOOLCHANGES(self, gcmd):
        """
        This macro can be used to set the total number of tool changes from the slicer. AFC will keep track of tool changes and print out
        the current tool change number when a T(n) command is called from G-code.

        The following call can be added to the slicer by adding the following lines to the Change filament G-code section in your slicer.

        You may already have `T[next_extruder]`, just make sure the tool change call is after your T(n) call:

        `T[next_extruder] { if toolchange_count == 1 }SET_AFC_TOOLCHANGES TOOLCHANGES=[total_toolchanges]{endif }`

        The following can also be added to your `PRINT_END` section in your slicer to set the number of tool changes back to zero:

        `SET_AFC_TOOLCHANGES TOOLCHANGES=0`

        Usage
        -----
        `SET_AFC_TOOLCHANGES TOOLCHANGES=<number>`

        Example
        -------
        ```
        SET_AFC_TOOLCHANGES TOOLCHANGES=100
        ```

        """
        self.number_of_toolchanges  = gcmd.get_int("TOOLCHANGES")
        self.current_toolchange     = 0 # Reset back to one
        if self.number_of_toolchanges > 0:
            self.logger.info("Total number of toolchanges set to {}".format(self.number_of_toolchanges))

    cmd_LANE_MOVE_help = "Lane Manual Movements"
    def cmd_LANE_MOVE(self, gcmd):
        """
        This function handles the manual movement of a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and moves it by the distance specified by the 'DISTANCE' parameter.

        Distance's lower than 200 moves extruder at short_move_speed/accel, values above 200 move extruder at long_move_speed/accel

        Usage
        -----
        `LANE_MOVE LANE=<lane> DISTANCE=<distance>`

        Example
        -----
        ```
        LANE_MOVE LANE=lane1 DISTANCE=100
        ```
        """
        if self.function.is_printing():
            self.error.AFC_error("Cannot move lane while printer is printing", pause=False)
            return
        lane = gcmd.get('LANE', None)
        distance = gcmd.get_float('DISTANCE', 0)
        if lane not in self.lanes:
            self.logger.info('{} Unknown'.format(lane))
            return
        cur_lane = self.lanes[lane]
        self.current_state = State.MOVING_LANE

        speed_mode = SpeedMode.SHORT
        if abs(distance) >= 200: speed_mode = SpeedMode.LONG

        cur_lane.set_load_current() # Making current is set correctly when doing lane moves
        cur_lane.do_enable(True)
        cur_lane.move_advanced(distance, speed_mode, assist_active = AssistActive.YES)
        cur_lane.do_enable(False)
        self.current_state = State.IDLE
        cur_lane.unit_obj.return_to_home()
        # Put CAM back to lane if its loaded to toolhead
        self.function.select_loaded_lane()

    def _get_resume_speed(self):
        """
        Common function for return resume speed
        """
        return self.resume_speed if self.resume_speed > 0 else self.speed

    def _get_resume_speedz(self):
        """
        Common function for return resume z speed
        """
        return self.resume_z_speed if self.resume_z_speed > 0 else self.speed

    def _move_z_pos(self, z_amount):
        """
        Common function helper to move z, also does a check for max z so toolhead does not exceed max height

        :param base_pos: position to apply z amount to
        :param z_amount: amount to add to the base position

        :return newpos: Position list with updated z position
        """
        max_z = self.toolhead.get_status(0)['axis_maximum'][2]
        newpos = self.toolhead.get_position()

        # Determine z movement, get the min value to not exceed max z movement
        newpos[2] = min(max_z - 1, z_amount)

        self.gcode_move.move_with_transform(newpos, self._get_resume_speedz())
        # Update gcode move last position to current position
        self.gcode_move.reset_last_position()
        self.function.log_toolhead_pos("_move_z_pos: ")

        return newpos[2]

    def save_pos(self):
        """
        Only save previous location on the first toolchange call to keep an error state from overwriting the location
        """
        if not self.in_toolchange:
            if not self.error_state and not self.function.is_paused() and not self.position_saved:
                self.position_saved         = True
                self.last_toolhead_position = self.toolhead.get_position()
                self.base_position          = list(self.gcode_move.base_position)
                self.last_gcode_position    = list(self.gcode_move.last_position)
                self.homing_position        = list(self.gcode_move.homing_position)
                self.speed                  = self.gcode_move.speed
                self.speed_factor           = self.gcode_move.speed_factor
                self.absolute_coord         = self.gcode_move.absolute_coord
                self.absolute_extrude       = self.gcode_move.absolute_extrude
                self.extrude_factor         = self.gcode_move.extrude_factor
                msg = "Saving position {}".format(self.last_toolhead_position)
                msg += " Base position: {}".format(self.base_position)
                msg += " last_gcode_position: {}".format(self.last_gcode_position)
                msg += " homing_position: {}".format(self.homing_position)
                msg += " speed: {}".format(self.speed)
                msg += " speed_factor: {}".format(self.speed_factor)
                msg += " absolute_coord: {}".format(self.absolute_coord)
                msg += " absolute_extrude: {}".format(self.absolute_extrude)
                msg += " extrude_factor: {}\n".format(self.extrude_factor)
                self.logger.debug(msg)
            else:
                self.function.log_toolhead_pos("Not Saving, Error State: {}, Is Paused {}, Position_saved {}, POS: ".format(self.error_state, self.function.is_paused(), self.position_saved))
        else:
            self.function.log_toolhead_pos("Not Saving In a toolchange, Error State: {}, Is Paused {}, Position_saved {}, in toolchange: {}, POS: ".format(
                self.error_state, self.function.is_paused(), self.position_saved, self.in_toolchange ))

    def restore_pos(self, move_z_first=True):
        """
        restore_pos function restores the previous saved position, speed and coord type. The resume uses
        the z_hop value to lift, move to previous x,y coords, then lower to saved z position.

        :param move_z_first: Enable to move z before moving x,y
        """
        msg = "Restoring Position {}".format(self.last_toolhead_position)
        msg += " Base position: {}".format(self.base_position)
        msg += " last_gcode_position: {}".format(self.last_gcode_position)
        msg += " homing_position: {}".format(self.homing_position)
        msg += " speed: {}".format(self.speed)
        msg += " speed_factor: {}".format(self.speed_factor)
        msg += " absolute_coord: {}".format(self.absolute_coord)
        msg += " absolute_extrude: {}".format(self.absolute_extrude)
        msg += " extrude_factor: {}\n".format(self.extrude_factor)
        self.logger.debug(msg)
        self.function.log_toolhead_pos("Resume initial pos: ")

        self.current_state = State.RESTORING_POS
        newpos = self.toolhead.get_position()

        # Move toolhead to previous z location with zhop added
        if move_z_first:
            newpos[2] = self._move_z_pos(self.last_gcode_position[2] + self.z_hop)

        # Move to previous x,y location
        newpos[:2] = self.last_gcode_position[:2]
        self.gcode_move.move_with_transform(newpos, self._get_resume_speed() )
        self.function.log_toolhead_pos("Resume prev xy: ")

        # Update GCODE STATE variables
        self.gcode_move.base_position       = list(self.base_position)
        self.gcode_move.homing_position     = list(self.homing_position)

        # Restore absolute coords
        self.gcode_move.absolute_coord      = self.absolute_coord
        self.gcode_move.absolute_extrude    = self.absolute_extrude
        self.gcode_move.extrude_factor      = self.extrude_factor
        self.gcode_move.speed               = self.speed
        self.gcode_move.speed_factor        = self.speed_factor

        # Restore the relative E position
        e_diff = self.gcode_move.last_position[3] - self.last_gcode_position[3]
        self.gcode_move.base_position[3] += e_diff
        self.gcode_move.last_position[:3] = self.last_gcode_position[:3]

        # Return to previous xyz
        self.gcode_move.move_with_transform(self.gcode_move.last_position, self._get_resume_speedz() )
        self.function.log_toolhead_pos("Resume final z, Error State: {}, Is Paused {}, Position_saved {}, in toolchange: {}, POS: ".format(self.error_state, self.function.is_paused(), self.position_saved, self.in_toolchange))

        self.current_state = State.IDLE
        self.position_saved = False


    def save_vars(self):
        """
        save_vars function saves lane variables to var file and prints with indents to
                  make it more readable for users
        """

        # Return early if prep is not done so that file is not overridden until prep is atleast done
        if not self.prep_done: return
        str = {}
        for UNIT in self.units.keys():
            cur_unit=self.units[UNIT]
            str[cur_unit.name]={}
            name=[]
            for NAME in cur_unit.lanes:
                cur_lane=self.lanes[NAME]
                str[cur_unit.name][cur_lane.name]=cur_lane.get_status()
                name.append(cur_lane.name)

        str["system"]={}
        str["system"]['current_load']= self.current
        str["system"]['num_units'] = len(self.units)
        str["system"]['num_lanes'] = len(self.lanes)
        str["system"]['num_extruders'] = len(self.tools)
        str["system"]["extruders"]={}
        str["system"]["bypass"] = {"enabled": self._get_bypass_state() }

        for extrude in self.tools.keys():
            cur_extruder = self.tools[extrude]
            str["system"]["extruders"][cur_extruder.name]={}
            str["system"]["extruders"][cur_extruder.name]['lane_loaded'] = cur_extruder.lane_loaded

        with open(self.VarFile+ '.unit', 'w') as f:
            f.write(json.dumps(str, indent=4))

    # HUB COMMANDS
    cmd_HUB_LOAD_help = "Load lane into hub"
    def cmd_HUB_LOAD(self, gcmd):
        """
        This function handles the loading of a specified lane into the hub. It performs
        several checks and movements to ensure the lane is properly loaded.

        Usage
        -----
        `HUB_LOAD LANE=<lane>`

        Example
        -----
        ```
        HUB_LOAD LANE=lane1
        ```
        """

        if self.function.is_printing():
            self.error.AFC_error("Cannot load lane to hub while printer is printing", pause=False)
            return

        lane = gcmd.get('LANE', None)
        if lane not in self.lanes:
            self.logger.info('{} Unknown'.format(lane))
            return
        cur_lane = self.lanes[lane]
        cur_hub = cur_lane.hub_obj
        if not cur_lane.prep_state: return
        cur_lane.status = AFCLaneState.HUB_LOADING
        if not cur_lane.load_state:
            cur_lane.do_enable(True)
            while not cur_lane.load_state:
                cur_lane.move_advanced( cur_hub.move_dis, SpeedMode.SHORT)
        if not cur_lane.loaded_to_hub:
            cur_lane.move_advanced(cur_lane.dist_hub, SpeedMode.HUB, assist_active = AssistActive.DYNAMIC)
        while not cur_hub.state:
            cur_lane.move_advanced(cur_hub.move_dis, SpeedMode.SHORT)
        while cur_hub.state:
            cur_lane.move_advanced(cur_hub.move_dis * -1, SpeedMode.SHORT)
        cur_lane.status = AFCLaneState.NONE
        cur_lane.do_enable(False)
        cur_lane.loaded_to_hub = True
        self.save_vars()
        cur_lane.unit_obj.return_to_home()
        # Put CAM back to lane if its loaded to toolhead
        self.function.select_loaded_lane()

    cmd_LANE_UNLOAD_help = "Unload lane from extruder"
    def cmd_LANE_UNLOAD(self, gcmd):
        """
        This function handles the unloading of a specified lane from the extruder. It performs
        several checks and movements to ensure the lane is properly unloaded.

        Usage
        -----
        `LANE_UNLOAD LANE=<lane>`

        Example
        -----
        ```
        LANE_UNLOAD LANE=lane1
        ```

        """
        if self.function.is_printing():
            self.error.AFC_error("Cannot eject lane while printer is printing", pause=False)
            return

        lane = gcmd.get('LANE', None)
        if lane not in self.lanes:
            self.logger.info('{} Unknown'.format(lane))
            return
        cur_lane = self.lanes[lane]
        self.LANE_UNLOAD( cur_lane )

    def LANE_UNLOAD(self, cur_lane):
        cur_hub = cur_lane.hub_obj

        self.current_state = State.EJECTING_LANE

        if cur_lane.name != self.current and cur_lane.hub != 'direct':
            # Setting status as ejecting so if filament is removed and de-activates the prep sensor while
            # extruder motors are still running it does not trigger infinite spool or pause logic
            # once user removes filament lanes status will go to None
            cur_lane.status = AFCLaneState.EJECTING
            self.save_vars()
            cur_lane.do_enable(True)
            if cur_lane.loaded_to_hub:
                cur_lane.move_advanced(cur_lane.dist_hub * -1, SpeedMode.HUB, assist_active = AssistActive.DYNAMIC)
            cur_lane.loaded_to_hub = False
            while cur_lane.load_state:
                cur_lane.move_advanced(cur_hub.move_dis * -1, SpeedMode.SHORT, assist_active = AssistActive.YES)
            cur_lane.move_advanced(cur_hub.move_dis * -5, SpeedMode.SHORT)
            cur_lane.do_enable(False)
            cur_lane.status = AFCLaneState.NONE
            cur_lane.unit_obj.return_to_home()
            # Put CAM back to lane if its loaded to toolhead
            self.function.select_loaded_lane()
            self.save_vars()

            # Removing spool from vars since it was ejected
            self.spool.set_spoolID(cur_lane, "")
            self.logger.info("LANE {} eject done".format(cur_lane.name))
            self.function.afc_led(cur_lane.led_not_ready, cur_lane.led_index)

        elif cur_lane.name == self.current:
            self.logger.info("LANE {} is loaded in toolhead, can't unload.".format(cur_lane.name))

        elif cur_lane.hub == 'direct':
            self.logger.info("LANE {} is a direct lane must be tool unloaded.".format(cur_lane.name))

        self.current_state = State.IDLE

    cmd_TOOL_LOAD_help = "Load lane into tool"
    def cmd_TOOL_LOAD(self, gcmd):
        """
        This function handles the loading of a specified lane into the tool. It retrieves
        the lane specified by the 'LANE' parameter and calls the TOOL_LOAD method to perform
        the loading process.

        Optionally setting PURGE_LENGTH parameter to pass a value into poop macro.

        Usage
        -----
        `TOOL_LOAD LANE=<lane> PURGE_LENGTH=<purge_length>(optional value)`

        Example
        -----
        ```
        TOOL_LOAD LANE=lane1 PURGE_LENGTH=80
        ```
        """
        self.afcDeltaTime.set_start_time()
        lane = gcmd.get('LANE', None)
        if lane not in self.lanes:
            self.logger.info('{} Unknown'.format(lane))
            return

        if self.current is not None:
            self.error.AFC_error("Cannot load {}, {} currently loaded".format(lane, self.current), pause=self.function.in_print())
            return

        purge_length = gcmd.get('PURGE_LENGTH', None)
        cur_lane = self.lanes[lane]
        self.TOOL_LOAD(cur_lane, purge_length)

    def TOOL_LOAD(self, cur_lane, purge_length=None):
        """
        This function handles the loading of a specified lane into the tool. It performs
        several checks and movements to ensure the lane is properly loaded.

        :param cur_lane: The lane object to be loaded into the tool.
        :param purge_length: Amount of filament to poop (optional).

        :return bool: True if load was successful, False if an error occurred.
        """
        if not self.function.is_homed():
            self.error.AFC_error("Please home printer before doing a tool load", False)
            return False

        if cur_lane is None:
            self.error.AFC_error("No lane provided to load, not loading any lane.", pause=self.function.in_print())
            # Exit early if no lane is provided.
            return False

        # Check if the bypass filament sensor is triggered; abort loading if filament is already present.
        if self._check_bypass(): return False

        self.logger.info("Loading {}".format(cur_lane.name))

        # Verify that printer is in absolute mode
        self.function.check_absolute_mode("TOOL_LOAD")

        # Lookup extruder and hub objects associated with the lane.
        cur_hub = cur_lane.hub_obj

        cur_extruder = cur_lane.extruder_obj
        self.current_state = State.LOADING
        self.current_loading = cur_lane.name

        # Set the lane status to 'loading' and activate the loading LED.
        cur_lane.status = AFCLaneState.TOOL_LOADING
        self.save_vars()
        self.function.afc_led(cur_lane.led_loading, cur_lane.led_index)

        # Check if the lane is in a state ready to load and hub is clear.
        if (cur_lane.load_state and not cur_hub.state) or cur_lane.hub == 'direct':

            if self._check_extruder_temp(cur_lane):
                self.afcDeltaTime.log_with_time("Done heating toolhead")

            # Enable the lane for filament movement.
            cur_lane.do_enable(True)

            # Move filament to the hub if it's not already loaded there.
            if not cur_lane.loaded_to_hub or cur_lane.hub == 'direct':
                cur_lane.move_advanced(cur_lane.dist_hub, SpeedMode.HUB, assist_active = AssistActive.DYNAMIC)
                self.afcDeltaTime.log_with_time("Loaded to hub")

            cur_lane.loaded_to_hub = True
            hub_attempts = 0

            # Ensure filament moves past the hub.
            while not cur_hub.state and cur_lane.hub != 'direct':
                if hub_attempts == 0:
                    cur_lane.move_advanced(cur_hub.move_dis, SpeedMode.SHORT)
                else:
                    cur_lane.move_advanced(cur_lane.short_move_dis, SpeedMode.SHORT)
                hub_attempts += 1
                if hub_attempts > 20:
                    message = 'filament did not trigger hub sensor, CHECK FILAMENT PATH\n||=====||==>--||-----||\nTRG   LOAD   HUB   TOOL.'
                    if self.function.in_print():
                        message += '\nOnce issue is resolved please manually load {} with {} macro and click resume to continue printing.'.format(cur_lane.name, cur_lane.map)
                        message += '\nIf you have to retract filament back, use LANE_MOVE macro for {}.'.format(cur_lane.name)
                    self.error.handle_lane_failure(cur_lane, message)
                    return False

            self.afcDeltaTime.log_with_time("Filament loaded to hub")

            # Move filament towards the toolhead.
            if cur_lane.hub != 'direct':
                cur_lane.move_advanced(cur_hub.afc_bowden_length, SpeedMode.LONG, assist_active = AssistActive.YES)

            # Ensure filament reaches the toolhead.
            tool_attempts = 0
            if cur_extruder.tool_start:
                while not cur_lane.get_toolhead_pre_sensor_state():
                    tool_attempts += 1
                    cur_lane.move(cur_lane.short_move_dis, cur_extruder.tool_load_speed, cur_lane.long_moves_accel)
                    if tool_attempts > int(self.tool_homing_distance/cur_lane.short_move_dis):
                        message = 'filament failed to trigger pre extruder gear toolhead sensor, CHECK FILAMENT PATH\n||=====||====||==>--||\nTRG   LOAD   HUB   TOOL'
                        message += '\nTo resolve set lane loaded with `SET_LANE_LOADED LANE={}` macro.'.format(cur_lane.name)
                        message += '\nManually move filament with LANE_MOVE macro for {} until filament is right before toolhead extruder gears,'.format(cur_lane.name)
                        message += '\n then load into extruder gears with extrude button in your gui of choice until the color fully changes'
                        if self.function.in_print():
                            message += '\nOnce filament is fully loaded click resume to continue printing'
                        self.error.handle_lane_failure(cur_lane, message)
                        return False

            self.afcDeltaTime.log_with_time("Filament loaded to pre-sensor")

            # Synchronize lane's extruder stepper and finalize tool loading.
            cur_lane.status = AFCLaneState.TOOL_LOADED
            self.save_vars()
            cur_lane.sync_to_extruder()

            if cur_extruder.tool_end:
                pos = self.toolhead.get_position()
                while not cur_extruder.tool_end_state:
                    tool_attempts += 1
                    pos[3] += cur_lane.short_move_dis
                    self.toolhead.manual_move(pos, cur_extruder.tool_load_speed)
                    self.toolhead.wait_moves()
                    if tool_attempts > 20:
                        message = 'filament failed to trigger post extruder gear toolhead sensor, CHECK FILAMENT PATH\n||=====||====||==>--||\nTRG   LOAD   HUB   TOOL'
                        message += '\nTo resolve set lane loaded with `SET_LANE_LOADED LANE={}` macro.'.format(cur_lane.name)
                        message += '\nAlso might be a good idea to verify that post extruder gear toolhead sensor is working.'
                        if self.function.in_print():
                            message += '\nOnce issue is resolved click resume to continue printing'
                        self.error.handle_lane_failure(cur_lane, message)
                        return False

                self.afcDeltaTime.log_with_time("Filament loaded to post-sensor")

            # Adjust tool position for loading.
            pos = self.toolhead.get_position()
            pos[3] += cur_extruder.tool_stn
            self.toolhead.manual_move(pos, cur_extruder.tool_load_speed)
            self.toolhead.wait_moves()

            self.afcDeltaTime.log_with_time("Filament loaded to nozzle")

            # Check if ramming is enabled, if it is go through ram load sequence.
            # Lane will load until Advance sensor is True
            # After the tool_stn distance the lane will retract off the sensor to confirm load and reset buffer
            if cur_extruder.tool_start == "buffer":
                cur_lane.unsync_to_extruder()
                load_checks = 0
                while cur_lane.get_toolhead_pre_sensor_state():
                    cur_lane.move_advanced(cur_lane.short_move_dis * -1, SpeedMode.SHORT)
                    load_checks += 1
                    self.reactor.pause(self.reactor.monotonic() + 0.1)
                    if load_checks > self.tool_max_load_checks:
                        msg = ''
                        msg += "Buffer did not become compressed after {} short moves.\n".format(self.tool_max_load_checks)
                        msg += "Tool may not be loaded"
                        self.logger.info("<span class=warning--text>{}</span>".format(msg))
                        break
                cur_lane.sync_to_extruder()
            # Update tool and lane status.
            cur_lane.set_loaded()
            cur_lane.enable_buffer()

            # Activate the tool-loaded LED and handle filament operations if enabled.
            self.function.afc_led(cur_lane.led_tool_loaded, cur_lane.led_index)
            if self.poop:
                if purge_length is not None:
                    self.gcode.run_script_from_command("%s %s=%s" % (self.poop_cmd, 'PURGE_LENGTH', purge_length))

                else:
                    self.gcode.run_script_from_command(self.poop_cmd)

                self.afcDeltaTime.log_with_time("TOOL_LOAD: After poop")
                self.function.log_toolhead_pos()

                if self.wipe:
                    self.gcode.run_script_from_command(self.wipe_cmd)
                    self.afcDeltaTime.log_with_time("TOOL_LOAD: After first wipe")
                    self.function.log_toolhead_pos()

            if self.kick:
                self.gcode.run_script_from_command(self.kick_cmd)
                self.afcDeltaTime.log_with_time("TOOL_LOAD: After kick")
                self.function.log_toolhead_pos()

            if self.wipe:
                self.gcode.run_script_from_command(self.wipe_cmd)
                self.afcDeltaTime.log_with_time("TOOL_LOAD: After second wipe")
                self.function.log_toolhead_pos()

            # Update lane and extruder state for tracking.
            cur_extruder.lane_loaded = cur_lane.name
            self.spool.set_active_spool(cur_lane.spool_id)
            self.function.afc_led(cur_lane.led_tool_loaded, cur_lane.led_index)
            self.save_vars()
            self.current_state = State.IDLE
            self.afcDeltaTime.log_major_delta("{} is now loaded in toolhead".format(cur_lane.name), False)

        else:
            # Handle errors if the hub is not clear or the lane is not ready for loading.
            if cur_hub.state:
                message = 'Hub not clear when trying to load.\nPlease check that hub does not contain broken filament and is clear'
                if self.function.in_print():
                    message += '\nOnce issue is resolved please manually load {} with {} macro and click resume to continue printing.'.format(cur_lane.name, cur_lane.map)
                self.error.handle_lane_failure(cur_lane, message)
                return False
            if not cur_lane.load_state:
                message = 'Current lane not loaded, LOAD TRIGGER NOT TRIGGERED\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL'
                message += '\nPlease load lane before continuing.'
                if self.function.in_print():
                    message += '\nOnce issue is resolved please manually load {} with {} macro and click resume to continue printing.'.format(cur_lane.name, cur_lane.map)
                self.error.handle_lane_failure(cur_lane, message)
                return False
        return True

    cmd_TOOL_UNLOAD_help = "Unload from tool head"
    def cmd_TOOL_UNLOAD(self, gcmd):
        """
        This function handles the unloading of a specified lane from the tool head. It retrieves
        the lane specified by the 'LANE' parameter or uses the currently loaded lane if no parameter
        is provided, and calls the TOOL_UNLOAD method to perform the unloading process.

        Usage
        -----
        `TOOL_UNLOAD LANE=<lane>`

        Example
        -----
        ```
        TOOL_UNLOAD LANE=lane1
        ```
        """
        self.afcDeltaTime.set_start_time()
        # Check if the bypass filament sensor detects filament; if so unload filament and abort the tool load.
        if self._check_bypass(unload=True): return False

        lane = gcmd.get('LANE', self.current)
        if lane is None:
            return
        if lane not in self.lanes:
            self.logger.info('{} Unknown'.format(lane))
            return
        cur_lane = self.lanes[lane]
        self.TOOL_UNLOAD(cur_lane)

        # User manually unloaded spool from toolhead, remove spool from active status
        self.spool.set_active_spool(None)

    def TOOL_UNLOAD(self, cur_lane):
        """
        This function handles the unloading of a specified lane from the tool. It performs
        several checks and movements to ensure the lane is properly unloaded.

        :param cur_lane: The lane object to be unloaded from the tool.

        :return bool: True if unloading was successful, False if an error occurred.
        """
        # Check if the bypass filament sensor detects filament; if so unload filament and abort the tool load.
        if self._check_bypass(unload=True): return False

        if not self.function.is_homed():
            self.error.AFC_error("Please home printer before doing a tool unload", False)
            return False

        if cur_lane is None:
            # If no lane is provided, exit the function early with a failure.
            self.error.AFC_error("No lane is currently loaded, nothing to unload", pause=self.function.in_print())
            return False

        self.current_state  = State.UNLOADING
        self.current_loading = cur_lane.name
        self.logger.info("Unloading {}".format(cur_lane.name))
        cur_lane.status = AFCLaneState.TOOL_UNLOADING
        self.save_vars()

        # Verify that printer is in absolute mode
        self.function.check_absolute_mode("TOOL_UNLOAD")

        # Lookup current extruder and hub objects using the lane's information.
        cur_hub = cur_lane.hub_obj
        cur_extruder = cur_lane.extruder_obj

        # Prepare the extruder and heater for unloading.
        if self._check_extruder_temp(cur_lane):
            self.afcDeltaTime.log_with_time("Done heating toolhead")

        # Quick pull to prevent oozing.
        pos = self.toolhead.get_position()
        pos[3] -= 2
        self.toolhead.manual_move(pos, cur_extruder.tool_unload_speed)
        self.toolhead.wait_moves()

        self.function.log_toolhead_pos("TOOL_UNLOAD quick pull: ")

        # Perform Z-hop to avoid collisions during unloading.
        pos[2] += self.z_hop
        self._move_z_pos(pos[2])
        self.toolhead.wait_moves()

        # Disable the buffer if it's active.
        cur_lane.disable_buffer()

        # Activate LED indicator for unloading.
        self.function.afc_led(cur_lane.led_unloading, cur_lane.led_index)

        if cur_lane.extruder_stepper.motion_queue != cur_lane.extruder_name:
            # Synchronize the extruder stepper with the lane.
            cur_lane.sync_to_extruder()

        # Enable the lane for unloading operations.
        cur_lane.do_enable(True)

        # Perform filament cutting and parking if specified.
        if self.tool_cut:
            self.gcode.run_script_from_command(self.tool_cut_cmd)
            self.afcDeltaTime.log_with_time("TOOL_UNLOAD: After cut")
            self.function.log_toolhead_pos()

            if self.park:
                self.gcode.run_script_from_command(self.park_cmd)
                self.afcDeltaTime.log_with_time("TOOL_UNLOAD: After park")
                self.function.log_toolhead_pos()

        # Form filament tip if necessary.
        if self.form_tip:
            if self.park:
                self.gcode.run_script_from_command(self.park_cmd)
                self.afcDeltaTime.log_with_time("TOOL_UNLOAD: After form tip park")
                self.function.log_toolhead_pos()

            if self.form_tip_cmd == "AFC":
                self.tip = self.printer.lookup_object('AFC_form_tip')
                self.tip.tip_form()
                self.afcDeltaTime.log_with_time("TOOL_UNLOAD: After afc form tip")
                self.function.log_toolhead_pos()

            else:
                self.gcode.run_script_from_command(self.form_tip_cmd)
                self.afcDeltaTime.log_with_time("TOOL_UNLOAD: After custom form tip")
                self.function.log_toolhead_pos()

        # Attempt to unload the filament from the extruder, retrying if needed.
        num_tries = 0
        if cur_extruder.tool_start == "buffer":
            # if ramming is enabled, AFC will retract to collapse buffer before unloading
            cur_lane.unsync_to_extruder()
            while not cur_lane.get_trailing():
                # attempt to return buffer to trailng pin
                cur_lane.move_advanced(cur_lane.short_move_dis * -1, SpeedMode.SHORT)
                num_tries += 1
                self.reactor.pause(self.reactor.monotonic() + 0.1)
                if num_tries > self.tool_max_unload_attempts:
                    msg = ''
                    msg += "Buffer did not become compressed after {} short moves.\n".format(self.tool_max_unload_attempts)
                    msg += "Increasing 'tool_max_unload_attempts' may improve loading reliability"
                    self.logger.info("<span class=warning--text>{}</span>".format(msg))
                    break
            cur_lane.sync_to_extruder(False)
            pos = self.toolhead.get_position()
            pos[3] -= cur_extruder.tool_stn_unload
            with cur_lane.assist_move(cur_extruder.tool_unload_speed, True, cur_lane.assisted_unload):
                self.toolhead.manual_move(pos, cur_extruder.tool_unload_speed)
                self.toolhead.wait_moves()
        else:
            while cur_lane.get_toolhead_pre_sensor_state() or cur_extruder.tool_end_state:
                num_tries += 1
                if num_tries > self.tool_max_unload_attempts:
                    # Handle failure if the filament cannot be unloaded.
                    message = 'Failed to unload filament from toolhead. Filament stuck in toolhead.'
                    if self.function.in_print():
                        message += "\nRetract filament fully with retract button in gui of choice to remove from extruder gears if needed,"
                        message += "\n  and then use LANE_MOVE to fully retract behind hub so its not triggered anymore."
                        message += "\nThen Manually run UNSET_LANE_LOADED to let AFC know nothing is loaded into toolhead"
                        # Check to make sure next_lane_loaded is not None before adding instructions on how to manually load next lane
                        if self.next_lane_load is not None:
                            message += "\nThen manually load {} with {} macro".format(self.next_lane_load, self.lanes[self.next_lane_load].map)
                            message += "\nOnce lane is loaded click resume to continue printing"
                    self.error.handle_lane_failure(cur_lane, message)
                    return False
                cur_lane.sync_to_extruder()
                pos = self.toolhead.get_position()
                pos[3] -= cur_extruder.tool_stn_unload
                with cur_lane.assist_move(cur_extruder.tool_unload_speed, True, cur_lane.assisted_unload):
                    self.toolhead.manual_move(pos, cur_extruder.tool_unload_speed)
                    self.toolhead.wait_moves()

        self.afcDeltaTime.log_with_time("Unloaded from toolhead")

        # Move filament past the sensor after the extruder, if applicable.
        if cur_extruder.tool_sensor_after_extruder > 0:
            pos = self.toolhead.get_position()
            pos[3] -= cur_extruder.tool_sensor_after_extruder
            with cur_lane.assist_move(cur_extruder.tool_unload_speed, True, cur_lane.assisted_unload):
                self.toolhead.manual_move(pos, cur_extruder.tool_unload_speed)
                self.toolhead.wait_moves()

            self.afcDeltaTime.log_with_time("Tool sensor after extruder move done")

        self.save_vars()
        # Synchronize and move filament out of the hub.
        cur_lane.unsync_to_extruder()
        if cur_lane.hub != 'direct':
            cur_lane.move_advanced(cur_hub.afc_unload_bowden_length * -1, SpeedMode.LONG, assist_active = AssistActive.YES)
        else:
            cur_lane.move_advanced(cur_lane.dist_hub * -1, SpeedMode.HUB, assist_active = AssistActive.DYNAMIC)

        self.afcDeltaTime.log_with_time("Long retract done")

        # Clear toolhead's loaded state for easier error handling later.
        cur_lane.set_unloaded()

        self.save_vars()

        # Ensure filament is fully cleared from the hub.
        num_tries = 0
        while cur_hub.state:
            cur_lane.move_advanced(cur_lane.short_move_dis * -1, SpeedMode.SHORT, assist_active = AssistActive.YES)
            num_tries += 1
            if num_tries > (cur_hub.afc_unload_bowden_length / cur_lane.short_move_dis):
                # Handle failure if the filament doesn't clear the hub.
                message = 'Hub is not clearing, filament may be stuck in hub'
                message += '\nPlease check to make sure filament has not broken off and caused the sensor to stay stuck'
                message += '\nIf you have to retract filament back, use LANE_MOVE macro for {}.'.format(cur_lane.name)
                if self.function.in_print():
                    # Check to make sure next_lane_loaded is not None before adding instructions on how to manually load next lane
                    if self.next_lane_load is not None:
                        message += "\nOnce hub is clear, manually load {} with {} macro".format(self.next_lane_load, self.lanes[self.next_lane_load].map)
                        message += "\nOnce lane is loaded click resume to continue printing"

                self.error.handle_lane_failure(cur_lane, message)
                return False

        self.afcDeltaTime.log_with_time("Hub cleared")

        #Move to make sure hub path is clear based on the move_clear_dis var
        if cur_lane.hub != 'direct':
            cur_lane.move_advanced(cur_hub.hub_clear_move_dis * -1, SpeedMode.SHORT, assist_active = AssistActive.YES)

            # Cut filament at the hub, if configured.
            if cur_hub.cut:
                if cur_hub.cut_cmd == 'AFC':
                    cur_hub.hub_cut(cur_lane)
                else:
                    self.gcode.run_script_from_command(cur_hub.cut_cmd)

                # Confirm the hub is clear after the cut.
                while cur_hub.state:
                    cur_lane.move_advanced(cur_lane.short_move_dis * -1, SpeedMode.SHORT, assist_active = AssistActive.YES)
                    num_tries += 1
                    # TODO: Figure out max number of tries
                    if num_tries > (cur_hub.afc_unload_bowden_length / cur_lane.short_move_dis):
                        message = 'HUB NOT CLEARING after hub cut\n'
                        self.error.handle_lane_failure(cur_lane, message)
                        return False

                self.afcDeltaTime.log_with_time("Hub cut done")

        # Finalize unloading and reset lane state.
        cur_lane.loaded_to_hub = True
        self.function.afc_led(cur_lane.led_ready, cur_lane.led_index)
        cur_lane.status = AFCLaneState.NONE

        if cur_lane.hub == 'direct':
            while cur_lane.load_state:
                cur_lane.move_advanced(cur_lane.short_move_dis * -1, SpeedMode.SHORT, assist_active = AssistActive.YES)
            cur_lane.move_advanced(cur_lane.short_move_dis * -5, SpeedMode.SHORT)

        cur_lane.do_enable(False)
        cur_lane.unit_obj.return_to_home()

        self.save_vars()
        self.afcDeltaTime.log_major_delta("Lane {} unload done".format(cur_lane.name))
        self.current_state = State.IDLE
        return True

    cmd_CHANGE_TOOL_help = "change filaments in tool head"
    def cmd_CHANGE_TOOL(self, gcmd):
        """
        This function handles the tool change process. It retrieves the lane specified by the 'LANE' parameter,
        checks the filament sensor, saves the current position, and performs the tool change by unloading the
        current lane and loading the new lane.

        Optionally setting PURGE_LENGTH parameter to pass a value into poop macro.

        Usage
        -----
        `CHANGE_TOOL LANE=<lane> PURGE_LENGTH=<purge_length>(optional value)`

        Example
        ------
        ```
        CHANGE_TOOL LANE=lane1 PURGE_LENGTH=100
        ```
        """
        self.afcDeltaTime.set_start_time()
        # Check if the bypass filament sensor detects filament; if so, abort the tool change.
        if self._check_bypass(unload=False): return

        if not self.function.is_homed():
            self.error.AFC_error("Please home printer before doing a tool change", False)
            return

        purge_length = gcmd.get('PURGE_LENGTH', None)

        # Klipper macros that start with a single letter (ie T0) parse the parameter values with the equals sign
        # for some sort of backwards compatibility, so for example: T0 PURGE_LENGTH=200, the purge_length would be
        # equal to "=200". So run this check to remove it:
        if purge_length is not None:
            if purge_length.startswith('='):
                purge_length = purge_length[1:]

        command_line = gcmd.get_commandline()
        self.logger.debug("CHANGE_TOOL: cmd-{}".format(command_line))

        # Remove everything after ; since it could contain strings like CHANGE in a comment and should be ignored
        command = re.sub( ';.*', '', command_line)
        command = command.split(' ')[0].upper()
        tmp = gcmd.get_commandline()
        cmd = tmp.upper()
        Tcmd = ''
        if 'CHANGE' in command:
            lane = gcmd.get('LANE', None)
            if lane is not None:
                for key in self.tool_cmds.keys():
                    if self.tool_cmds[key].upper() == lane.upper():
                        Tcmd = key
                        break
        else:
            Tcmd = command

        if Tcmd == '':
            self.error.AFC_error("I did not understand the change -- " + cmd, pause=self.function.in_print())
            return

        self.CHANGE_TOOL(self.lanes[self.tool_cmds[Tcmd]], purge_length)

    def CHANGE_TOOL(self, cur_lane, purge_length=None, restore_pos=True):
        # Check if the bypass filament sensor detects filament; if so, abort the tool change.
        if self._check_bypass(unload=False): return

        self.next_lane_load = cur_lane.name

        # If the requested lane is not the current lane, proceed with the tool change.
        if cur_lane.name != self.current:
            # Save the current toolhead position to allow restoration after the tool change.
            self.save_pos()
            # Set the in_toolchange flag to prevent overwriting the saved position during potential failures.
            self.in_toolchange = True

            # Check if the lane has completed the preparation process required for tool changes.
            if cur_lane._afc_prep_done:
                # Log the tool change operation for debugging or informational purposes.
                self.logger.info("Tool Change - {} -> {}".format(self.current, cur_lane.name))
                if not self.error_state and self.number_of_toolchanges != 0 and self.current_toolchange != self.number_of_toolchanges:
                    self.current_toolchange += 1
                    self.logger.raw("//      Change {} out of {}".format(self.current_toolchange, self.number_of_toolchanges))

                # If a current lane is loaded, unload it first.
                if self.current is not None:
                    c_lane = self.current
                    if c_lane not in self.lanes:
                        self.error.AFC_error('{} Unknown'.format(c_lane))
                        return
                    if not self.TOOL_UNLOAD(self.lanes[c_lane]):
                        # Abort if the unloading process fails.
                        msg = (' UNLOAD error NOT CLEARED')
                        self.error.fix(msg, self.lanes[c_lane])  #send to error handling
                        return

            # Load the new lane and restore the toolhead position if successful.
            if self.TOOL_LOAD(cur_lane, purge_length) and not self.error_state:
                self.afcDeltaTime.log_total_time("Total change time:")
                if restore_pos:
                    self.restore_pos()
                self.in_toolchange = False
                # Setting next lane load as none since toolchange was successful
                self.next_lane_load = None
        else:
            self.logger.info("{} already loaded".format(cur_lane.name))
            if not self.error_state and self.number_of_toolchanges != 0 and self.current_toolchange != self.number_of_toolchanges:
                self.current_toolchange += 1

        self.function.log_toolhead_pos("Final Change Tool: Error State: {}, Is Paused {}, Position_saved {}, in toolchange: {}, POS: ".format(
                self.error_state, self.function.is_paused(), self.position_saved, self.in_toolchange ))

    def _get_message(self):
        """
        Helper function to return a message from the error message queue
        : return Dictionary in {"message":"", "type":""} format
        """
        message = {"message":"", "type":""}
        try:
            message['message'], message["type"] = self.message_queue.pop(0)
        except IndexError:
            pass
        return message

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
        str['spoolman']                 = self.spoolman
        str['error_state']              = self.error_state
        str["bypass_state"]             = bool(self._get_bypass_state())
        str["quiet_mode"]               = bool(self._get_quiet_mode())
        str["position_saved"]           = self.position_saved

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
        str["message"] = self._get_message()
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
            str[unit.name]['system']['type']        = unit.type
            str[unit.name]['system']['hub_loaded'] = unit.hub_obj.state if unit.hub_obj is not None else None

        str["system"]                           = {}
        str["system"]['current_load']           = self.current
        str["system"]['num_units']              = len(self.units)
        str["system"]['num_lanes']              = numoflanes
        str["system"]['num_extruders']          = len(self.tools)
        str["system"]['spoolman']               = self.spoolman
        str["system"]["current_toolchange"]     = self.current_toolchange
        str["system"]["number_of_toolchanges"]  = self.number_of_toolchanges
        str["system"]["extruders"]              = {}
        str["system"]["hubs"]                   = {}
        str["system"]["buffers"]                = {}

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

        Usage
        -----
        `AFC_STATUS`

        Example
        -----
        ```
        AFC_STATUS
        ```
        """
        status_msg = ''

        for unit in self.units.values():
            # Find the maximum length of lane names to determine the column width
            max_lane_length = max(len(lane) for lane in unit.lanes.keys())

            status_msg += '<span class=info--text>{} Status</span>\n'.format(unit.name)

            # Create a dynamic format string that adjusts based on lane name length
            header_format = '{:<{}} | Prep | Load |\n'
            status_msg += header_format.format("LANE", max_lane_length)

            for cur_lane in unit.lanes.values():
                lane_msg = ''
                if self.current is not None:
                    if self.current == cur_lane.name:
                        if not cur_lane.get_toolhead_pre_sensor_state() or not cur_lane.hub_obj.state:
                            lane_msg += '<span class=warning--text>{:<{}} </span>'.format(cur_lane.name, max_lane_length)
                        else:
                            lane_msg += '<span class=success--text>{:<{}} </span>'.format(cur_lane.name, max_lane_length)
                    else:
                        lane_msg += '{:<{}} '.format(cur_lane.name, max_lane_length)
                else:
                    lane_msg += '{:<{}} '.format(cur_lane.name, max_lane_length)

                if cur_lane.prep_state:
                    lane_msg += '| <span class=success--text><--></span> |'
                else:
                    lane_msg += '|  <span class=error--text>xx</span>  |'
                if cur_lane.load_state:
                    lane_msg += ' <span class=success--text><--></span> |\n'
                else:
                    lane_msg += '  <span class=error--text>xx</span>  |\n'
                status_msg += lane_msg

            if cur_lane.hub_obj.state:
                status_msg += 'HUB: <span class=success--text><-></span>'
            else:
                status_msg += 'HUB: <span class=error--text>x</span>'

            extruder_msg = '  Tool: <span class=error--text>x</span>'
            if cur_lane.extruder_obj.tool_start != "buffer":
                if cur_lane.extruder_obj.tool_start_state:
                    extruder_msg = '  Tool: <span class=success--text><-></span>'
            else:
                if cur_lane.tool_loaded and cur_lane.extruder_obj.lane_loaded in self.units[unit]:
                    if cur_lane.get_toolhead_pre_sensor_state():
                        extruder_msg = '  Tool: <span class=success--text><-></span>'

            status_msg += extruder_msg
            if cur_lane.extruder_obj.tool_start == 'buffer':
                status_msg += '\n<span class=info--text>Ram sensor enabled</span>\n'

        self.logger.raw(status_msg)

    cmd_TURN_OFF_AFC_LED_help = "Turns off all LEDs for AFC_led configurations"
    def cmd_TURN_OFF_AFC_LED(self, gcmd: Any) -> None:
        """
        This macro handles turning off all LEDs for AFC_led configurations. Color for LEDs are saved if colors are changed while they are turned off.

        Usage
        -----
        `TURN_OFF_AFC_LED`

        Example
        -----
        ```
        TURN_OFF_AFC_LED
        ```
        """
        for led in self.led_obj.values():
            led.turn_off_leds()

    cmd_TURN_ON_AFC_LED_help = "Turns on all LEDs for AFC_led configurations and restores state"
    def cmd_TURN_ON_AFC_LED(self, gcmd):
        """
        This macro handles turning on all LEDs for AFC_led configurations. LEDs are restored to last previous state.

        Usage
        -----
        `TURN_ON_AFC_LED`

        Example
        -----
        ```
        TURN_ON_AFC_LED
        ```
        """
        for led in self.led_obj.values():
            led.turn_on_leds()
