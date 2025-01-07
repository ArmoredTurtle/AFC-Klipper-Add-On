class afcBoxTurtle:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')

        firstLeg = '<span class=warning--text>|</span><span class=error--text>_</span>'
        secondLeg = firstLeg + '<span class=warning--text>|</span>'
        self.logo ='<span class=success--text>R  _____     ____\n'
        self.logo+='E /      \  |  </span><span class=info--text>o</span><span class=success--text> | \n'
        self.logo+='A |       |/ ___/ \n'
        self.logo+='D |_________/     \n'
        self.logo+='Y {first}{second} {first}{second}\n'.format(first=firstLeg, second=secondLeg)

        self.logo_error ='<span class=error--text>E  _ _   _ _\n'
        self.logo_error+='R |_|_|_|_|_|\n'
        self.logo_error+='R |         \____\n'
        self.logo_error+='O |              \ \n'
        self.logo_error+='R |          |\ <span class=secondary--text>X</span> |\n'
        self.logo_error+='! \_________/ |___|</span>\n'

        self.AFC.gcode.register_mux_command('CALIBRATE_AFC', None, None, self.cmd_CALIBRATE_AFC, desc=self.cmd_CALIBRATE_AFC_help)

    def system_Test(self, UNIT, LANE, delay):
        msg = ''
        succeeded = True
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
        try: CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        except:
            error_string = 'Error: No config found for extruder: ' + CUR_LANE.extruder_name + ' in [AFC_stepper ' + CUR_LANE.name + ']. Please make sure [AFC_extruder ' + CUR_LANE.extruder_name + '] config exists in AFC_Hardware.cfg'
            self.AFC.AFC_error(error_string, False)
            return False

        # Run test reverse/forward on each lane
        CUR_LANE.extruder_stepper.sync_to_extruder(None)
        CUR_LANE.move( 5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + delay)
        CUR_LANE.move( -5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)

        if CUR_LANE.prep_state == False:
            if CUR_LANE.load_state == False:
                self.AFC.afc_led(self.AFC.led_not_ready, CUR_LANE.led_index)
                msg += 'EMPTY READY FOR SPOOL'
            else:
                self.AFC.afc_led(self.AFC.led_fault, CUR_LANE.led_index)
                CUR_LANE.status = None
                msg +="<span class=error--text> NOT READY</span>"
                CUR_LANE.do_enable(False)
                msg = '<span class=error--text>CHECK FILAMENT Prep: False - Load: True</span>'
                succeeded = False

        else:
            CUR_LANE.hub_load = self.AFC.lanes[UNIT][LANE]['hub_loaded'] # Setting hub load state so it can be retained between restarts
            self.AFC.afc_led(self.AFC.led_ready, CUR_LANE.led_index)
            msg +="<span class=success--text>LOCKED</span>"
            if CUR_LANE.load_state == False:
                msg +="<span class=error--text> NOT LOADED</span>"
                self.AFC.afc_led(self.AFC.led_not_ready, CUR_LANE.led_index)
                succeeded = False
            else:
                CUR_LANE.status = 'Loaded'
                msg +="<span class=success--text> AND LOADED</span>"

                if self.AFC.lanes[UNIT][CUR_LANE.name]['tool_loaded']:
                    if CUR_EXTRUDER.tool_start_state == True or CUR_EXTRUDER.tool_start == "buffer":
                        if self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded'] == CUR_LANE.name:
                            CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
                            msg +="<span class=primary--text> in ToolHead</span>"
                            if CUR_EXTRUDER.tool_start == "buffer":
                                msg += "<span class=warning--text>\n Ram sensor enabled, confirm tool is loaded</span>"
                            self.AFC.SPOOL.set_active_spool(self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'])
                            self.AFC.afc_led(self.AFC.led_tool_loaded, CUR_LANE.led_index)
                            if len(self.AFC.extruders) == 1:
                                self.AFC.current = CUR_LANE.name
                                CUR_EXTRUDER.enable_buffer()
                        else:
                            if CUR_EXTRUDER.tool_start_state == True:
                                msg +="<span class=error--text> error in ToolHead. \nLane identified as loaded in AFC.vars.unit file\n but not identified as loaded in AFC.var.tool file</span>"
                                succeeded = False
                    else:
                        lane_check=self.AFC.ERROR.fix('toolhead',CUR_LANE)  #send to error handling
                        if not lane_check:
                            return False

        self.AFC.TcmdAssign(CUR_LANE)
        CUR_LANE.do_enable(False)
        self.AFC.gcode.respond_info( '{lane_name} tool cmd: {tcmd:3} {msg}'.format(lane_name=CUR_LANE.name.upper(), tcmd=CUR_LANE.map, msg=msg))
        CUR_LANE.set_afc_prep_done()

        return succeeded

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
            for UNIT in self.AFC.lanes.keys():
                if lane_name in self.AFC.lanes[UNIT]:
                    return lane_name

            # If the lane was not found
            self.AFC.gcode.respond_info('{} not found in any unit.'.format(lane_name))
            return None

        # Helper functions for movement and calibration
        def calibrate_hub(CUR_LANE, CUR_HUB):
            hub_pos = 0
            hub_pos = move_until_state(CUR_LANE, lambda: CUR_HUB.state, CUR_HUB.move_dis, tol, short_dis, hub_pos)
            tuned_hub_pos = calc_position(CUR_LANE, lambda: CUR_HUB.state, hub_pos, short_dis, tol)
            return tuned_hub_pos

        def move_until_state(lane, state, move_dis, tolerance, short_move, pos=0):
            while state() == False:
                lane.move(move_dis, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
                pos += move_dis
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)
            while state() == True:
                lane.move(short_move * -1, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                pos -= short_move
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)
            while state() == False:
                lane.move(tolerance, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
                pos += tolerance
            return pos

        def calc_position(lane, state, pos, short_move, tolerance):
            while state():
                lane.move(short_move * -1, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                pos -= short_move
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)
            while not state():
                lane.move(tolerance, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
                pos += tolerance
            return pos

        def calibrate_lane(LANE):
            CUR_LANE = self.printer.lookup_object('AFC_stepper {}'.format(LANE))
            CUR_HUB = self.printer.lookup_object('AFC_hub {}'.format(CUR_LANE.unit))
            if CUR_HUB.state:
                self.AFC.gcode.respond_info('Hub is not clear, check before calibration')
                return False, ""
            if not CUR_LANE.load_state:
                self.AFC.gcode.respond_info('{} not loaded, load before calibration'.format(CUR_LANE.name.upper()))
                return True, ""

            self.AFC.gcode.respond_info('Calibrating {}'.format(CUR_LANE.name.upper()))
            # reset to extruder
            calc_position(CUR_LANE, lambda: CUR_LANE.load_state, 0, short_dis, tol)
            hub_pos = calibrate_hub(CUR_LANE, CUR_HUB)
            if CUR_HUB.state:
                CUR_LANE.move(CUR_HUB.move_dis * -1, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
            CUR_LANE.hub_load = True
            self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['hub_loaded'] = CUR_LANE.hub_load
            CUR_LANE.do_enable(False)
            cal_msg = "\n{} dist_hub: {}".format(CUR_LANE.name.upper(), (hub_pos - CUR_HUB.hub_clear_move_dis))
            return True, cal_msg

        # Determine if a specific lane is provided
        if lanes is not None:
            self.AFC.gcode.respond_info('Starting AFC distance Calibrations')
            cal_msg += 'AFC Calibration distances +/-{}mm'.format(tol)
            cal_msg += '\n<span class=info--text>Update values in AFC_Hardware.cfg</span>'
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
                for UNIT in self.AFC.lanes.keys():
                    for LANE in self.AFC.lanes[UNIT].keys():
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
                cal_msg += '\n<span class=info--text>Update values in AFC_Hardware.cfg</span>'

            lane_to_calibrate = find_lane_to_calibrate(afc_bl)

            if lane_to_calibrate is None:
                return

            lane = lane_to_calibrate
            CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
            CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
            CUR_HUB = self.printer.lookup_object('AFC_hub ' + CUR_LANE.unit)
            self.AFC.gcode.respond_info('Calibrating Bowden Length with {}'.format(CUR_LANE.name.upper()))

            move_until_state(CUR_LANE, lambda: CUR_HUB.state, CUR_HUB.move_dis, tol, short_dis)

            bow_pos = 0
            if CUR_EXTRUDER.tool_start:
                while not CUR_EXTRUDER.tool_start_state:
                    CUR_LANE.move(dis, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
                    bow_pos += dis
                    self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)
                bow_pos = calc_position(CUR_LANE, lambda: CUR_EXTRUDER.tool_start_state, bow_pos, short_dis, tol)
                CUR_LANE.move(bow_pos * -1, self.AFC.long_moves_speed, self.AFC.long_moves_accel, True)
                calibrate_hub(CUR_LANE, CUR_HUB)
                if CUR_HUB.state:
                    CUR_LANE.move(CUR_HUB.move_dis * -1, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                if CUR_EXTRUDER.tool_start == 'buffer':
                    cal_msg += '\n afc_bowden_length: {}'.format(bow_pos - (short_dis * 2))
                else:
                    cal_msg += '\n afc_bowden_length: {}'.format(bow_pos - short_dis)
                CUR_LANE.do_enable(False)
            else:
                self.AFC.gcode.respond_info('CALIBRATE_AFC is not currently supported without tool start sensor')

        self.AFC.save_vars()
        self.AFC.gcode.respond_info(cal_msg)
            
def load_config(config):
    return afcBoxTurtle(config)
