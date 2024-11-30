

class afcError:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')
        self.errorLog= {}
        self.pause= False

        self.gcode.register_command('RESET_FAILURE', self.cmd_CLEAR_ERROR, desc=self.cmd_CLEAR_ERROR_help)
        self.gcode.register_command('AFC_RESUME', self.cmd_AFC_RESUME, desc=self.cmd_AFC_RESUME_help)

        # Constant variable for renaming RESUME macro
        self.AFC_RENAME_RESUME_NAME = '_AFC_RENAMED_RESUME_'

    def fix(self, problem, LANE=None):
        self.pause= True
        self.AFC = self.printer.lookup_object('AFC')
        self.set_error_state(True)
        error_handled = False
        if problem == None:
            self.PauseUserIntervention('Paused for unknown error')
        if problem=='toolhead':
            error_handled = self.ToolHeadFix(LANE)
        else:
            self.PauseUserIntervention(problem)

        return error_handled

    def ToolHeadFix(self, CUR_LANE):
        CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        if CUR_EXTRUDER.tool_start_state:   #toolhead has filament
            if self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded'] == CUR_LANE.name:   #var has right lane loaded
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
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = False
                self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded']= ''
                self.AFC.save_vars()
                return True

            else:
                self.PauseUserIntervention('Filament not loaded in Lane')

    def PauseUserIntervention(self,message):
        #pause for user intervention
        self.gcode.respond_info(message)
        if self.AFC.is_homed() and not self.AFC.is_paused():
            self.AFC.save_pos()
            self.gcode.respond_info ('PAUSING')
            if self.pause: self.pause_print()

    def set_error_state(self, state):
        # Only save position on first error state call
        if state == True and self.AFC.failure == False:
            self.AFC.save_pos()
        self.AFC.failure = state

    def AFC_error(self, msg, pause=True):
        # Handle AFC errors
        self.gcode._respond_error( msg )


    cmd_CLEAR_ERROR_help = "CLEAR STATUS ERROR"
    def cmd_CLEAR_ERROR(self, gcmd):
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
        self.set_error_state(False)
        self.in_toolchange = False
        self.gcode.run_script_from_command(self.AFC_RENAME_RESUME_NAME)
        self.restore_pos()

    handle_lane_failure_help = "Get load errors, stop stepper and respond error"
    def handle_lane_failure(self, CUR_LANE, message, pause=True):
        # Disable the stepper for this lane
        CUR_LANE.do_enable(False)
        msg = (CUR_LANE.name.upper() + ' NOT READY' + message)
        self.AFC_error(msg, pause)
        self.afc_led(self.led_fault, CUR_LANE.led_index)

def load_config(config):
    return afcError(config)

