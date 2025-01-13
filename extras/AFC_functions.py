# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import os

def load_config(config):
    return afcFunction(config)

class afcFunction:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.printer.register_event_handler("afc_stepper:register_macros",self.register_lane_macros)
        self.printer.register_event_handler("afc_hub:register_macros",self.register_hub_macros)
        self.errorLog= {}
        self.pause= False

    def register_lane_macros(self, lane_obj):
        """
        Callback function to register macros with proper lane names so that klipper errors out correctly when users supply lanes names that
        are not valid

        :param lane_obj: object for lane to register
        """
        self.AFC.gcode.register_mux_command('TEST',         "LANE", lane_obj.name, self.cmd_TEST,         desc=self.cmd_TEST_help)
        self.AFC.gcode.register_mux_command('HUB_CUT_TEST', "LANE", lane_obj.name, self.cmd_HUB_CUT_TEST, desc=self.cmd_HUB_CUT_TEST_help)

    def register_hub_macros(self, hub_obj):
        """
        Callback function to register macros with proper hub names so that klipper errors out correctly when users supply hub names that
        are not valid

        :param hub_obj: object for hub to register
        """
        self.AFC.gcode.register_mux_command('SET_BOWDEN_LENGTH', 'HUB', hub_obj.name, self.cmd_SET_BOWDEN_LENGTH, desc=self.cmd_SET_BOWDEN_LENGTH_help)

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')
        self.AFC.gcode.register_mux_command('CALIBRATE_AFC', None, None, self.cmd_CALIBRATE_AFC, desc=self.cmd_CALIBRATE_AFC_help)

    cmd_CALIBRATE_AFC_help = 'calibrate the dist hub for lane and then afc_bowden_length'
    def cmd_CALIBRATE_AFC(self, gcmd):
        """
        This function performs the calibration of the hub and Bowden length for one or more lanes within an AFC
        (Automated Filament Changer) system. The function uses precise movements to adjust the positions of the
        steppers, check the state of the hubs and tools, and calculate distances for calibration based on the
        user-provided input. If no specific lane is provided, the function defaults to notifying the user that no lane has been selected. The function also includes
        the option to calibrate the Bowden length for a particular lane, if specified.

        Usage:`CALIBRATE_AFC LANE=<lane> DISTANCE=<distance> TOLERANCE=<tolerance> BOWDEN=<lane>`
        Examples:
            - `CALIBRATE_AFC LANE=all Bowden=leg1 DISTANCE=30 TOLERANCE=3`
            - `CALIBRATE_AFC BOWDEN=leg1` (Calibrates the Bowden length for 'leg1')

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                Parameters:
                - LANES: Specifies the lane to calibrate. If not provided, calibrates no lanes.
                - DISTANCE: The distance to move during calibration (optional, defaults to 25mm).
                - TOLERANCE: The tolerance for fine adjustments during calibration (optional, defaults to 5mm).
                - BOWDEN: Specifies the lane to perform Bowden length calibration (optional).

        Returns:
            None
        """
        dis    = gcmd.get_float('DISTANCE' , 25)
        tol    = gcmd.get_float('TOLERANCE', 5)
        afc_bl = gcmd.get(      'BOWDEN'   , None)
        lanes  = gcmd.get(      'LANE'     , None)
        unit   = gcmd.get(      'UNIT'     , None)

        if self.AFC.current is not None:
            self.AFC.gcode.respond_info('Tool must be unloaded to calibrate Bowden length')
            return

        cal_msg = ''

        # Determine if a specific lane is provided
        if lanes is not None:
            self.AFC.gcode.respond_info('Starting AFC distance Calibrations')
            cal_msg += 'AFC Calibration distances +/-{}mm'.format(tol)
            if unit is None:
                if lanes != 'all':
                    CUR_LANE=self.AFC.lanes[lanes]
                    checked, msg = CUR_LANE.unit_obj.calibrate_lane(CUR_LANE, tol)
                    if(not checked): return
                    cal_msg += msg
                else:
                    # Calibrate all lanes if no specific lane is provided
                    for CUR_LANE in self.AFC.lanes.values():
                        # Calibrate the specific lane
                        checked, msg = CUR_LANE.unit_obj.calibrate_lane(CUR_LANE, tol)
                        if(not checked): return
                        cal_msg += msg
            else:
                if lanes != 'all':
                    CUR_LANE=self.AFC.lanes[lanes]
                    checked, msg = CUR_LANE.unit_obj.calibrate_lane(CUR_LANE, tol)
                    if(not checked): return
                    cal_msg += msg
                else:
                    CUR_UNIT = self.AFC.units[unit]
                    self.AFC.gcode.respond_info('{}'.format(CUR_UNIT))
                    # Calibrate all lanes if no specific lane is provided
                    for CUR_LANE in CUR_UNIT.lanes.values():
                        # Calibrate the specific lane
                        checked, msg = CUR_UNIT.calibrate_lane(CUR_LANE, tol)
                        if(not checked): return
                        cal_msg += msg
        else:
            cal_msg +='No lanes selected to calibrate dist_hub'


        # Calibrate Bowden length with specified lane
        if afc_bl is not None:
            self.AFC.gcode.respond_info('Starting AFC distance Calibrations')
            cal_msg += 'AFC Calibration distances +/-{}mm'.format(tol)
            cal_msg += '\n<span class=info--text>Update values in AFC_Hardware.cfg</span>'
            CUR_LANE=self.AFC.lanes[afc_bl]
            CUR_LANE.unit_obj.calibrate_bowden(CUR_LANE, dis, tol)

    def ConfigRewrite(self, rawsection, rawkey, rawvalue, msg=None):
        taskdone = False
        sectionfound = False
        for filename in os.listdir(self.AFC.cfgloc):
            file_path = os.path.join(self.AFC.cfgloc, filename)
            if os.path.isfile(file_path) and filename.endswith(".cfg"):
                with open(file_path, 'r') as f:
                    dataout = ''
                    for line in f:
                        if rawsection in line: sectionfound = True
                        if sectionfound == True and line.startswith(rawkey):
                            comments = ""
                            try:
                                comments = line.index('#')
                            except:
                                pass
                            line = "{}: {}{}\n".format(rawkey, rawvalue, comments )
                            sectionfound = False
                            taskdone = True
                        dataout += line
                if taskdone:
                    f=open(file_path, 'w')
                    f.write(dataout)
                    f.close
                    taskdone = False
                    msg +='\n<span class=info--text>Saved to configuration file</span>'
                    self.AFC.gcode.respond_info(msg)
                    return
        msg +='\n<span class=info--text>Update values in [' + rawsection +']</span>'
        self.AFC.save_vars()
        self.AFC.gcode.respond_info(msg)

    def TcmdAssign(self, CUR_LANE):
        if CUR_LANE.map == 'NONE' :
            for x in range(99):
                cmd = 'T'+str(x)
                if cmd not in self.AFC.tool_cmds:
                    CUR_LANE.map = cmd
                    break
        self.AFC.tool_cmds[CUR_LANE.map]=CUR_LANE.name
        try:
            self.AFC.gcode.register_command(CUR_LANE.map, self.AFC.cmd_CHANGE_TOOL, desc=self.AFC.cmd_CHANGE_TOOL_help)
        except:
            self.AFC.gcode.respond_info("Error trying to map lane {lane} to {tool_macro}, please make sure there are no macros already setup for {tool_macro}".format(lane=[CUR_LANE.name], tool_macro=CUR_LANE.map), )
        self.AFC.save_vars()

    def is_homed(self):
        curtime = self.AFC.reactor.monotonic()
        kin_status = self.AFC.toolhead.get_kinematics().get_status(curtime)
        if ('x' not in kin_status['homed_axes'] or 'y' not in kin_status['homed_axes'] or 'z' not in kin_status['homed_axes']):
            return False
        else:
            return True

    def is_printing(self):
        eventtime = self.AFC.reactor.monotonic()
        idle_timeout = self.printer.lookup_object("idle_timeout")
        if idle_timeout.get_status(eventtime)["state"] == "Printing":
            return True
        else:
            False

    def is_paused(self):
        eventtime = self.AFC.reactor.monotonic()
        pause_resume = self.printer.lookup_object("pause_resume")
        return bool(pause_resume.get_status(eventtime)["is_paused"])

    def afc_led (self, status, idx=None):
        if idx == None:
            return
        # Try to find led object, if not found print error to console for user to see
        afc_object = 'AFC_led '+ idx.split(':')[0]
        try:
            led = self.printer.lookup_object(afc_object)
            led.led_change(int(idx.split(':')[1]), status)
        except:
            error_string = "Error: Cannot find [{}] in config, make sure led_index in config is correct for AFC_stepper {}".format(afc_object, idx.split(':')[-1])
            self.AFC.gcode.respond_info( error_string)
        led.led_change(int(idx.split(':')[1]), status)

    def get_filament_status(self, CUR_LANE):
        if CUR_LANE.prep_state:
            if CUR_LANE.load_state:
                if CUR_LANE.extruder_obj is not None and CUR_LANE.extruder_obj.lane_loaded == CUR_LANE.name:
                    return 'In Tool:' + self.HexConvert(CUR_LANE.led_tool_loaded).split(':')[-1]
                return "Ready:" + self.HexConvert(CUR_LANE.led_ready).split(':')[-1]
            return 'Prep:' + self.HexConvert(CUR_LANE.led_prep_loaded).split(':')[-1]
        return 'Not Ready:' + self.HexConvert(CUR_LANE.led_not_ready).split(':')[-1]

    def HexConvert(self,tmp):
        led=tmp.split(',')
        if float(led[0])>0:
            led[0]=int(255*float(led[0]))
        else:
            led[0]=0
        if float(led[1])>0:
            led[1]=int(255*float(led[1]))
        else:
            led[1]=0
        if float(led[2])>0:
            led[2]=int(255*float(led[2]))
        else:
            led[2]=0

        return '#{:02x}{:02x}{:02x}'.format(*led)

    cmd_SET_BOWDEN_LENGTH_help = "Helper to dynamically set length of bowden between hub and toolhead. Pass in HUB if using multiple box turtles"
    def cmd_SET_BOWDEN_LENGTH(self, gcmd):
        """
        This function adjusts the length of the Bowden tube between the hub and the toolhead.
        It retrieves the hub specified by the 'HUB' parameter and the length adjustment specified
        by the 'LENGTH' parameter. If the hub is not specified and a lane is currently loaded,
        it uses the hub of the current lane.

        Usage: `SET_BOWDEN_LENGTH HUB=<hub> LENGTH=<length>`
        Example: `SET_BOWDEN_LENGTH HUB=Turtle_1 LENGTH=100`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  - HUB: The name of the hub to be adjusted (optional).
                  - LENGTH: The length adjustment value (optional).

        Returns:
            None
        """
        hub           = gcmd.get("HUB", None )
        length_param  = gcmd.get('LENGTH', None)

        # If hub is not passed in try and get hub if a lane is currently loaded
        if hub is None and self.AFC.current is not None:
            CUR_LANE = self.AFC.lanes[self.current]
            hub     = CUR_LANE.hub_obj.name
        elif hub is None and self.current is None:
            self.AFC.gcode.respond_info("A lane is not loaded please specify hub to adjust bowden length")
            return

        CUR_HUB = self.AFC.hubs[hub]
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
        self.AFC.gcode.respond_raw(msg)

    cmd_HUB_CUT_TEST_help = "Test the cutting sequence of the hub cutter, expects LANE=legN"
    def cmd_HUB_CUT_TEST(self, gcmd):
        """
        This function tests the cutting sequence of the hub cutter for a specified lane.
        It retrieves the lane specified by the 'LANE' parameter, performs the hub cut,
        and responds with the status of the operation.

        Usage: `HUB_CUT_TEST LANE=<lane>`
        Example: `HUB_CUT_TEST LANE=leg1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameter:
                  - LANE: The name of the lane to be tested.

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        self.AFC.gcode.respond_info('Testing Hub Cut on Lane: ' + lane)
        if lane not in self.AFC.lanes:
            self.AFC.gcode.respond_info('{} Unknown'.format(lane))
            return
        CUR_LANE = self.AFC.lanes[lane]
        CUR_HUB = CUR_LANE.hub_obj
        CUR_HUB.hub_cut(CUR_LANE)
        self.AFC.gcode.respond_info('Hub cut Done!')

    cmd_TEST_help = "Test Assist Motors"
    def cmd_TEST(self, gcmd):
        """
        This function tests the assist motors of a specified lane at various speeds.
        It performs the following steps:
        1. Retrieves the lane specified by the 'LANE' parameter.
        2. Tests the assist motor at full speed, 50%, 30%, and 10% speeds.
        3. Reports the status of each test step.

        Usage: `TEST LANE=<lane>`
        Example: `TEST LANE=leg1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameter:
                  - LANE: The name of the lane to be tested.

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        if lane == None:
            self.AFC.ERROR.AFC_error('Must select LANE', False)
            return
        self.AFC.gcode.respond_info('TEST ROUTINE')
        if lane not in self.AFC.lanes:
            self.AFC.gcode.respond_info('{} Unknown'.format(lane))
            return
        CUR_LANE = self.AFC.lanes[lane]
        self.AFC.gcode.respond_info('Testing at full speed')
        CUR_LANE.assist(-1)
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 1)
        if CUR_LANE.afc_motor_rwd.is_pwm:
            self.AFC.gcode.respond_info('Testing at 50 percent speed')
            CUR_LANE.assist(-.5)
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 1)
            self.AFC.gcode.respond_info('Testing at 30 percent speed')
            CUR_LANE.assist(-.3)
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 1)
            self.AFC.gcode.respond_info('Testing at 10 percent speed')
            CUR_LANE.assist(-.1)
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 1)
        self.AFC.gcode.respond_info('Test routine complete')
        CUR_LANE.assist(0)
