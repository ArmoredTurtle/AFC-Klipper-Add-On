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
        self.delay = config.getfloat('delay_time', 0.1, minval=0.0)                 # Time to delay when moving extruders and spoolers during PREP routine
        self.enable = config.getboolean("enable", False)                            # Set True to disable PREP checks

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

    def _rename_resume(self):
        """
            Helper function to check if renaming RESUME macro has occured and renames RESUME.
            Addes a new RESUME macro that points to AFC resume function
        """

        # Checking to see if rename has already been done, don't want to rename again if prep was already ran
        if not self.rename_occurred:
            self.rename_occurred = True
            # Renaming users Resume macro so that RESUME calls AFC_Resume function instead
            base_resume_name = "RESUME"
            prev_cmd = self.AFC.gcode.register_command(base_resume_name, None)
            if prev_cmd is not None:
                pdesc = "Renamed builtin of '%s'" % (base_resume_name,)
                self.AFC.gcode.register_command(self.AFC.ERROR.AFC_RENAME_RESUME_NAME, prev_cmd, desc=pdesc)
            else:
                self.AFC.gcode.respond_info("{}Existing command {} not found in gcode_macros{}".format("<span class=warning--text>", base_resume_name, "</span>",))
            self.AFC.gcode.register_command(base_resume_name, self.AFC.ERROR.cmd_AFC_RESUME, desc=self.AFC.ERROR.cmd_AFC_RESUME_help)

    def PREP(self, gcmd):
        while self.printer.state_message != 'Printer is ready':
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 1)
        self._rename_resume()
        self.AFC.print_version()

        ## load Unit variables
        units={}
        if os.path.exists(self.AFC.VarFile + '.unit') and os.stat(self.AFC.VarFile + '.unit').st_size > 0:
            units=json.load(open(self.AFC.VarFile + '.unit'))

        ## load Toolhead variables
        extruders={}
        if os.path.exists(self.AFC.VarFile + '.tool') and os.stat(self.AFC.VarFile + '.tool').st_size > 0:
            extruders=json.load(open(self.AFC.VarFile + '.tool'))

        # check if Lane is suppose to be loaded in tool head from saved file
        for EXTRUDER in self.AFC.tools.keys():
            PrinterObject=self.printer.lookup_object(EXTRUDER)
            self.AFC.tools[PrinterObject.name]=PrinterObject
            if PrinterObject.name in extruders:
                if 'lane_loaded' in extruders[PrinterObject.name]: PrinterObject.lane_loaded = extruders[PrinterObject.name]['lane_loaded']
            self.AFC.current = PrinterObject.lane_loaded

        for LANE in self.AFC.lanes.keys():
                CUR_LANE = self.AFC.lanes[LANE]
                CUR_LANE.unit_obj = self.AFC.units[CUR_LANE.unit]
                if CUR_LANE.name not in CUR_LANE.unit_obj.lanes: CUR_LANE.unit_obj.lanes.append(CUR_LANE.name)    #add lanes to units list
                # If units section exists in vars file add currently stored data to AFC.units array
                if CUR_LANE.unit in units:
                    if CUR_LANE.name in units[CUR_LANE.unit]:
                        if 'spool_id' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.spool_id = units[CUR_LANE.unit][CUR_LANE.name]['spool_id']
                        if self.AFC.spoolman_ip !=None and CUR_LANE.spool_id != None:
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
                        if 'status' in units[CUR_LANE.unit][CUR_LANE.name]: CUR_LANE.status = units[CUR_LANE.unit][CUR_LANE.name]['status']
        self.AFC.save_vars()
        if self.enable == False:
            self.AFC.gcode.respond_info('Prep Checks Disabled')
            return
        else:
            for UNIT in self.AFC.units.keys():
                try: CUR_UNIT = self.AFC.units[UNIT]
                except:
                    error_string = 'Error: ' + UNIT + '  Unit not found in  config section.'
                    self.AFC.ERROR.AFC_error(error_string, False)
                    return
                self.AFC.gcode.respond_info(CUR_UNIT.type + ' ' + UNIT +' Prepping lanes')
                LaneCheck = True
                for LANE in CUR_UNIT.lanes:
                    if not CUR_UNIT.system_Test(LANE, self.delay, self.assignTcmd):
                        LaneCheck = False
                if LaneCheck:
                    self.AFC.gcode.respond_raw(CUR_UNIT.logo)
                else:
                    self.AFC.gcode.respond_raw(CUR_UNIT.logo_error)
        try:
            bypass = self.printer.lookup_object('filament_switch_sensor bypass').runout_helper
            if bypass.filament_present == True:
              self.AFC.gcode.respond_info("Filament loaded in bypass, not doing toolchange")
        except: bypass = None

        # Defaulting to no active spool, putting at end so endpoint has time to register
        if self.AFC.current is None:
            self.AFC.SPOOL.set_active_spool( None )
        # Setting value to False so the T commands do try to get reassigned when users manually
        #   run PREP after it has already be ran once upon boot
        self.assignTcmd = False

def load_config(config):
    return afcPrep(config)

