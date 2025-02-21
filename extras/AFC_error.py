# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging
from extras.AFC import State

def load_config(config):
    return afcError(config)

class afcError:
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
        # Constant variable for renaming RESUME macro
        self.BASE_RESUME_NAME       = 'RESUME'
        self.AFC_RENAME_RESUME_NAME = '_AFC_RENAMED_{}_'.format(self.BASE_RESUME_NAME)

        self.AFC.gcode.register_command('RESET_FAILURE', self.cmd_RESET_FAILURE, desc=self.cmd_RESET_FAILURE_help)
        self.AFC.gcode.register_command('AFC_RESUME', self.cmd_AFC_RESUME, desc=self.cmd_AFC_RESUME_help)

    def fix(self, problem, LANE):
        self.pause= True
        self.AFC = self.printer.lookup_object('AFC')
        error_handled = False
        if problem == None:
            self.PauseUserIntervention('Paused for unknown error')
        if problem=='toolhead':
            error_handled = self.ToolHeadFix(LANE)
        else:
            self.PauseUserIntervention(problem)
        if not error_handled:
            self.AFC.FUNCTION.afc_led(self.AFC.led_fault, LANE.led_index)

        return error_handled

    def ToolHeadFix(self, CUR_LANE):
        if CUR_LANE.get_toolhead_sensor_state():   #toolhead has filament
            if CUR_LANE.extruder_obj.lane_loaded == CUR_LANE.name:   #var has right lane loaded
                if CUR_LANE.load_state == False: #Lane has filament
                    self.PauseUserIntervention('Filament not loaded in Lane')
                else:
                    self.PauseUserIntervention('no error detected')
            else:
                self.PauseUserIntervention('laneloaded does not match extruder')

        else: #toolhead empty
            if CUR_LANE.load_state == True: #Lane has filament
                while CUR_LANE.load_state == True:  # slowly back filament up to lane extruder
                    CUR_LANE.move(-5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                while CUR_LANE.load_state == False:  # reload lane extruder
                    CUR_LANE.move(5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)

                CUR_LANE.tool_load = False
                CUR_LANE.loaded_to_hub = False
                CUR_LANE.extruder_obj.lane_loaded = ''
                self.AFC.save_vars()
                self.pause = False
                return True

            else:
                self.PauseUserIntervention('Filament not loaded in Lane')

    def PauseUserIntervention(self,message):
        #pause for user intervention
        self.AFC.gcode._respond_error(message)
        if self.AFC.FUNCTION.is_homed() and not self.AFC.FUNCTION.is_paused():
            self.AFC.save_pos()
            if self.pause:
                self.pause_print()

    def pause_print(self):
        """
        pause_print function verifies that the printer is homed and not currently paused before calling
        the base pause command
        """
        self.set_error_state( True )
        self.AFC.gcode.respond_info ('PAUSING')
        self.AFC.gcode.run_script_from_command('PAUSE')

    def set_error_state(self, state=False):
        logging.warning("AFC debug: setting error state {}".format(state))
        # Only save position on first error state call
        if state == True and self.AFC.error_state == False:
            self.AFC.save_pos()
        self.AFC.error_state = state
        self.AFC.current_state = State.ERROR if state else State.IDLE

    def AFC_error(self, msg, pause=True):
        # Print to logger since respond_raw does not write to logger
        logging.warning(msg)
        # Handle AFC errors
        self.AFC.gcode.respond_raw( "!! {}".format(msg) )
        if pause: self.pause_print()


    cmd_RESET_FAILURE_help = "CLEAR STATUS ERROR"
    def cmd_RESET_FAILURE(self, gcmd):
        """
        This function clears the error state of the AFC system by setting the error state to False.

        Usage: `RESET_FAILURE`
        Example: `RESET_FAILURE`

        Args:
            gcmd: The G-code command object containing the parameters for the command.

        Returns:
            None
        """
        self.set_error_state(False)
        self.pause = False

    cmd_AFC_RESUME_help = "Clear error state and restores position before resuming the print"
    def cmd_AFC_RESUME(self, gcmd):
        """
        This function clears the error state of the AFC system, sets the in_toolchange flag to False,
        runs the resume script, and restores the toolhead position to the last saved position.

        Usage: `AFC_RESUME`
        Example: `AFC_RESUME`

        Args:
            gcmd: The G-code command object containing the parameters for the command.

        Returns:
            None
        """
        self.AFC.in_toolchange = False
        self.AFC.gcode.run_script_from_command(self.AFC_RENAME_RESUME_NAME)

        #The only time our resume should restore position is if there was an error that caused the pause
        if self.AFC.error_state:
            self.set_error_state(False)
            self.AFC.restore_pos()
            self.pause = False

    handle_lane_failure_help = "Get load errors, stop stepper and respond error"
    def handle_lane_failure(self, CUR_LANE, message, pause=True):
        # Disable the stepper for this lane
        CUR_LANE.do_enable(False)
        CUR_LANE.status = 'Error'
        msg = "{} {}".format(CUR_LANE.name, message)
        self.AFC_error(msg, pause)
        self.AFC.FUNCTION.afc_led(self.AFC.led_fault, CUR_LANE.led_index)
