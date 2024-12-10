
from configparser import Error as error

class afc_hub:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

        self.name = config.get_name().split()[-1]
        self.type = config.get('type', None)

        try:
            self.unit = self.printer.load_object(config, "AFC_{}".format(self.type.replace("_", "")))
        except:
            raise error("{} not supported, please remove or fix correct type for AFC_hub in your configuration".format(self.type))

        # HUB Cut variables
        # Next two variables are used in AFC
        self.cut = config.getboolean("cut", False)
        self.cut_cmd = config.get('cut_cmd', None)
        self.cut_servo_name = config.get('cut_servo_name', 'cut')
        self.cut_dist = config.getfloat("cut_dist", 200)
        self.cut_clear = config.getfloat("cut_clear", 120)
        self.cut_min_length = config.getfloat("cut_min_length", 200)
        self.cut_servo_pass_angle = config.getfloat("cut_servo_pass_angle", 0)
        self.cut_servo_clip_angle = config.getfloat("cut_servo_clip_angle", 160)
        self.cut_servo_prep_angle = config.getfloat("cut_servo_prep_angle", 75)
        self.cut_confirm = config.getboolean("cut_confirm", 0)

        self.move_dis = config.getfloat("move_dis", 50)
        self.hub_clear_move_dis = config.getfloat("hub_clear_move_dis", 10)
        self.afc_bowden_length = config.getfloat("afc_bowden_length", 900)
        self.config_bowden_length = self.afc_bowden_length                          # Used by SET_BOWDEN_LENGTH macro
        buttons = self.printer.load_object(config, "buttons")
        self.switch_pin = config.get('switch_pin', None)
        if self.switch_pin is not None:
            self.state = False
            buttons.register_buttons([self.switch_pin], self.switch_pin_callback)

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')
        self.gcode = self.AFC.gcode
        self.reactor = self.AFC.reactor

        #self.gcode.register_command('HUB_CUT_TEST', self.cmd_HUB_CUT_TEST, desc=self.cmd_HUB_CUT_TEST_help)
        #self.gcode.register_command('HUB_LOAD', self.cmd_HUB_LOAD, desc=self.cmd_HUB_LOAD_help)


    def switch_pin_callback(self, eventtime, state):
        self.state = state

    # HUB COMMANDS
    cmd_HUB_LOAD_help = "Load lane into hub"
    def cmd_HUB_LOAD(self, gcmd):
        """
        This function handles the loading of a specified lane into the hub. It performs
        several checks and movements to ensure the lane is properly loaded.

        Usage: `HUB_LOAD LANE=<lane>`
        Example: `HUB_LOAD LANE=leg1`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameter:
                  - LANE: The name of the lane to be loaded.

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_HUB = self.printer.lookup_object('AFC_hub '+ CUR_LANE.unit)
        if CUR_LANE.prep_state == False: return
        if CUR_LANE.load_state == False:
            CUR_LANE.do_enable(True)
            while CUR_LANE.load_state == False:
                CUR_LANE.move( CUR_HUB.move_dis, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
        if CUR_LANE.hub_load == False:
            CUR_LANE.move(CUR_LANE.dist_hub, CUR_LANE.dist_hub_move_speed, CUR_LANE.dist_hub_move_accel, True if CUR_LANE.dist_hub > 200 else False)
        while CUR_HUB.state == False:
            CUR_LANE.move(CUR_HUB.move_dis, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
        while CUR_HUB.state == True:
            CUR_LANE.move(CUR_HUB.move_dis * -1, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
        CUR_LANE.status = 'Hubed'
        CUR_LANE.do_enable(False)
        CUR_LANE.hub_load = True
        self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['hub_loaded'] = CUR_LANE.hub_load
        self.AFC.save_vars()

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
        self.gcode.respond_info('Testing Hub Cut on Lane: ' + lane)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_HUB = self.printer.lookup_object('AFC_hub ' + CUR_LANE.unit)
        CUR_HUB.hub_cut(CUR_LANE)
        self.gcode.respond_info('Hub cut Done!')

    def hub_cut(self, CUR_LANE):
        servo_string = 'SET_SERVO SERVO={servo} ANGLE={{angle}}'.format(servo=self.cut_servo_name)

        # Prep the servo for cutting.
        self.gcode.run_script_from_command(servo_string.format(angle=self.cut_servo_prep_angle))
        # Load the lane until the hub is triggered.
        while self.state == False:
            CUR_LANE.move( self.move_dis, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
        # Go back, to allow the `hub_cut_dist` to be accurate.
        CUR_LANE.move( -self.move_dis*4, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
        # Feed the `hub_cut_dist` amount.
        CUR_LANE.move( self.cut_dist, self.AFC.short_moves_speed, self.AFC.short_moves_accel)
        # Have a snooze
        self.reactor.pause(self.reactor.monotonic() + 0.5)


        # Choppy Chop
        self.gcode.run_script_from_command(servo_string.format(angle=self.cut_servo_clip_angle))
        if self.cut_confirm == True:
            self.reactor.pause(self.reactor.monotonic() + 0.5)
            # ReChop, To be doubly choppy sure.
            self.gcode.run_script_from_command(servo_string.format(angle=self.cut_servo_prep_angle))

            self.reactor.pause(self.reactor.monotonic() + 1)
            self.gcode.run_script_from_command(servo_string.format(angle=self.cut_servo_clip_angle))
        # Longer Snooze
        self.reactor.pause(self.reactor.monotonic() + 1)
        # Align bowden tube (reset)
        self.gcode.run_script_from_command(servo_string.format(angle=self.cut_servo_pass_angle))

        # Retract lane by `hub_cut_clear`.
        CUR_LANE.move( -self.cut_clear, self.AFC.short_moves_speed, self.AFC.short_moves_accel)

def load_config_prefix(config):
    return afc_hub(config)