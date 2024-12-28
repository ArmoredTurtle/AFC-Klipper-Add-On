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
        units={}
        ## load Unit variables
        if os.path.exists(self.AFC.VarFile + '.unit') and os.stat(self.AFC.VarFile + '.unit').st_size > 0:
            units=json.load(open(self.AFC.VarFile + '.unit'))
        ## load Toolhead variables
        if os.path.exists(self.AFC.VarFile + '.tool') and os.stat(self.AFC.VarFile + '.tool').st_size > 0:
            extruders=json.load(open(self.AFC.VarFile + '.tool'))
        else:
            extruders={}

        self.AFC.tool_cmds={}
        for PO in self.printer.objects:
            if 'AFC_extruder' in PO:
                extruder=self.printer.lookup_object(PO)
                self.AFC.extruders[extruder.name]=extruder
                if extruder.name in extruders:
                    if 'lane_loaded' in extruders[extruder.name]: extruder.lane_loaded = extruders[extruder.name]['lane_loaded']
                self.AFC.current = extruder.lane_loaded
        self.buffer = {}
        for PO in self.printer.objects:
            if 'AFC_buffer' in PO:
                tmpBUFFER = self.printer.lookup_object(PO)
                self.buffer[tmpBUFFER.name] = tmpBUFFER
        hub = []
        for PO in self.printer.objects:
            if 'AFC_hub' in PO:
                hub.append(PO.split()[-1])

        for PO in self.printer.objects:
            if 'AFC_stepper' in PO and 'tmc' not in PO:
                LANE=self.printer.lookup_object(PO)
                UNIT=self.printer.lookup_object(self.AFC.units[LANE.unit] + ' ' + LANE.unit)
                if LANE.name not in UNIT.lanes: UNIT.lanes.append(LANE.name)    #add lanes to units list
                self.AFC.stepper[LANE.name]=LANE                                #add list of all lanes
                if LANE.hub_name == None:
                    LANE.hub_name_ = hub[0]
                if LANE.buffer_name == None:
                    LANE.buffer_name = list(self.buffer.keys())[0]
                # If units section exists in vars file add currently stored data to AFC.units array
                if LANE.unit in units:
                    if LANE.name in units[LANE.unit]:
                        if 'spool_id' in units[LANE.unit][LANE.name]: LANE.spool_id = units[LANE.unit][LANE.name]['spool_id']
                        if self.AFC.spoolman_ip !=None and LANE.spool_id != None:
                            self.AFC.SPOOL.set_spoolID(LANE, LANE.spool_id, save_vars=False)
                        else:
                            if 'material' in units[LANE.unit][LANE.name]: LANE.material = units[LANE.unit][LANE.name]['material']
                            if 'color' in units[LANE.unit][LANE.name]: LANE.color = units[LANE.unit][LANE.name]['color']
                            if 'weight' in units[LANE.unit][LANE.name]: LANE.weight = units[LANE.unit][LANE.name]['weight']
                        if 'runout_lane' in units[LANE.unit][LANE.name]: LANE.runout_lane = units[LANE.unit][LANE.name]['runout_lane']
                        if LANE.runout_lane == '': LANE.runout_lane='NONE'
                        if 'map' in units[LANE.unit][LANE.name]: LANE.map = units[LANE.unit][LANE.name]['map']
                        if LANE.map != 'NONE':
                            self.AFC.tool_cmds[LANE.map] = LANE.name
                        # Check first for hub_loaded as this was the old name in software with version <= 1030
                        if 'hub_loaded' in units[LANE.unit][LANE.name]: LANE.loaded_to_hub = units[LANE.unit][LANE.name]['hub_loaded']
                        # Check for loaded_to_hub as this is how its being saved version > 1030
                        if 'loaded_to_hub' in units[LANE.unit][LANE.name]: LANE.loaded_to_hub = units[LANE.unit][LANE.name]['loaded_to_hub']
                        if 'tool_loaded' in units[LANE.unit][LANE.name]: LANE.tool_loaded = units[LANE.unit][LANE.name]['tool_loaded']
                        if 'status' in units[LANE.unit][LANE.name]: LANE.status = units[LANE.unit][LANE.name]['status']
        self.AFC.save_vars()
        if self.enable == False:
            self.AFC.gcode.respond_info('Prep Checks Disabled')
            return
        else:
            for UNIT in self.AFC.units.keys():
                try: CUR_UNIT = self.printer.lookup_object(self.AFC.units[UNIT] + ' ' + UNIT)
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

