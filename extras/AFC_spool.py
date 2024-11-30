import json
try:
    from urllib.request import urlopen
except:
    # Python 2.7 support
    from urllib2 import urlopen

class afcSpool:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

        self.gcode.register_mux_command('SET_COLOR',None,None, self.cmd_SET_COLOR, desc=self.cmd_SET_COLOR_help)
        self.gcode.register_mux_command('SET_SPOOL_ID',None,None, self.cmd_SET_SPOOLID, desc=self.cmd_SET_SPOOLID_help)
        self.gcode.register_mux_command('SET_RUNOUT',None,None, self.cmd_SET_RUNOUT, desc=self.cmd_SET_RUNOUT_help)
        self.gcode.register_mux_command('SET_MAP',None,None, self.cmd_SET_RUNOUT, desc=self.cmd_SET_RUNOUT_help)

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up the AFC object
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')
        self.ERROR = self.printer.lookup_object('AFC_error')

    cmd_SET_MAP_help = "change filaments color"
    def cmd_SET_MAP(self, gcmd):
        """
        This function handles changing the GCODE tool change command for a Lane.

        Usage: `SET_MAP LANE=<lane> MAP=<cmd>`
        Example: `SET_MAP LANE=leg1 MAP=T1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  - LANE: The name of the lane whose color is to be changed.
                  - MAP: The new tool change gcode for lane (optional, defaults to None).

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.gcode.respond_info("No LANE Defined")
            return
        map_cmd = gcmd.get('MAP', None)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_LANE.map = map_cmd
        for UNIT_SERACH in self.AFC.lanes.keys():
            if lane in self.AFC.lanes[UNIT_SERACH]:
                UNIT = UNIT_SERACH

        lane_switch=self.AFC.tool_cmds[map_cmd]
        for UNIT_SERACH in self.AFC.lanes.keys():
            if lane_switch in self.AFC.lanes[UNIT_SERACH]:
                UNIT_switch = UNIT_SERACH

        self.AFC.tool_cmds[map_cmd]=lane_switch
        self.AFC.lanes[UNIT_switch][lane_switch]['map'] = self.AFC.lanes[UNIT][CUR_LANE]['map']

        self.AFC.tool_cmds[map_cmd]=lane
        self.AFC.lanes[UNIT][CUR_LANE]['map']

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

    def set_active_spool(self, ID):
        webhooks = self.printer.lookup_object('webhooks')
        if self.AFC.spoolman_ip != None:
            if ID:
                args = {'spool_id' : int(ID)}
                try:
                    webhooks.call_remote_method("spoolman_set_active_spool", **args)
                except self.printer.command_error:
                    self.gcode._respond_error("Error trying to set active spool")
            else:
                self.gcode.respond_info("Spool ID not set, cannot update spoolman with active spool")

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
            if SpoolID !='':
                url = 'http://' + self.AFC.spoolman_ip + ':'+ self.AFC.spoolman_port +"/api/v1/spool/" + SpoolID
                result = json.load(urlopen(url))
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'] = SpoolID
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['material'] = result['filament']['material']
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['color'] = '#' + result['filament']['color_hex']
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['weight'] =  result['remaining_weight']
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
        if self.AFC.spoolman_ip !=None:
            lane = gcmd.get('LANE', None)
            if lane == None:
                self.gcode.respond_info("No LANE Defined")
                return
            runout = gcmd.get('RUNOUT', '')
            CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
            self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['runout_lane'] = runout
            self.AFC.save_vars()

def load_config(config):
    return afcSpool(config)
