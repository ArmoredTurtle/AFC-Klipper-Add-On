import json
try:
    from urllib.request import urlopen
except:
    # Python 2.7 support
    from urllib2 import urlopen

class afcSpool:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up the AFC object
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')
        self.ERROR = self.AFC.ERROR
        self.reactor = self.AFC.reactor
        self.gcode = self.AFC.gcode

        self.gcode.register_mux_command('SET_COLOR',None,None, self.cmd_SET_COLOR, desc=self.cmd_SET_COLOR_help)
        self.gcode.register_mux_command('SET_WEIGHT',None,None, self.cmd_SET_WEIGHT, desc=self.cmd_SET_WEIGHT_help)
        self.gcode.register_mux_command('SET_MATERIAL',None,None, self.cmd_SET_MATERIAL, desc=self.cmd_SET_MATERIAL_help)
        self.gcode.register_mux_command('SET_SPOOL_ID',None,None, self.cmd_SET_SPOOLID, desc=self.cmd_SET_SPOOLID_help)
        self.gcode.register_mux_command('SET_RUNOUT',None,None, self.cmd_SET_RUNOUT, desc=self.cmd_SET_RUNOUT_help)
        self.gcode.register_mux_command('SET_MAP',None,None, self.cmd_SET_MAP, desc=self.cmd_SET_MAP_help)
        self.gcode.register_command("RESET_AFC_MAPPING", self.cmd_RESET_AFC_MAPPING, desc=self.cmd_RESET_AFC_MAPPING_help)

        self.URL = 'http://{}:{}/api/v1/spool/'.format(self.AFC.spoolman_ip, self.AFC.spoolman_port)


    cmd_SET_MAP_help = "change filaments map"
    def cmd_SET_MAP(self, gcmd):
        """
        This function handles changing the GCODE tool change command for a Lane.

        Usage: `SET_MAP LANE=<lane> MAP=<cmd>`
        Example: `SET_MAP LANE=leg1 MAP=T1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  - LANE: The name of the lane whose map is to be changed.
                  - MAP: The new tool change gcode for lane (optional, defaults to None).

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.gcode.respond_info("No LANE Defined")
            return
        map_cmd = gcmd.get('MAP', None)
        lane_switch=self.AFC.tool_cmds[map_cmd]
        self.gcode.respond_info("lane to switch is " + lane_switch)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        for UNIT_SERACH in self.AFC.lanes.keys():
            self.gcode.respond_info("looking for "+lane+" in " + UNIT_SERACH)
            if lane in self.AFC.lanes[UNIT_SERACH]:
                self.AFC.tool_cmds[map_cmd]=lane
                map_switch=self.AFC.lanes[UNIT_SERACH][CUR_LANE.name]['map']
                self.AFC.lanes[UNIT_SERACH][CUR_LANE.name]['map']=map_cmd
                CUR_LANE.map=map_cmd

        for UNIT_SERACH in self.AFC.lanes.keys():
            if lane_switch in self.AFC.lanes[UNIT_SERACH]:
                SW_LANE = self.printer.lookup_object('AFC_stepper ' + lane_switch)
                self.AFC.tool_cmds[map_switch]=lane_switch
                self.AFC.lanes[UNIT_SERACH][lane_switch]['map']=map_switch
                SW_LANE.map=map_switch
        self.AFC.save_vars()

    cmd_SET_COLOR_help = "change filaments color"
    def cmd_SET_COLOR(self, gcmd):
        """
        This function handles changing the color of a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and sets its color to the value provided by the 'COLOR' parameter.

        Usage: `SET_COLOR LANE=<lane> COLOR=<color>`
        Example: `SET_COLOR LANE=leg1 COLOR=FF0000`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  - LANE: The name of the lane whose color is to be changed.
                  - COLOR: The new color value in hexadecimal format (optional, defaults to '#000000').

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.gcode.respond_info("No LANE Defined")
            return
        color = gcmd.get('COLOR', '#000000')
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_LANE.color = '#' + color
        self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['color'] ='#'+ color
        self.AFC.save_vars()

    cmd_SET_WEIGHT_help = "change filaments color"
    def cmd_SET_WEIGHT(self, gcmd):
        """
        This function handles changing the material of a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and sets its material to the value provided by the 'MATERIAL' parameter.

        Usage: SET_WEIGHT LANE=<lane> WEIGHT=<weight>
        Example: SET_WEIGHT LANE=leg1 WEIGHT=850

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  
                    LANE: The name of the lane whose weight is to be changed.
                    WEIGHT: The new weight (optional, defaults to '').

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.gcode.respond_info("No LANE Defined")
            return
        weight = gcmd.get('WEIGHT', '')
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_LANE.weight = weight
        self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['weight'] = weight
        self.AFC.save_vars()

    cmd_SET_MATERIAL_help = "change filaments color"
    def cmd_SET_MATERIAL(self, gcmd):
        """
        This function handles changing the material of a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and sets its material to the value provided by the 'MATERIAL' parameter.

        Usage: SET_MATERIAL LANE=<lane> MATERIAL=<material>
        Example: SET_MATERIAL LANE=leg1 MATERIAL=ABS

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  
                      LANE: The name of the lane whose material is to be changed.
                      MATERIAL: The new material (optional, defaults to '').

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.gcode.respond_info("No LANE Defined")
            return
        material = gcmd.get('MATERIAL', '')
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_LANE.material = material
        self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['material'] = material
        self.AFC.save_vars()
    def set_active_spool(self, ID):
        webhooks = self.printer.lookup_object('webhooks')
        if self.AFC.spoolman_ip != None:
            if ID and ID is not None:
                id = int(ID)
            else:
                id = None

            args = {'spool_id' : id }
            try:
                webhooks.call_remote_method("spoolman_set_active_spool", **args)
            except self.printer.command_error as e:
                self.gcode._respond_error("Error trying to set active spool \n{}".format(e))

    cmd_SET_SPOOLID_help = "change filaments ID"
    def cmd_SET_SPOOLID(self, gcmd):
        """
        This function handles setting the spool ID for a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and updates its spool ID, material, color, and weight
        based on the information retrieved from the Spoolman API.

        Usage: `SET_SPOOLID LANE=<lane> SPOOL_ID=<spool_id>`
        Example: `SET_SPOOLID LANE=leg1 SPOOL_ID=12345`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  - LANE: The name of the lane whose spool ID is to be set.
                  - SPOOL_ID: The new spool ID (optional, defaults to an empty string).

        Returns:
            None
        """
        if self.AFC.spoolman_ip !=None:
            lane = gcmd.get('LANE', None)
            if lane == None:
                self.gcode.respond_info("No LANE Defined")
                return
            SpoolID = gcmd.get('SPOOL_ID', '')
            CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
            self.set_spoolID(CUR_LANE, SpoolID)

    def set_spoolID(self, CUR_LANE, SpoolID):
        if self.AFC.spoolman_ip !=None:
            if SpoolID !='':
                try:
                    url =  "{}{}".format(self.URL, SpoolID)
                    result = json.load(urlopen(url))
                    self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'] = SpoolID
                    self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['material'] = result['filament']['material']
                    self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['color'] = '#' + result['filament']['color_hex']
                    if 'remaining_weight' in result: self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['weight'] =  result['remaining_weight']
                except:
                    self.AFC.ERROR.AFC_error("Error when trying to get Spoolman data for ID:{}".format(SpoolID), False)
            else:
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'] = ''
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['material'] = ''
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['color'] = ''
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['weight'] = ''
            self.AFC.save_vars()

    cmd_SET_RUNOUT_help = "change filaments ID"
    def cmd_SET_RUNOUT(self, gcmd):
        """
        This function handles setting the runout lane (infanet spool) for a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and updates its the lane to use if filament is empty
        based on the information retrieved from the Spoolman API.

        Usage: `SET_RUNOUT LANE=<lane> RUNOUT=<lane>`
        Example: `SET_RUNOUT LANE=lane1 RUNOUT=lane4`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  - LANE: The name of the lane whose spool ID is to be set.
                  - RUNOUT: The lane to use if LANE runsout (optional, defaults to an empty string).

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.gcode.respond_info("No LANE Defined")
            return
        runout = gcmd.get('RUNOUT', '')
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['runout_lane'] = runout
        self.AFC.save_vars()
        self.gcode.respond_info("This is a feature WIP. Not functioning yet")
    
    cmd_RESET_AFC_MAPPING_help = "Resets all lane mapping in AFC"
    def cmd_RESET_AFC_MAPPING(self, gcmd):
        """
        This commands resets all tool lane mapping to the order that is setup in configuration.

        Useful to put in your PRINT_END macro to reset mapping

        Usage: RESET_AFC_MAPPING
        """
        t_index = 0
        for key, unit in self.AFC.lanes.items():
            for lane in unit:
                map_cmd = "T{}".format(t_index)
                self.AFC.tool_cmds[map_cmd] = lane
                self.AFC.lanes[key][lane]['map']=map_cmd
                self.printer.lookup_object('AFC_stepper ' + lane).map = map_cmd
                t_index += 1

        self.AFC.save_vars()
        self.AFC.gcode.respond_info("Tool mappings reset")

def load_config(config):
    return afcSpool(config)
