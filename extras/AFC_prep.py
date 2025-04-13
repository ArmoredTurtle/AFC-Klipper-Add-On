# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import os
import json

class afcPrep:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.delay              = config.getfloat('delay_time', 0.1, minval=0.0)                # Time to delay when moving extruders and spoolers during PREP routine
        self.enable             = config.getboolean("enable", False)                            # Set True to disable PREP checks
        self.dis_unload_macro   = config.getboolean("disable_unload_filament_remapping", False) # Set to True to disable remapping UNLOAD_FILAMENT macro to TOOL_UNLOAD macro

        # Flag to set once resume rename as occurred for the first time
        self.rename_occurred = False
        # Value gets set to false once prep has been ran for the first time after restarting klipper
        self.assignTcmd = True

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')
        self.AFC.gcode.register_command('PREP', self.PREP, desc=None)
        self.logger = self.AFC.logger

    def _rename(self, base_name, rename_name, rename_macro, rename_help):
        """
        Helper function to get stock macros, rename to something and replace stock macro with AFC functions
        """
        # Renaming users Resume macro so that RESUME calls AFC_Resume function instead
        prev_cmd = self.AFC.gcode.register_command(base_name, None)
        if prev_cmd is not None:
            pdesc = "Renamed builtin of '%s'" % (base_name,)
            self.AFC.gcode.register_command(rename_name, prev_cmd, desc=pdesc)
        else:
            self.logger.debug("{}Existing command {} not found in gcode_macros{}".format("<span class=warning--text>", base_name, "</span>",))
        self.logger.debug("PREP-renaming macro {}".format(base_name))
        self.AFC.gcode.register_command(base_name, rename_macro, desc=rename_help)

    def _rename_macros(self):
        """
        Helper function to rename multiple macros and substitute with AFC macros.
        - Replaces stock RESUME macro and reassigns to AFC_RESUME function
        - Replaces stock UNLOAD macro and reassigns to TOOL_UNLOAD function. This can be disabled in AFC_prep config
        - Replaces stock/users PAUSE macro and reassigns to AFC_PAUSE function.
        """
        # Checking to see if rename has already been done, don't want to rename again if prep was already ran
        if not self.rename_occurred:
            self.rename_occurred = True
            self._rename( self.AFC.ERROR.BASE_RESUME_NAME, self.AFC.ERROR.AFC_RENAME_RESUME_NAME, self.AFC.ERROR.cmd_AFC_RESUME, self.AFC.ERROR.cmd_AFC_RESUME_help )
            self._rename( self.AFC.ERROR.BASE_PAUSE_NAME,  self.AFC.ERROR.AFC_RENAME_PAUSE_NAME,  self.AFC.ERROR.cmd_AFC_PAUSE,  self.AFC.ERROR.cmd_AFC_RESUME_help )

            # Check to see if the user does not want to rename UNLOAD_FILAMENT macro
            if not self.dis_unload_macro:
                self._rename( self.AFC.BASE_UNLOAD_FILAMENT,   self.AFC.RENAMED_UNLOAD_FILAMENT,      self.AFC.cmd_TOOL_UNLOAD,      self.AFC.cmd_TOOL_UNLOAD_help )

    def PREP(self, gcmd):
        while self.printer.state_message != 'Printer is ready':
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 1)
        self._rename_macros()
        self.AFC.print_version(console_only=True)

        ## load Unit stored variables
        units={}
        if os.path.exists(self.AFC.VarFile + '.unit') and os.stat(self.AFC.VarFile + '.unit').st_size > 0:
            units=json.load(open(self.AFC.VarFile + '.unit'))

        # check if Lane is suppose to be loaded in tool head from saved file
        for EXTRUDER in self.AFC.tools.keys():
            PrinterObject=self.AFC.tools[EXTRUDER]
            self.AFC.tools[PrinterObject.name]=PrinterObject
            if 'system' in units and "extruders" in units["system"]:
                # Check to see if lane_loaded is in dictionary and its its not an empty string
                if PrinterObject.name in units["system"]["extruders"] and \
                  'lane_loaded' in units["system"]["extruders"][PrinterObject.name] and \
                  units["system"]["extruders"][PrinterObject.name]['lane_loaded']:
                    PrinterObject.lane_loaded = units["system"]["extruders"][PrinterObject.name]['lane_loaded']
                    self.AFC.current = PrinterObject.lane_loaded

        for LANE in self.AFC.lanes.keys():
            CUR_LANE = self.AFC.lanes[LANE]
            CUR_LANE.unit_obj = self.AFC.units[CUR_LANE.unit]
            if CUR_LANE.name not in CUR_LANE.unit_obj.lanes: CUR_LANE.unit_obj.lanes.append(CUR_LANE.name)    #add lanes to units list
            # If units section exists in vars file add currently stored data to AFC.units array
            if CUR_LANE.unit in units:
                if CUR_LANE.name in units[CUR_LANE.unit]:
                    if 'spool_id' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.spool_id = units[CUR_LANE.unit][CUR_LANE.name]['spool_id']
                    if self.AFC.spoolman != None and CUR_LANE.spool_id:
                        self.AFC.SPOOL.set_spoolID(CUR_LANE, CUR_LANE.spool_id, save_vars=False)
                    else:
                        if 'material' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.material = units[CUR_LANE.unit][CUR_LANE.name]['material']
                        if 'color' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.color = units[CUR_LANE.unit][CUR_LANE.name]['color']
                        if 'weight' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.weight = units[CUR_LANE.unit][CUR_LANE.name]['weight']
                    if 'runout_lane' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.runout_lane = units[CUR_LANE.unit][CUR_LANE.name]['runout_lane']
                    if CUR_LANE.runout_lane == '': CUR_LANE.runout_lane='NONE'
                    if 'map' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.map = units[CUR_LANE.unit][CUR_LANE.name]['map']
                    if CUR_LANE.map != 'NONE':
                        self.AFC.tool_cmds[CUR_LANE.map] = CUR_LANE.name
                    # Check first for hub_loaded as this was the old name in software with version <= 1030
                    if 'hub_loaded' in units[CUR_LANE.unit][CUR_LANE.name]: LANE.loaded_to_hub = units[CUR_LANE.unit][CUR_LANE.name]['hub_loaded']
                    # Check for loaded_to_hub as this is how its being saved version > 1030
                    if 'loaded_to_hub' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.loaded_to_hub = units[CUR_LANE.unit][CUR_LANE.name]['loaded_to_hub']
                    if 'tool_loaded' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.tool_loaded = units[CUR_LANE.unit][CUR_LANE.name]['tool_loaded']
                    # Commenting out until there is better handling of this variable as it could cause someone to not be able to load their lane if klipper crashes
                    # if 'status' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.status = units[CUR_LANE.unit][CUR_LANE.name]['status']

        for UNIT in self.AFC.units.keys():
            try: CUR_UNIT = self.AFC.units[UNIT]
            except:
                error_string = 'Error: ' + UNIT + '  Unit not found in  config section.'
                self.AFC.ERROR.AFC_error(error_string, False)
                return
            self.logger.info(CUR_UNIT.type + ' ' + UNIT +' Prepping lanes')
            lanes_for_first_hub = []
            hub_name = ""
            LaneCheck = True
            for LANE in CUR_UNIT.lanes.values():
                # Used to print out warning message that multiple hubs are found
                if LANE.multi_hubs_found:
                    lanes_for_first_hub.append(LANE.name)
                    hub_name = LANE.hub_obj.fullname

                if not CUR_UNIT.system_Test(LANE, self.delay, self.assignTcmd, self.enable):
                    LaneCheck = False
            # Warn user if multiple hubs were found and hub was not assigned to unit/stepper
            if len(lanes_for_first_hub) != 0:
                self.logger.raw("<span class=warning--text>No hub defined in lanes or unit for {unit}. Defaulting to {hub}</span>".format(
                                            unit=" ".join(CUR_UNIT.full_name), hub=hub_name))

            if LaneCheck:
                self.logger.raw(CUR_UNIT.logo)
            else:
                self.logger.raw(CUR_UNIT.logo_error)
        try:
            if self.AFC._get_bypass_state():
                self.logger.info("Filament loaded in bypass, toolchanges deactivated")
        except:
            pass

        # look up what current lane should be an call select lane, this is more for units that
        # have selectors to make sure the selector is on the correct lane
        current_lane = self.AFC.FUNCTION.get_current_lane_obj()
        if current_lane is not None:
            current_lane.unit_obj.select_lane(current_lane)

        # Restore previous bypass state if virtual bypass is active
        if 'virtual' in self.AFC.bypass.name:
            if "system" in units and 'bypass' in units["system"]:
                self.AFC.bypass.sensor_enabled = units["system"]["bypass"]["enabled"]

        # Defaulting to no active spool, putting at end so endpoint has time to register
        if self.AFC.current is None:
            self.AFC.SPOOL.set_active_spool( None )
        # Setting value to False so the T commands don't try to get reassigned when users manually
        #   run PREP after it has already be ran once upon boot
        self.assignTcmd = False
        self.AFC.prep_done = True
        self.AFC.save_vars()

def load_config(config):
    return afcPrep(config)

