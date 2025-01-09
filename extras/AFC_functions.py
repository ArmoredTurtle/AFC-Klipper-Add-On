import os

def load_config(config):
    return afcFunction(config)

class afcFunction:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.errorLog= {}
        self.pause= False

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')

        self.AFC.gcode.register_command('TEST', self.cmd_TEST, desc=self.cmd_TEST_help)
        self.AFC.gcode.register_command('HUB_CUT_TEST', self.cmd_HUB_CUT_TEST, desc=self.cmd_HUB_CUT_TEST_help)
        self.AFC.gcode.register_mux_command('SET_BOWDEN_LENGTH', 'AFC', None, self.cmd_SET_BOWDEN_LENGTH, desc=self.cmd_SET_BOWDEN_LENGTH_help)
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
        dis = gcmd.get_float('DISTANCE', 25)
        tol = gcmd.get_float('TOLERANCE', 5)
        afc_bl = gcmd.get('BOWDEN', None)
        short_dis = self.AFC.short_move_dis
        lanes = gcmd.get('LANE', None)

        if self.AFC.current is not None:
            self.AFC.gcode.respond_info('Tool must be unloaded to calibrate Bowden length')
            return

        cal_msg = ''

        def find_lane_to_calibrate(lane_name):
            """
            Search for the given lane across all units in the AFC system.

            Args: lane_name: The name of the lane to search for

            Returns: The lane name if found, otherwise None
            """
            if lane_name in self.AFC.lanes:
                return lane_name

            # If the lane was not found
            self.AFC.gcode.respond_info('{} not found in any unit.'.format(lane_name))
            return None

        # Helper functions for movement and calibration
        def calibrate_hub(CUR_LANE):
            hub_pos = 0
            hub_pos = move_until_state(CUR_LANE, lambda: CUR_LANE.hub_obj.state, CUR_LANE.hub_obj.move_dis, tol, short_dis, hub_pos)
            tuned_hub_pos = calc_position(CUR_LANE, lambda: CUR_LANE.hub_obj.state, hub_pos, short_dis, tol)
            return tuned_hub_pos

        def move_until_state(CUR_LANE, state, move_dis, tolerance, short_move, pos=0):
            while state() == False:
                CUR_LANE.move(move_dis, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
                pos += move_dis
            self.AFC.reactor.pause(self.reactor.monotonic() + 0.1)
            while state() == True:
                CUR_LANE.move(short_move * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
                pos -= short_move
            self.AFC.reactor.pause(self.reactor.monotonic() + 0.1)
            while state() == False:
                CUR_LANE.move(tolerance, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
                pos += tolerance
            return pos

        def calc_position(CUR_LANE, state, pos, short_move, tolerance):
            while state():
                CUR_LANE.move(short_move * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
                pos -= short_move
            self.AFC.reactor.pause(self.reactor.monotonic() + 0.1)
            while not state():
                CUR_LANE.move(tolerance, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
                pos += tolerance
            return pos

        def calibrate_lane(LANE):
            if LANE not in self.AFC.lanes:
                self.AFC.gcode.respond_info(LANE + ' Unknown')
                return
            CUR_LANE = self.lanes[LANE]
            CUR_HUB = CUR_LANE.hub_obj
            if CUR_HUB.state:
                self.AFC.gcode.respond_info('Hub is not clear, check before calibration')
                return False, ""
            if not CUR_LANE.load_state:
                self.AFC.gcode.respond_info('{} not loaded, load before calibration'.format(CUR_LANE.name.upper()))
                return True, ""

            self.AFC.gcode.respond_info('Calibrating {}'.format(CUR_LANE.name.upper()))
            # reset to extruder
            calc_position(CUR_LANE, lambda: CUR_LANE.load_state, 0, short_dis, tol)
            hub_pos = calibrate_hub(CUR_LANE)
            if CUR_HUB.state:
                CUR_LANE.move(CUR_HUB.move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
            CUR_LANE.hub_load = True
            CUR_LANE.do_enable(False)
            CUR_LANE.dist_hub = hub_pos - CUR_HUB.hub_clear_move_dis
            cal_msg = "\n{} dist_hub: {}".format(CUR_LANE.name.upper(), (hub_pos - CUR_HUB.hub_clear_move_dis))
            self.ConfigRewrite(CUR_LANE.fullname, "dist_hub", hub_pos - CUR_HUB.hub_clear_move_dis, cal_msg)
            return True, cal_msg

        # Determine if a specific lane is provided
        if lanes is not None:
            self.AFC.gcode.respond_info('Starting AFC distance Calibrations')
            cal_msg += 'AFC Calibration distances +/-{}mm'.format(tol)
            if lanes != 'all':
                lane_to_calibrate = find_lane_to_calibrate(lanes)
                if lane_to_calibrate is None:
                    return
                # Calibrate the specific lane
                checked, msg = calibrate_lane(lane_to_calibrate)
                if(not checked): return
                cal_msg += msg
            else:
                # Calibrate all lanes if no specific lane is provided
                for LANE in self.AFC.lanes.keys():
                    # Calibrate the specific lane
                    checked, msg = calibrate_lane(LANE)
                    if(not checked): return
                    cal_msg += msg
        else:
            cal_msg +='No lanes selected to calibrate dist_hub'

        if afc_bl is not None:
            if lanes is None:
                self.AFC.gcode.respond_info('Starting AFC distance Calibrations')
                cal_msg += 'AFC Calibration distances +/-{}mm'.format(tol)

            lane_to_calibrate = find_lane_to_calibrate(afc_bl)

            if lane_to_calibrate is None:
                return

            lane = lane_to_calibrate
            CUR_LANE = self.AFC.lanes[lane]
            CUR_EXTRUDER = CUR_LANE.extruder_obj
            CUR_HUB = CUR_LANE.hub_obj
            self.AFC.gcode.respond_info('Calibrating Bowden Length with {}'.format(CUR_LANE.name.upper()))

            move_until_state(CUR_LANE, lambda: CUR_HUB.state, CUR_HUB.move_dis, tol, short_dis)

            bow_pos = 0
            if CUR_EXTRUDER.tool_start:
                while not CUR_EXTRUDER.tool_start_state:
                    CUR_LANE.move(dis, self.short_moves_speed, self.short_moves_accel)
                    bow_pos += dis
                    self.AFC.reactor.pause(self.reactor.monotonic() + 0.1)
                bow_pos = calc_position(CUR_LANE, lambda: CUR_EXTRUDER.tool_start_state, bow_pos, short_dis, tol)
                CUR_LANE.move(bow_pos * -1, CUR_LANE.long_moves_speed, CUR_LANE.long_moves_accel, True)
                if CUR_HUB.state:
                    CUR_LANE.move(CUR_HUB.move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
                if CUR_EXTRUDER.tool_start == 'buffer':
                    cal_msg += '\n afc_bowden_length: {}'.format(bow_pos - (short_dis * 2))
                    self.ConfigRewrite(CUR_HUB.fullname, "afc_bowden_length", bow_pos - (short_dis * 2), cal_msg)
                else:
                    cal_msg += '\n afc_bowden_length: {}'.format(bow_pos - short_dis)
                    self.ConfigRewrite(CUR_HUB.fullname, "afc_bowden_length", bow_pos - short_dis, cal_msg)
                CUR_LANE.do_enable(False)
            else:
                self.AFC.gcode.respond_info('CALIBRATE_AFC is not currently supported without tool start sensor')

        self.AFC.save_vars()

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

        CUR_HUB = CUR_LANE.hub_obj
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
            self.AFC.gcode.respond_info('{} Unknown'.format(lane.upper()))
            return
        CUR_LANE = self.lanes[lane]
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
            self.AFC.gcode.respond_info('{} Unknown'.format(lane.upper()))
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