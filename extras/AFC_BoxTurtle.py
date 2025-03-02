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
        self.logger.info('Calibrating Bowden Length with {}'.format(CUR_LANE.name))
        self.move_until_state(CUR_LANE, lambda: CUR_HUB.state, CUR_HUB.move_dis, tol, CUR_LANE.short_move_dis)
        bow_pos = 0
        if CUR_EXTRUDER.tool_start:
            # Clear until toolhead sensor is clear
            while not CUR_LANE.get_toolhead_pre_sensor_state():
                CUR_LANE.move(dis, self.short_moves_speed, self.short_moves_accel)
                bow_pos += dis
                self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)

            bow_pos = self.calc_position(CUR_LANE, lambda: CUR_LANE.get_toolhead_pre_sensor_state(), bow_pos, CUR_LANE.short_move_dis, tol)
            CUR_LANE.move(bow_pos * -1, CUR_LANE.long_moves_speed, CUR_LANE.long_moves_accel, True)

            self.calibrate_hub( CUR_LANE, tol)

            if CUR_HUB.state:
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
        else:
            self.logger.info('CALIBRATE_AFC is not currently supported without tool start sensor')
        self.AFC.save_vars()

    # Helper functions for movement and calibration
    def calibrate_hub(self, CUR_LANE, tol):
        hub_pos = 0
        hub_pos = self.move_until_state(CUR_LANE, lambda: CUR_LANE.hub_obj.state, CUR_LANE.hub_obj.move_dis, tol, CUR_LANE.short_move_dis, hub_pos)
        tuned_hub_pos = self.calc_position(CUR_LANE, lambda: CUR_LANE.hub_obj.state, hub_pos, CUR_LANE.short_move_dis, tol)
        return tuned_hub_pos

    def move_until_state(self, CUR_LANE, state, move_dis, tolerance, short_move, pos=0):
        while state() == False:
            CUR_LANE.move(move_dis, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
            pos += move_dis
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)
        while state() == True:
            CUR_LANE.move(short_move * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
            pos -= short_move
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)
        while state() == False:
            CUR_LANE.move(tolerance, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
            pos += tolerance
        return pos

    def calc_position(self,CUR_LANE, state, pos, short_move, tolerance):
        while state():
            CUR_LANE.move(short_move * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)
            pos -= short_move
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + 0.1)
        while not state():
            CUR_LANE.move(tolerance, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel)
            pos += tolerance
        return pos

    def calibrate_lane(self, CUR_LANE, tol):
        CUR_HUB = CUR_LANE.hub_obj
        if CUR_HUB.state:
            self.logger.info('Hub is not clear, check before calibration')
            return False, ""
        if not CUR_LANE.load_state:
            self.logger.info('{} not loaded, load before calibration'.format(CUR_LANE.name))
            return True, ""

        self.logger.info('Calibrating {}'.format(CUR_LANE.name))
        # reset to extruder
        self.calc_position(CUR_LANE, lambda: CUR_LANE.load_state, 0, CUR_LANE.short_move_dis, tol)
        hub_pos = self.calibrate_hub(CUR_LANE, tol)
        if CUR_HUB.state:
            CUR_LANE.move(CUR_HUB.move_dis * -1, CUR_LANE.short_moves_speed, CUR_LANE.short_moves_accel, True)

        cal_dist = hub_pos - CUR_HUB.hub_clear_move_dis
        cal_msg = "\n{} dist_hub: New: {} Old: {}".format(CUR_LANE.name, cal_dist, CUR_LANE.dist_hub)
        CUR_LANE.loaded_to_hub  = True
        CUR_LANE.do_enable(False)
        CUR_LANE.dist_hub = cal_dist
        self.AFC.FUNCTION.ConfigRewrite(CUR_LANE.fullname, "dist_hub", cal_dist, cal_msg)
        return True, cal_msg

def load_config_prefix(config):
    return afcBoxTurtle(config)