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

    def TOOL_LOAD(self, CUR_LANE):
        """
        This function handles the loading of a specified lane into the tool. It performs
        several checks and movements to ensure the lane is properly loaded.

        Usage: `TOOL_LOAD LANE=<lane>`
        Example: `TOOL_LOAD LANE=leg1`

        Args:
            CUR_LANE: The lane object to be loaded into the tool.

        Returns:
            bool: True if load was successful, False if an error occurred.
        """
        if CUR_LANE is None:
            # Exit early if no lane is provided.
            return False

        # Check if the bypass filament sensor is triggered; abort loading if filament is already present.
        try:
            bypass = self.printer.lookup_object('filament_switch_sensor bypass').runout_helper
            if bypass.filament_present:
                self.gcode.respond_info("Filament loaded in bypass, not doing tool load")
                self.bypass=True
                return False
            else:
                self.bypass=False
        except:
            bypass = None
        self.gcode.respond_info("Loading {}".format(CUR_LANE.name))

        # Lookup extruder and hub objects associated with the lane.
        CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        CUR_HUB = self.printer.lookup_object('AFC_hub '+ CUR_LANE.unit)
        # Prepare extruder and heater.
        extruder = self.toolhead.get_extruder()
        self.heater = extruder.get_heater()

        # Set the lane status to 'loading' and activate the loading LED.
        CUR_LANE.status = 'loading'
        self.afc_led(self.led_loading, CUR_LANE.led_index)

        # Check if the lane is in a state ready to load and hub is clear.
        if CUR_LANE.load_state and not CUR_HUB.state:
            # Heat the extruder if it is below the minimum extrusion temperature.
            if not self.heater.can_extrude:
                pheaters = self.printer.lookup_object('heaters')
                if self.heater.target_temp <= self.heater.min_extrude_temp:
                    self.gcode.respond_info('Extruder below min_extrude_temp, heating to 5 degrees above min.')
                    pheaters.set_temperature(extruder.get_heater(), self.heater.min_extrude_temp + 5, wait=True)

            # Enable the lane for filament movement.
            CUR_LANE.do_enable(True)

            # Move filament to the hub if it's not already loaded there.
            if not CUR_LANE.hub_load:
                CUR_LANE.move(CUR_LANE.dist_hub, CUR_LANE.dist_hub_move_speed, CUR_LANE.dist_hub_move_accel, CUR_LANE.dist_hub > 200)

            CUR_LANE.hub_load = True
            hub_attempts = 0

            # Ensure filament moves past the hub.
            while not CUR_HUB.state:
                if hub_attempts == 0:
                    CUR_LANE.move(CUR_HUB.move_dis, self.short_moves_speed, self.short_moves_accel)
                else:
                    CUR_LANE.move(self.short_move_dis, self.short_moves_speed, self.short_moves_accel)
                hub_attempts += 1
                if hub_attempts > 20:
                    message = ('PAST HUB, CHECK FILAMENT PATH\n||=====||==>--||-----||\nTRG   LOAD   HUB   TOOL')
                    self.ERROR.handle_lane_failure(CUR_LANE, message)
                    return False

            # Move filament towards the toolhead.
            CUR_LANE.move(CUR_HUB.afc_bowden_length, self.long_moves_speed, self.long_moves_accel, True)

            # Ensure filament reaches the toolhead.
            tool_attempts = 0
            if CUR_EXTRUDER.tool_start:
                while not CUR_EXTRUDER.tool_start_state:
                    tool_attempts += 1
                    CUR_LANE.move(self.short_move_dis, CUR_EXTRUDER.tool_load_speed, self.long_moves_accel)
                    if tool_attempts > 20:
                        message = ('FAILED TO LOAD ' + CUR_LANE.name.upper() + ' TO TOOL, CHECK FILAMENT PATH\n||=====||====||==>--||\nTRG   LOAD   HUB   TOOL')
                        self.ERROR.handle_lane_failure(CUR_LANE, message)
                        return False

            # Synchronize lane's extruder stepper and finalize tool loading.
            CUR_LANE.status = 'Tooled'
            CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)

            # Adjust tool position for loading.
            pos = self.toolhead.get_position()
            pos[3] += CUR_EXTRUDER.tool_stn
            self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_load_speed)
            self.toolhead.wait_moves()

            # Check if ramming is enabled, if it is go through ram load sequence.
            # Lane will load until Advance sensor is True
            # After the tool_stn distance the lane will retract off the sensor to confirm load and reset buffer
            if CUR_EXTRUDER.tool_start == "buffer":
                CUR_LANE.extruder_stepper.sync_to_extruder(None)
                load_checks = 0
                while CUR_EXTRUDER.tool_start_state == True:
                    CUR_LANE.move( self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel )
                    load_checks += 1
                    self.reactor.pause(self.reactor.monotonic() + 0.1)
                    if load_checks > self.tool_max_load_checks:
                        msg = ''
                        msg += "Buffer did not become compressed after {} short moves.\n".format(self.tool_max_load_checks)
                        msg += "Tool may not be loaded"
                        self.gcode.respond_info("<span class=warning--text>{}</span>".format(msg))
                        break
                CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
            # Update tool and lane status.
            self.printer.lookup_object('AFC_stepper ' + CUR_LANE.name).status = 'tool'
            self.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = True
            self.current = CUR_LANE.name
            CUR_EXTRUDER.enable_buffer()

            # Activate the tool-loaded LED and handle filament operations if enabled.
            self.afc_led(self.led_tool_loaded, CUR_LANE.led_index)
            if self.poop:
                self.gcode.run_script_from_command(self.poop_cmd)
                if self.wipe:
                    self.gcode.run_script_from_command(self.wipe_cmd)
            if self.kick:
                self.gcode.run_script_from_command(self.kick_cmd)
            if self.wipe:
                self.gcode.run_script_from_command(self.wipe_cmd)

            # Update lane and extruder state for tracking.
            self.lanes[CUR_LANE.unit][CUR_LANE.name]['hub_loaded'] = True
            self.extruders[CUR_LANE.extruder_name]['lane_loaded'] = CUR_LANE.name
            self.SPOOL.set_active_spool(self.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'])
            self.afc_led(self.led_tool_loaded, CUR_LANE.led_index)
            self.save_vars()
        else:
            # Handle errors if the hub is not clear or the lane is not ready for loading.
            if CUR_HUB.state:
                message = ('HUB NOT CLEAR TRYING TO LOAD ' + CUR_LANE.name.upper() + '\n||-----||----|x|-----||\nTRG   LOAD   HUB   TOOL')
                self.ERROR.handle_lane_failure(CUR_LANE, message)
                return False
            if not CUR_LANE.load_state:
                message = (CUR_LANE.name.upper() + ' NOT READY\n||==>--||----||-----||\nTRG   LOAD   HUB   TOOL')
                self.ERROR.handle_lane_failure(CUR_LANE, message)
                return False

        return True

    def TOOL_UNLOAD(self, CUR_LANE):
        """
        This function handles the unloading of a specified lane from the tool. It performs
        several checks and movements to ensure the lane is properly unloaded.

        Usage: `TOOL_UNLOAD LANE=<lane>`
        Example: `TOOL_UNLOAD LANE=leg1`
        Args:
            CUR_LANE: The lane object to be unloaded from the tool.

        Returns:
            bool: True if unloading was successful, False if an error occurred.
        """
        if CUR_LANE is None:
            # If no lane is provided, exit the function early with a failure.
            return False

        self.gcode.respond_info("Unloading {}".format(CUR_LANE.name))
        # Lookup current extruder and hub objects using the lane's information.
        CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        CUR_HUB = self.AFC.get_hub(CUR_LANE.unit)

        # Quick pull to prevent oozing.
        pos = self.toolhead.get_position()
        pos[3] -= 2
        self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
        self.toolhead.wait_moves()

        # Perform Z-hop to avoid collisions during unloading.
        pos[2] += self.z_hop
        self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
        self.toolhead.wait_moves()

        # Prepare the extruder and heater for unloading.
        extruder = self.toolhead.get_extruder()
        self.heater = extruder.get_heater()
        CUR_LANE.status = 'unloading'

        # Disable the buffer if it's active.
        CUR_EXTRUDER.disable_buffer()

        # Activate LED indicator for unloading.
        self.afc_led(self.led_unloading, CUR_LANE.led_index)

        if CUR_LANE.extruder_stepper.motion_queue != CUR_LANE.extruder_name:
            # Synchronize the extruder stepper with the lane.
            CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)

        # Check and set the extruder temperature if below the minimum.
        wait = True
        pheaters = self.printer.lookup_object('heaters')
        if self.heater.target_temp <= self.heater.min_extrude_temp:
            self.gcode.respond_info('Extruder below min_extrude_temp, heating to 5 degrees above min.')
            pheaters.set_temperature(extruder.get_heater(), self.heater.min_extrude_temp + 5, wait)

        # Enable the lane for unloading operations.
        CUR_LANE.do_enable(True)

        # Perform filament cutting and parking if specified.
        if self.tool_cut:
            self.gcode.run_script_from_command(self.tool_cut_cmd)
            if self.park:
                self.gcode.run_script_from_command(self.park_cmd)

        # Form filament tip if necessary.
        if self.form_tip:
            if self.park:
                self.gcode.run_script_from_command(self.park_cmd)
            if self.form_tip_cmd == "AFC":
                self.AFC_tip = self.printer.lookup_object('AFC_form_tip')
                self.AFC_tip.tip_form()
            else:
                self.gcode.run_script_from_command(self.form_tip_cmd)

        # Attempt to unload the filament from the extruder, retrying if needed.
        num_tries = 0
        if CUR_EXTRUDER.tool_start == "buffer":
            # if ramming is enabled, AFC will retract to collapse buffer before unloading
            CUR_LANE.extruder_stepper.sync_to_extruder(None)
            while CUR_EXTRUDER.buffer_trailing == False:
                # attempt to return buffer to trailng pin
                CUR_LANE.move( self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel )
                num_tries += 1
                self.reactor.pause(self.reactor.monotonic() + 0.1)
                if num_tries > self.tool_max_unload_attempts:
                    msg = ''
                    msg += "Buffer did not become compressed after {} short moves.\n".format(self.tool_max_unload_attempts)
                    msg += "Increasing 'tool_max_unload_attempts' may improve loading reliablity"
                    self.gcode.respond_info("<span class=warning--text>{}</span>".format(msg))
                    break
            CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
            pos = self.toolhead.get_position()
            pos[3] -= CUR_EXTRUDER.tool_stn_unload
            self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
            self.toolhead.wait_moves()
        else:
            while CUR_EXTRUDER.tool_start_state:
                num_tries += 1
                if num_tries > self.tool_max_unload_attempts:
                    # Handle failure if the filament cannot be unloaded.
                    message = ('FAILED TO UNLOAD {}. FILAMENT STUCK IN TOOLHEAD.'.format(CUR_LANE.name.upper()))
                    self.ERROR.handle_lane_failure(CUR_LANE, message)
                    return False
                CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
                pos = self.toolhead.get_position()
                pos[3] -= CUR_EXTRUDER.tool_stn_unload
                self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
                self.toolhead.wait_moves()

        # Move filament past the sensor after the extruder, if applicable.
        if CUR_EXTRUDER.tool_sensor_after_extruder > 0:
            pos = self.toolhead.get_position()
            pos[3] -= CUR_EXTRUDER.tool_sensor_after_extruder
            self.toolhead.manual_move(pos, CUR_EXTRUDER.tool_unload_speed)
            self.toolhead.wait_moves()

        # Synchronize and move filament out of the hub.
        CUR_LANE.extruder_stepper.sync_to_extruder(None)
        CUR_LANE.move(CUR_HUB.afc_bowden_length * -1, self.long_moves_speed, self.long_moves_accel, True)

        # Clear toolhead's loaded state for easier error handling later.
        self.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = False
        self.lanes[CUR_LANE.unit][CUR_LANE.name]['hub_loaded'] = CUR_LANE.hub_load
        self.extruders[CUR_LANE.extruder_name]['lane_loaded'] = ''
        self.save_vars()

        # Ensure filament is fully cleared from the hub.
        num_tries = 0
        while CUR_HUB.state:
            CUR_LANE.move(self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel, True)
            num_tries += 1
            if num_tries > (CUR_HUB.afc_bowden_length / self.short_move_dis):
                # Handle failure if the filament doesn't clear the hub.
                message = 'HUB NOT CLEARING'
                self.ERROR.handle_lane_failure(CUR_LANE, message)
                return False

        #Move to make sure hub path is clear based on the move_clear_dis var
        CUR_LANE.move( CUR_HUB.hub_clear_move_dis * -1, self.short_moves_speed, self.short_moves_accel, True)

        # Cut filament at the hub, if configured.
        if CUR_HUB.cut:
            if CUR_HUB.cut_cmd == 'AFC':
                CUR_HUB.hub_cut(CUR_LANE)
            else:
                self.gcode.run_script_from_command(CUR_HUB.cut_cmd)

        # Confirm the hub is clear after the cut.
        while CUR_HUB.state:
            CUR_LANE.move(self.short_move_dis * -1, self.short_moves_speed, self.short_moves_accel, True)
            num_tries += 1
            if num_tries > (CUR_HUB.afc_bowden_length / self.short_move_dis):
                message = 'HUB NOT CLEARING'
                self.ERROR.handle_lane_failure(CUR_LANE, message)
                return False

        # Finalize unloading and reset lane state.
        CUR_LANE.hub_load = True
        self.afc_led(self.led_ready, CUR_LANE.led_index)
        CUR_LANE.status = None
        self.current = None
        CUR_LANE.do_enable(False)

        return True


def load_config(config):
    return afcBoxTurtle(config)