
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
        self.cut_dist = config.getfloat("cut_dist", 50)
        self.cut_clear = config.getfloat("cut_clear", 120)
        self.cut_min_length = config.getfloat("cut_min_length", 200)
        self.cut_servo_pass_angle = config.getfloat("cut_servo_pass_angle", 0)
        self.cut_servo_clip_angle = config.getfloat("cut_servo_clip_angle", 160)
        self.cut_servo_prep_angle = config.getfloat("cut_servo_prep_angle", 75)
        self.cut_confirm = config.getboolean("cut_confirm", 0)

        self.move_dis = config.getfloat("move_dis", 50)
        self.hub_clear_move_dis = config.getfloat("hub_clear_move_dis", 50)
        self.assisted_retract = config.getboolean("assisted_retract", False) # if True, retracts are assisted to prevent loose windings on the spool
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


    def switch_pin_callback(self, eventtime, state):
        self.state = state

    def hub_cut(self, CUR_LANE):
        servo_string = 'SET_SERVO SERVO={servo} ANGLE={{angle}}'.format(servo=self.cut_servo_name)

        # Prep the servo for cutting.
        self.gcode.run_script_from_command(servo_string.format(angle=self.cut_servo_prep_angle))
        # Load the lane until the hub is triggered.
        while not self.state:
            CUR_LANE.move(self.move_dis, self.AFC.short_moves_speed, self.AFC.short_moves_accel)

        # To have an accurate reference position for `hub_cut_dist`, move back and forth in smaller steps
        # to find the point where the hub just triggers.
        while self.state:
            CUR_LANE.move(-10, self.AFC.short_moves_speed, self.AFC.short_moves_accel, self.assisted_retract)
        while not self.state:
            CUR_LANE.move(2, self.AFC.short_moves_speed, self.AFC.short_moves_accel)

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
        CUR_LANE.move(-self.cut_clear, self.AFC.short_moves_speed, self.AFC.short_moves_accel, self.assisted_retract)

def load_config_prefix(config):
    return afc_hub(config)