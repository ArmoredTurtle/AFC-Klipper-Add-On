# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.


class AFCSpool:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up the AFC object
        and assigns it to the instance variable `self.AFC`.
        """
        self.afc        = self.printer.lookup_object('AFC')
        self.error      = self.afc.error
        self.reactor    = self.afc.reactor
        self.gcode      = self.afc.gcode
        self.logger     = self.afc.logger

        # Registering stepper callback so that mux macro can be set properly with valid lane names
        self.printer.register_event_handler("afc_stepper:register_macros",self.register_lane_macros)

        self.gcode.register_command("RESET_AFC_MAPPING", self.cmd_RESET_AFC_MAPPING, desc=self.cmd_RESET_AFC_MAPPING_help)

    def register_lane_macros(self, lane_obj):
        """
        Callback function to register macros with proper lane names so that klipper errors out correctly when users supply lanes that
        are not valid

        :param lane_obj: object for lane to register
        """
        self.gcode.register_mux_command('SET_COLOR',    "LANE", lane_obj.name, self.cmd_SET_COLOR,      desc=self.cmd_SET_COLOR_help)
        self.gcode.register_mux_command('SET_WEIGHT',   "LANE", lane_obj.name, self.cmd_SET_WEIGHT,     desc=self.cmd_SET_WEIGHT_help)
        self.gcode.register_mux_command('SET_MATERIAL', "LANE", lane_obj.name, self.cmd_SET_MATERIAL,   desc=self.cmd_SET_MATERIAL_help)
        self.gcode.register_mux_command('SET_SPOOL_ID', "LANE", lane_obj.name, self.cmd_SET_SPOOL_ID,   desc=self.cmd_SET_SPOOL_ID_help)
        self.gcode.register_mux_command('SET_RUNOUT',   "LANE", lane_obj.name, self.cmd_SET_RUNOUT,     desc=self.cmd_SET_RUNOUT_help)
        self.gcode.register_mux_command('SET_MAP',      "LANE", lane_obj.name, self.cmd_SET_MAP,        desc=self.cmd_SET_MAP_help)

    cmd_SET_MAP_help = "Changes T(n) mapping for a lane"
    def cmd_SET_MAP(self, gcmd):
        """
        This function handles changing the GCODE tool change command for a Lane.

        Usage
        -----
        `SET_MAP LANE=<lane> MAP=<cmd>`

        Example
        -----
        ```
        SET_MAP LANE=lane1 MAP=T1
        ```
        """
        lane = gcmd.get('LANE', None)
        if lane is None:
            self.logger.info("No LANE Defined")
            return
        map_cmd = gcmd.get('MAP', None)
        lane_switch=self.afc.tool_cmds[map_cmd]
        self.logger.debug("lane to switch is {}".format(lane_switch))
        if lane not in self.afc.lanes:
            self.logger.info('{} Unknown'.format(lane))
            return
        cur_lane = self.afc.lanes[lane]
        self.afc.tool_cmds[map_cmd]=lane
        map_switch=cur_lane.map
        cur_lane.map=map_cmd

        sw_lane = self.afc.lanes[lane_switch]
        self.afc.tool_cmds[map_switch]=lane_switch
        sw_lane.map=map_switch
        self.afc.save_vars()

    cmd_SET_COLOR_help = "Set filaments color for a lane"
    def cmd_SET_COLOR(self, gcmd):
        """
        This function handles changing the color of a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and sets its color to the value provided by the 'COLOR' parameter.
        The 'COLOR' parameter should be a hex color code.

        Usage
        -----
        `SET_COLOR LANE=<lane> COLOR=<color>`

        Example
        -----
        ```
        SET_COLOR LANE=lane1 COLOR=FF0000
        ```
        """
        lane = gcmd.get('LANE', None)
        if lane is None:
            self.logger.info("No LANE Defined")
            return
        color = gcmd.get('COLOR', '#000000')
        if lane not in self.afc.lanes:
            self.logger.info('{} Unknown'.format(lane))
            return
        cur_lane = self.afc.lanes[lane]
        cur_lane.color = '#{}'.format(color.replace('#',''))
        self.afc.save_vars()

    cmd_SET_WEIGHT_help = "Sets filaments weight for a lane"
    def cmd_SET_WEIGHT(self, gcmd):
        """
        This function handles changing the weight remaining of a spool loaded in a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and sets its weight to the value provided by the 'WEIGHT' parameter.

        Usage
        -----
        `SET_WEIGHT LANE=<lane> WEIGHT=<weight>`

        Example
        -----
        ```
        SET_WEIGHT LANE=lane1 WEIGHT=850
        ```
        """
        lane = gcmd.get('LANE', None)
        if lane is None:
            self.logger.info("No LANE Defined")
            return
        weight = gcmd.get('WEIGHT', '')
        if lane not in self.afc.lanes:
            self.logger.info('{} Unknown'.format(lane))
            return
        cur_lane = self.afc.lanes[lane]
        cur_lane.weight = weight
        self.afc.save_vars()

    cmd_SET_MATERIAL_help = "Sets filaments material for a lane"
    def cmd_SET_MATERIAL(self, gcmd):
        """
        This function handles changing the material of a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and sets its material to the value provided by the 'MATERIAL' parameter.

        Usage
        -----
        `SET_MATERIAL LANE=<lane> MATERIAL=<material>`

        Example
        -----
        ```
        SET_MATERIAL LANE=lane1 MATERIAL=ABS
        ```
        """
        lane = gcmd.get('LANE', None)
        if lane is None:
            self.logger.info("No LANE Defined")
            return
        material = gcmd.get('MATERIAL', '')
        if lane not in self.afc.lanes:
            self.logger.info('{} Unknown'.format(lane))
            return
        cur_lane = self.afc.lanes[lane]
        cur_lane.material = material
        self.afc.save_vars()

    def set_active_spool(self, ID):
        webhooks = self.printer.lookup_object('webhooks')
        if self.afc.spoolman is not None:
            if ID and ID is not None:
                id = int(ID)
            else:
                id = None

            args = {'spool_id' : id }
            try:
                webhooks.call_remote_method("spoolman_set_active_spool", **args)
            except self.printer.command_error as e:
                self.logger.error("Error trying to set active spool \n{}".format(e))

    cmd_SET_SPOOL_ID_help = "Set lanes spoolman ID"
    def cmd_SET_SPOOL_ID(self, gcmd):
        """
        This function handles setting the spool ID for a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and updates its spool ID, material, color, and weight
        based on the information retrieved from the Spoolman API.

        Usage
        -----
        `SET_SPOOL_ID LANE=<lane> SPOOL_ID=<spool_id>`

        Example
        -----
        ```
        SET_SPOOL_ID LANE=lane1 SPOOL_ID=12345
        ```
        """
        if self.afc.spoolman is not None:
            lane = gcmd.get('LANE', None)
            if lane is None:
                self.logger.info("No LANE Defined")
                return
            SpoolID = gcmd.get('SPOOL_ID', '')
            if lane not in self.afc.lanes:
                self.logger.info('{} Unknown'.format(lane))
                return
            cur_lane = self.afc.lanes[lane]
            self.set_spoolID(cur_lane, SpoolID)

    def _get_filament_values( self, filament, field):
        '''
        Helper function for checking if field is set and returns value if it exists,
        otherwise retruns None

        :param filament: Dictionary for filament values
        :param field:    Field name to check for in dictionary
        :return:         Returns value if field exists or None if field does not exist
        '''
        value = None
        if field in filament:
            value = filament[field]
        return value

    def _clear_values(self, cur_lane):
        """
        Helper function for clearing out lane spool values
        """
        cur_lane.spool_id = ''
        cur_lane.material = ''
        cur_lane.color = ''
        cur_lane.weight = ''
        cur_lane.extruder_temp = None
        cur_lane.material = None

    def set_spoolID(self, cur_lane, SpoolID, save_vars=True):
        if self.afc.spoolman is not None:
            if SpoolID !='':
                try:
                    result = self.afc.moonraker.get_spool(SpoolID)
                    cur_lane.spool_id = SpoolID

                    cur_lane.material       = self._get_filament_values(result['filament'], 'material')
                    cur_lane.extruder_temp  = self._get_filament_values(result['filament'], 'settings_extruder_temp')
                    cur_lane.weight         = self._get_filament_values(result, 'remaining_weight')
                    # Check to see if filament is defined as multi color and take the first color for now
                    # Once support for multicolor is added this needs to be updated
                    if "multi_color_hexes" in result['filament']:
                        cur_lane.color = '#{}'.format(self._get_filament_values(result['filament'], 'multi_color_hexes').split(",")[0])
                    else:
                        cur_lane.color = '#{}'.format(self._get_filament_values(result['filament'], 'color_hex'))

                except Exception as e:
                    self.afc.error.AFC_error("Error when trying to get Spoolman data for ID:{}, Error: {}".format(SpoolID, e), False)
            else:
                self._clear_values(cur_lane)
        else:
            # Clears out values if users are not using spoolman, this is to cover this function being called from LANE UNLOAD and clearing out
            # Manually entered information
            self._clear_values(cur_lane)
        if save_vars: self.afc.save_vars()

    cmd_SET_RUNOUT_help = "Set runout lane"
    def cmd_SET_RUNOUT(self, gcmd):
        """
        This function handles setting the runout lane (infinite spool) for a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and updates it's the lane to use if filament runs out by un-triggering prep sensor.

        Usage
        -----
        `SET_RUNOUT LANE=<lane> RUNOUT=<lane>`

        Example
        -----
        ```
        SET_RUNOUT LANE=lane1 RUNOUT=lane4
        ```
        """
        lane = gcmd.get('LANE', None)
        if lane is None:
            self.logger.info("No LANE Defined")
            return

        runout = gcmd.get('RUNOUT', '')
        # Check to make sure runout does not equal lane
        if lane == runout:
            self.logger.error("Lane({}) and runout({}) cannot be the same".format(lane, runout))
            return
        # Check to make sure specified lane exists
        if lane not in self.afc.lanes:
            self.logger.error('Unknown lane: {}'.format(lane))
            return
        # Check to make sure specified runout lane exists as long as runout is not set as 'NONE'
        if runout != 'NONE' and runout not in self.afc.lanes:
            self.logger.error('Unknown runout lane: {}'.format(runout))
            return

        cur_lane = self.afc.lanes[lane]
        cur_lane.runout_lane = runout
        self.afc.save_vars()

    cmd_RESET_AFC_MAPPING_help = "Resets all lane mapping in AFC"
    def cmd_RESET_AFC_MAPPING(self, gcmd):
        """
        This commands resets all tool lane mapping to the order that is setup in configuration. Useful to put in your PRINT_END macro to reset mapping

        Usage
        -----
        `RESET_AFC_MAPPING`

        Example
        -----
        ```
        RESET_AFC_MAPPING
        ```
        """
        t_index = 0
        for key, unit in self.afc.units.items():
            for lane in unit.lanes:
                map_cmd = "T{}".format(t_index)
                self.afc.tool_cmds[map_cmd] = lane
                self.afc.lanes[lane].map = map_cmd
                t_index += 1

        self.afc.save_vars()
        self.logger.info("Tool mappings reset")

def load_config(config):
    return AFCSpool(config)
