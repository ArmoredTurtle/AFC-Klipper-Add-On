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
        self.AFC            = self.printer.lookup_object('AFC')
        self.pause_resume   = self.printer.lookup_object("pause_resume")
        self.logger = self.AFC.logger
        # Constant variable for renaming RESUME macro
        self.BASE_RESUME_NAME       = 'RESUME'
        self.AFC_RENAME_RESUME_NAME = '_AFC_RENAMED_{}_'.format(self.BASE_RESUME_NAME)
        self.BASE_PAUSE_NAME        = 'PAUSE'
        self.AFC_RENAME_PAUSE_NAME  = '_AFC_RENAMED_{}_'.format(self.BASE_PAUSE_NAME)

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
        if CUR_LANE.get_toolhead_pre_sensor_state():   #toolhead has filament
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
        self.logger.error(message)
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
        self.logger.info ('PAUSING')
        self.AFC.gcode.run_script_from_command('PAUSE')
        self.logger.debug("After User Pause")
        self.AFC.FUNCTION.log_toolhead_pos()

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
        self.logger.error( "{}".format(msg) )
        if pause: self.pause_print()


    cmd_RESET_FAILURE_help = "CLEAR STATUS ERROR"
    def cmd_RESET_FAILURE(self, gcmd):
        """
        This function clears the error state of the AFC system by setting the error state to False.

        Usage
        -----
        `RESET_FAILURE`

        Example
        -----
        `RESET_FAILURE`
        """
        self.reset_failure()

    def reset_failure(self):
        """
        Common function to reset error_state, pause, and position_saved variables
        """
        self.logger.debug("Resetting failures")
        self.set_error_state(False)
        self.pause              = False
        self.AFC.position_saved = False
        self.AFC.in_toolchange  = False

    cmd_AFC_RESUME_help = "Clear error state and restores position before resuming the print"
    def cmd_AFC_RESUME(self, gcmd):
        """
        During the PREP phase of startup, the user's RESUME macro is renamed and replaced with AFC_RESUME.
        This function clears the error state of the AFC system, sets the in_toolchange flag to False,
        runs the resume script, and restores the toolhead position to the last saved position.

        This is not a macro that should normally need to be called by the user.

        Usage
        -----
        `AFC_RESUME`

        Example
        -----
        ```
        AFC_RESUME
        ```
        """
        self.AFC.in_toolchange = False
        if not self.AFC.FUNCTION.is_paused():
            self.logger.debug("AFC_RESUME: Printer not paused, not executing resume code")
            return

        # Save current pause state
        temp_is_paused = self.AFC.FUNCTION.is_paused()
        curr_pos = self.AFC.toolhead.get_position()

        # Verify that printer is in absolute mode
        self.AFC.FUNCTION.check_absolute_mode("AFC_RESUME")

        # Check if current position is below saved gcode position, if its lower first raise z above last saved
        #   position so that toolhead does not crash into part
        if (curr_pos[2] <= self.AFC.last_gcode_position[2]):
            self.AFC._move_z_pos( self.AFC.last_gcode_position[2] + self.AFC.z_hop )

        self.logger.debug("AFC_RESUME: Before User Restore")
        self.AFC.FUNCTION.log_toolhead_pos()
        self.AFC.gcode.run_script_from_command("{macro_name} {user_params}".format(macro_name=self.AFC_RENAME_RESUME_NAME, user_params=gcmd.get_raw_command_parameters()))

        # The only time our resume should restore position is if there was an error that caused the pause
        if self.AFC.error_state or temp_is_paused or self.AFC.position_saved:
            self.set_error_state(False)
            self.AFC.restore_pos(False)
            self.pause = False

        self.logger.debug("RESUME-Error State: {}, Is Paused {}, Position_saved {}, in toolchange: {}".format(
            self.AFC.error_state, self.AFC.FUNCTION.is_paused(), self.AFC.position_saved, self.AFC.in_toolchange ))

    cmd_AFC_PAUSE_help = "Pauses print, raises z by z-hop amount, and then calls users pause macro"
    def cmd_AFC_PAUSE(self, gcmd):
        """
        During the PREP phase of startup, the user's PAUSE macro is renamed and replaced with AFC_PAUSE.
        This function pauses the print, raises the Z axis by the z-hop amount, and then calls the user's pause macro.

        This is not a macro that should normally need to be called by the user.

        Usage
        -----
        `AFC_PAUSE`

        Example
        -----
        ```
        AFC_PAUSE
        ```
        """
        # Check to make sure printer is not already paused
        if not self.AFC.FUNCTION.is_paused():
            self.logger.debug("AFC_PAUSE: Pausing")
            # Save position
            self.AFC.save_pos()
            # Need to pause as soon as possible to stop more gcode from executing, this needs to be done before movement in Z
            self.pause_resume.send_pause_command()
            # Verify that printer is in absolute mode
            self.AFC.FUNCTION.check_absolute_mode("AFC_PAUSE")
            # Move Z up by z-hop value
            self.AFC._move_z_pos( self.AFC.last_gcode_position[2] + self.AFC.z_hop )
            # Call users PAUSE
            self.AFC.gcode.run_script_from_command("{macro_name} {user_params}".format(macro_name=self.AFC_RENAME_PAUSE_NAME, user_params=gcmd.get_raw_command_parameters()))
            # Set Idle timeout to 10 hours
            self.AFC.gcode.run_script_from_command("SET_IDLE_TIMEOUT TIMEOUT=36000")
        else:
            self.logger.debug("AFC_PAUSE: Not Pausing")

        self.logger.debug("PAUSE-Error State: {}, Is Paused {}, Position_saved {}, in toolchange: {}".format(
            self.AFC.error_state, self.AFC.FUNCTION.is_paused(), self.AFC.position_saved, self.AFC.in_toolchange ))


    handle_lane_failure_help = "Get load errors, stop stepper and respond error"
    def handle_lane_failure(self, CUR_LANE, message, pause=True):
        # Disable the stepper for this lane
        CUR_LANE.do_enable(False)
        CUR_LANE.status = 'Error'
        msg = "{} {}".format(CUR_LANE.name, message)
        self.AFC_error(msg, pause)
        self.AFC.FUNCTION.afc_led(self.AFC.led_fault, CUR_LANE.led_index)
