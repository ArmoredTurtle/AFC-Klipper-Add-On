#import chelper
from . import AFC

class afc_hub:
    def __init__(self, config):
        self.AFC = AFC.afc
        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.AFC = self.printer.lookup_object('AFC')
        self.gcode = self.printer.lookup_object('gcode')
        self.reactor = self.printer.get_reactor()

        self.AFC = self.printer.lookup_object('AFC')
        self.cut = config.getboolean("cut", False)
        self.cut_cmd = config.get('cut_cmd', None)
        self.cut_dist = config.getfloat("cut_dist", 200)
        self.cut_clear = config.getfloat("cut_clear", 120)
        self.cut_min_length = config.getfloat("cut_min_length", 200)
        self.cut_servo_pass_angle = config.getfloat("cut_servo_pass_angle", 0)
        self.cut_servo_clip_angle = config.getfloat("cut_servo_clip_angle", 160)
        self.cut_servo_prep_angle = config.getfloat("cut_servo_prep_angle", 75)
        self.cut_confirm = config.getfloat("cut_confirm", 0)
        self.move_dis = config.getfloat("move_dis", 50)
        self.afc_bowden_length = config.getfloat("afc_bowden_length", 900)
        self.config_bowden_length = self.afc_bowden_length                          # Used by SET_BOWDEN_LENGTH macro
        buttons = self.printer.load_object(config, "buttons")
        self.switch_pin = config.get('switch_pin', None)
        if self.switch_pin is not None:
            self.state = False
            buttons.register_buttons([self.switch_pin], self.switch_pin_callback)

    def switch_pin_callback(self, eventtime, state):
        self.state = state

    def hub_cut(self, LANE):
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
        self.hub = self.printer.lookup_object('filament_switch_sensor ' + self.name).runout_helper

        # Prep the servo for cutting.
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_prep_angle))
        # Load the lane until the hub is triggered.
        while self.hub.filament_present == False:
            CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
        # Go back, to allow the `hub_cut_dist` to be accurate.
        CUR_LANE.move( -self.hub_move_dis*4, self.short_moves_speed, self.short_moves_accel)
        # Feed the `hub_cut_dist` amount.
        CUR_LANE.move( self.hub_cut_dist, self.short_moves_speed, self.short_moves_accel)
        # Have a snooze
        # Choppy Chop
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_clip_angle))
        if self.hub_cut_confirm == 1:
            # ReChop, To be doubly choppy sure.
            self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_prep_angle))
            self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_clip_angle))
        # Longer Snooze
        # Align bowden tube (reset)
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_pass_angle))
        # Retract lane by `hub_cut_clear`.
        CUR_LANE.move( -self.hub_cut_clear, self.short_moves_speed, self.short_moves_accel)

def load_config_prefix(config):
    return afc_hub(config)