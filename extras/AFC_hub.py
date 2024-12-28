from configparser import Error as error

class afc_hub:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.AFC = self.printer.lookup_object('AFC')
        self.name = config.get_name().split()[-1]

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
        self.AFC.hubs[self.name]=None

        self.move_dis = config.getfloat("move_dis", 50)
        self.hub_clear_move_dis = config.getfloat("hub_clear_move_dis", 50)
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
        self.gcode = self.AFC.gcode
        self.reactor = self.AFC.reactor
        self.AFC.hubs[self.name]=self


    def switch_pin_callback(self, eventtime, state):
        self.state = state

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

    def get_status(self, eventtime=None):
        self.response = {}
        self.response['state'] = self.state
        self.response['cut'] = self.cut
        self.response['cut_cmd'] = self.cut_cmd
        self.response['cut_dist'] = self.cut_dist
        self.response['cut_clear'] = self.cut_clear
        self.response['cut_min_length'] = self.cut_min_length
        self.response['cut_servo_pass_angle'] = self.cut_servo_pass_angle
        self.response['cut_servo_clip_angle'] = self.cut_servo_clip_angle
        self.response['cut_servo_prep_angle'] = self.cut_servo_prep_angle
        
        return self.response

def load_config_prefix(config):
    return afc_hub(config)