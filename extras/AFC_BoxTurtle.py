# Armored Turtle Automated Filament Control
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from configparser import Error as error
try:
    from extras.AFC_unit import afcUnit
except:
    raise error("Error trying to import AFC_unit, please rerun install-afc.sh script in your AFC-Klipper-Add-On directory then restart klipper")

class afcBoxTurtle(afcUnit):
    def __init__(self, config):
        super().__init__(config)
        self.type = config.get('type', 'Box_Turtle')

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        super().handle_connect()

        firstLeg = '<span class=warning--text>|</span><span class=error--text>_</span>'
        secondLeg = firstLeg + '<span class=warning--text>|</span>'
        self.logo ='<span class=success--text>R  _____     ____\n'
        self.logo+='E /      \  |  </span><span class=info--text>o</span><span class=success--text> | \n'
        self.logo+='A |       |/ ___/ \n'
        self.logo+='D |_________/     \n'
        self.logo+='Y {first}{second} {first}{second}\n'.format(first=firstLeg, second=secondLeg)
        self.logo+= '  ' + self.name + '\n'

        self.logo_error ='<span class=error--text>E  _ _   _ _\n'
        self.logo_error+='R |_|_|_|_|_|\n'
        self.logo_error+='R |         \____\n'
        self.logo_error+='O |              \ \n'
        self.logo_error+='R |          |\ <span class=secondary--text>X</span> |\n'
        self.logo_error+='! \_________/ |___|</span>\n'
        self.logo_error+= '  ' + self.name + '\n'

    def system_Test(self, CUR_LANE, delay, assignTcmd, enable_movement):
        msg = ''
        succeeded = True

        # Run test reverse/forward on each lane
        CUR_LANE.unsync_to_extruder(False)
        if enable_movement:
            CUR_LANE.move( 5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + delay)
            CUR_LANE.move( -5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
        else:
            self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.7)

        if CUR_LANE.prep_state == False:
            if CUR_LANE.load_state == False:
                self.AFC.FUNCTION.afc_led(CUR_LANE.led_not_ready, CUR_LANE.led_index)
                msg += 'EMPTY READY FOR SPOOL'
            else:
                self.AFC.FUNCTION.afc_led(CUR_LANE.led_fault, CUR_LANE.led_index)
                msg +="<span class=error--text> NOT READY</span>"
                CUR_LANE.do_enable(False)
                msg = '<span class=error--text>CHECK FILAMENT Prep: False - Load: True</span>'
                succeeded = False

        else:
            self.AFC.FUNCTION.afc_led(CUR_LANE.led_ready, CUR_LANE.led_index)
            msg +="<span class=success--text>LOCKED</span>"
            if CUR_LANE.load_state == False:
                msg +="<span class=error--text> NOT LOADED</span>"
                self.AFC.FUNCTION.afc_led(CUR_LANE.led_not_ready, CUR_LANE.led_index)
                succeeded = False
            else:
                CUR_LANE.status = 'Loaded'
                msg +="<span class=success--text> AND LOADED</span>"

                if CUR_LANE.tool_loaded:
                    if CUR_LANE.get_toolhead_pre_sensor_state() == True or CUR_LANE.extruder_obj.tool_start == "buffer" or CUR_LANE.extruder_obj.tool_end_state:
                        if CUR_LANE.extruder_obj.lane_loaded == CUR_LANE.name:
                            self.AFC.current = CUR_LANE.name
                            CUR_LANE.sync_to_extruder()
                            msg +="<span class=primary--text> in ToolHead</span>"
                            if CUR_LANE.extruder_obj.tool_start == "buffer":
                                msg += "<span class=warning--text>\n Ram sensor enabled, confirm tool is loaded</span>"

                            if self.AFC.FUNCTION.get_current_lane() == CUR_LANE.name:
                                self.AFC.SPOOL.set_active_spool(CUR_LANE.spool_id)
                                self.AFC.FUNCTION.afc_led(CUR_LANE.led_tool_loaded, CUR_LANE.led_index)
                                CUR_LANE.status = 'Tooled'

                            CUR_LANE.enable_buffer()
                        else:
                            if CUR_LANE.get_toolhead_pre_sensor_state() == True or CUR_LANE.extruder_obj.tool_end_state:
                                msg +="<span class=error--text> error in ToolHead. \nLane identified as loaded \n but not identified as loaded in extruder</span>"
                                succeeded = False
                    else:
                        lane_check=self.AFC.ERROR.fix('toolhead',CUR_LANE)  #send to error handling
                        if not lane_check:
                            return False

        if assignTcmd: self.AFC.FUNCTION.TcmdAssign(CUR_LANE)
        CUR_LANE.do_enable(False)
        self.logger.info( '{lane_name} tool cmd: {tcmd:3} {msg}'.format(lane_name=CUR_LANE.name, tcmd=CUR_LANE.map, msg=msg))
        CUR_LANE.set_afc_prep_done()

        return succeeded

    def calibrate_bowden(self, CUR_LANE, dis, tol):
        CUR_EXTRUDER = CUR_LANE.extruder_obj
        CUR_HUB = CUR_LANE.hub_obj
        self.logger.raw('Calibrating Bowden Length with {}'.format(CUR_LANE.name))
        # move to hub and retrieve that distance, the checkpoint returned and if successful
        hub_pos, checkpoint, success = self.move_until_state(CUR_LANE, lambda: CUR_HUB.state, CUR_HUB.move_dis, tol,
                                                     CUR_LANE.short_move_dis, 0, CUR_LANE.dist_hub + 200, "Moving to hub")

        if not success:
            # if movement does not suceed fault and return values to calibration macro
            msg = 'Failed {} after {}mm'.format(checkpoint, hub_pos)
            return False, msg, hub_pos

        bow_pos = 0
        if CUR_EXTRUDER.tool_start:
            # if tool_start is defined move and confirm distance
            while not CUR_LANE.get_toolhead_pre_sensor_state():
                fault_dis = CUR_HUB.afc_bowden_length + 500
                CUR_LANE.move(dis, self.short_moves_speed, self.short_moves_accel)
                bow_pos += dis
                self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)
                if bow_pos >= fault_dis:
                    # fault if move to bowden length does not reach toolhead sensor return to calibration macro
                    msg = 'while moving to toolhead. Failed after {}mm'.format(bow_pos)
                    msg += '\n if filament stopped short of the toolhead sensor/ramming during calibration'
                    msg += '\n use the following command to increase bowden length'
                    msg += '\n SET_BOWDEN_LENGTH HUB={} LENGTH=+(distance the filament was short from the toolhead)'.format(CUR_HUB.name)
                    return False, msg, bow_pos

            if CUR_EXTRUDER.tool_start != 'buffer':
                # is using ramming, only use first trigger of sensor
                bow_pos, checkpoint, success = self.calc_position(CUR_LANE, lambda: CUR_LANE.get_toolhead_pre_sensor_state(), bow_pos,
                                                        CUR_LANE.short_move_dis, tol, 100, "retract from toolhead sensor")

            if not success:
                # fault if check is not successful
                msg = 'Failed {} after {}mm'.format(checkpoint, bow_pos)
                return False, msg, bow_pos

            CUR_LANE.move(bow_pos * -1, CUR_LANE.long_moves_speed, CUR_LANE.long_moves_accel, True)

            success, message, hub_dis = self.calibrate_hub(CUR_LANE, tol)

            if not success:
                return False, message, hub_dis

            if CUR_HUB.state:
                # reset at hub
                CUR_LANE.move(CUR_HUB.move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)

            bowden_dist = 0
            if CUR_EXTRUDER.tool_start == 'buffer':
                bowden_dist = bow_pos - (CUR_LANE.short_move_dis * 2)
            else:
                bowden_dist = bow_pos - CUR_LANE.short_move_dis

            cal_msg = '\n afc_bowden_length: New: {} Old: {}'.format(bowden_dist, CUR_LANE.hub_obj.afc_bowden_length)
            CUR_LANE.hub_obj.afc_bowden_length = bowden_dist
            self.AFC.FUNCTION.ConfigRewrite(CUR_HUB.fullname, "afc_bowden_length", bowden_dist, cal_msg)
            CUR_LANE.do_enable(False)
            self.AFC.save_vars()
            return True, "afc_bowden_length successful", bowden_dist
        else:
            self.logger.info('CALIBRATE_AFC is not currently supported without tool start sensor')

    # Helper functions for movement and calibration
    def calibrate_hub(self, CUR_LANE, tol):
        hub_pos = 0
        msg = ''
        hub_fault_dis = CUR_LANE.dist_hub + 150
        checkpoint = 'hub calibration {}'.format(CUR_LANE.name)
        # move until hub sensor is triggered and get information
        hub_pos, checkpoint, success = self.move_until_state(CUR_LANE, lambda: CUR_LANE.hub_obj.state, CUR_LANE.hub_obj.move_dis,
                                                             tol, CUR_LANE.short_move_dis, hub_pos, hub_fault_dis, checkpoint)

        if not success:
            # fault if check is not successful
            msg = 'Failed to calibrate dist_hub for {}. Failed after {}mm'.format(CUR_LANE.name, hub_fault_dis)
            msg += '\n if filament stopped short of the hub during calibration use the following command to increase dist_hub value'
            msg += '\n SET_HUB_DIST LANE={} LENGTH=+(distance the filament was short from the hub)'.format(CUR_LANE.name)
            return False, msg, hub_pos

        hub_dist = CUR_LANE.dist_hub + 500
        # verify hub distance
        tuned_hub_pos, checkpoint, success = self.calc_position(CUR_LANE, lambda: CUR_LANE.hub_obj.state, hub_pos,
                                            CUR_LANE.short_move_dis, tol, hub_dist, checkpoint)

        if not success:
            # fault if check is not successful
            msg = 'failed {} after {}mm'.format(checkpoint, tuned_hub_pos)
            return False, msg, tuned_hub_pos

        # when successful return values to calibration macro
        return True, msg, tuned_hub_pos

    def move_until_state(self, CUR_LANE, state, move_dis, tolerance, short_move, pos=0, fault_dis=250, checkpoint=None):
        # moves filament until specified sensor, returns values for further czlibration
        while state() == False:
            CUR_LANE.move(move_dis, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
            pos += move_dis
            if pos >= fault_dis:
                # return if pos exceeds fault_dis
                return fault_dis, checkpoint, False
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)

        state_retracts = 0
        while state() == True:
            # retract off of sensor
            state_retracts =+ 1
            CUR_LANE.move(short_move * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
            pos -= short_move
            check_p = '{} switch did not go false, reset lane and check switch'.format(checkpoint)
            if state_retracts >= 4:
                # fault if it takes more than 4 attempts
                f_dis = short_move * 4
                return f_dis, check_p, False
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)

        tol_checks = 0
        while state() == False:
            # move back to sensor in short steps
            tol_checks += 1
            CUR_LANE.move(tolerance, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
            pos += tolerance
            check_p = '{} switch failed to become true during tolerance check, reset lane and check switch'.format(checkpoint)
            if tol_checks >= 15:
                # fault if tol_checks exceed 15
                return fault_dis, check_p, False

        return pos, checkpoint, True

    def calc_position(self, CUR_LANE, state, pos, short_move, tolerance, fault_dis=250, checkpoint=None):
        # move off and back on to sensor to calculate end position of calibration
        check_pos = 0
        while state():
            # retract from sensor
            CUR_LANE.move(short_move * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
            pos -= short_move
            check_pos -= short_move
            if abs(check_pos) >= fault_dis:
                # fault if absolute value you check_pos exceeds fault_dis
                return fault_dis, checkpoint, False
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)

        checkpoint += ', tolerance check,'
        tol_checks = 0
        while not state():
            #move back to sensor to confirm distance
            tol_checks += 1
            CUR_LANE.move(tolerance, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
            pos += tolerance

            if tol_checks >= 15:
                # fault if tol_checks exceeds 15
                return pos, checkpoint, False

        return pos, checkpoint, True

    def calibrate_lane(self, CUR_LANE, tol):
        # function to calibrate distance from secondary extruder to hub
        CUR_HUB = CUR_LANE.hub_obj
        if CUR_HUB.state:
            msg = 'Hub is not clear, check before calibration'
            return False, msg, 0
        if not CUR_LANE.load_state:
            msg = '{} not loaded, load before calibration'.format(CUR_LANE.name)
            return False, msg, 0
        if not CUR_LANE.prep_state:
            msg = '{} is loaded but not prepped, check prep before calibration'.format(CUR_LANE.name)
            return False, msg, 0

        self.logger.info('Calibrating {}'.format(CUR_LANE.name))
        CUR_LANE.status = "calibrating"
        # reset to extruder
        pos, checkpoint, success = self.calc_position(CUR_LANE, lambda: CUR_LANE.load_state, 0, CUR_LANE.short_move_dis,
                                              tol, CUR_LANE.dist_hub + 100, "retract to extruder")

        if not success:
            msg = 'Lane failed to calibrate {} after {}mm'.format(checkpoint, pos)
            CUR_LANE.status = None
            CUR_LANE.unit_obj.return_to_home()
            return False, msg, 0

        else:
            success, message, hub_pos = self.calibrate_hub(CUR_LANE, tol)

            if not success:
                CUR_LANE.status = None
                CUR_LANE.unit_obj.return_to_home()
                return False, message, hub_pos

            if CUR_HUB.state:
                CUR_LANE.move(CUR_HUB.move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)

            cal_dist = hub_pos - CUR_HUB.hub_clear_move_dis
            cal_msg = "\n{} dist_hub: New: {} Old: {}".format(CUR_LANE.name, cal_dist, CUR_LANE.dist_hub)
            CUR_LANE.loaded_to_hub  = True
            CUR_LANE.do_enable(False)
            CUR_LANE.dist_hub = cal_dist
            self.AFC.FUNCTION.ConfigRewrite(CUR_LANE.fullname, "dist_hub", cal_dist, cal_msg)
            CUR_LANE.status = None
            CUR_LANE.unit_obj.return_to_home()
            return True, cal_msg, cal_dist

def load_config_prefix(config):
    return afcBoxTurtle(config)