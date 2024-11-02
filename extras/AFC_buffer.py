# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from configparser import Error as error

ADVANCE_STATE_NAME = "Expanded"
TRAILING_STATE_NAME = "Compressed"

class AFCtrigger:

    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')
        self.name = config.get_name().split(' ')[-1]
        self.turtleneck = False
        self.belay = False
        self.last_state = False
        self.enable = False
        self.current = ''
        self.AFC = self.printer.lookup_object('AFC')
        self.debug = config.getboolean("debug", False)
        self.buttons = self.printer.load_object(config, "buttons")

        # LED SETTINGS
        self.led_index = config.get('led_index', None)
        self.led = False
        if self.led_index is not None:
            self.led = True
            self.led_index = config.get('led_index')

        # Try and get one of each pin to see how user has configured buffer
        self.advance_pin = config.get('advance_pin', None)
        self.buffer_distance = config.getfloat('distance', None)

        if self.advance_pin is not None and self.buffer_distance is not None:
            # Throw an error as this is not a valid configuration, only Turtle neck or buffer can be configured not both
            msg = "Turtle neck or buffer can be configured not both, please fix buffer configuration"
            self.gcode._respond_error( msg )
            raise error( msg )

        # Pull config for Turtleneck style buffer (advance and training switches)
        if self.advance_pin is not None:
            self.turtleneck = True
            self.advance_pin = config.get('advance_pin')
            self.trailing_pin = config.get('trailing_pin')
            self.multiplier_high = config.getfloat("multiplier_high", default=1.1, minval=1.0)
            self.multiplier_low = config.getfloat("multiplier_low", default=0.9, minval=0.0, maxval=1.0)

        # Pull config for Belay style buffer (single switch)
        elif self.buffer_distance is not None:
            self.belay = True
            self.pin = config.get('pin')
            self.buffer_distance = config.getfloat('distance', 0)
            self.velocity = config.getfloat('velocity', 0)
            self.accel = config.getfloat('accel', 0)

        # Error if buffer is not configured correctly
        else:
            msg = "Buffer is not configured correctly, please fix configuration"
            self.gcode._respond_error( msg )
            raise error( msg )

        self.printer.register_event_handler("klippy:ready", self._handle_ready)

        self.gcode.register_mux_command("QUERY_BUFFER", "BUFFER", self.name, self.cmd_QUERY_BUFFER, desc=self.cmd_QUERY_BUFFER_help)

        # Belay Buffer
        if self.belay:
            self.buttons.register_buttons([self.pin], self.belay_sensor_callback)

        # Turtleneck Buffer
        if self.turtleneck:
            self.buttons.register_buttons([self.advance_pin], self.advance_callback)
            self.buttons.register_buttons([self.trailing_pin], self.trailing_callback)
            self.gcode.register_mux_command("SET_ROTATION_FACTOR", "AFC_trigger", None, self.cmd_SET_ROTATION_FACTOR, desc=self.cmd_LANE_ROT_FACTOR_help)

    def _handle_ready(self):
        self.min_event_systime = self.reactor.monotonic() + 2.

     # Belay Call back
    def belay_sensor_callback(self, eventime, state):
        if not self.last_state and state:
            if self.printer.state_message == 'Printer is ready' and self.enable:
                if self.AFC.tool_start.filament_present:
                    if self.AFC.current != None:
                        self.belay_move_lane(state)
        self.last_state = state

    def belay_move_lane(self, state):
        if not self.enable: return
        if self.AFC.current is None: return

        if state:
            tool_loaded = self.AFC.current
            LANE = self.printer.lookup_object('AFC_stepper ' + tool_loaded)
            if LANE.status != 'unloading':
                if self.debug: self.gcode.respond_info("Buffer Triggered, Moving Lane {} forward {}mm".format(tool_loaded, self.buffer_distance))
                LANE.move(self.buffer_distance, self.velocity ,self.accel)

    def enable_buffer(self):
        if self.led:
            self.AFC.afc_led(self.AFC.led_buffer_disabled, self.led_index)
        if self.turtleneck:
            self.enable = True
            multiplier = 1.0
            if self.last_state == ADVANCE_STATE_NAME:
                multiplier = self.multiplier_low
            elif self.last_state == TRAILING_STATE_NAME:
                multiplier = self.multiplier_high
            self.set_multiplier( multiplier )
            if self.debug: self.gcode.respond_info("{} buffer enabled".format(self.name.upper()))
        elif self.belay:
            self.enable = True
            if self.debug: self.gcode.respond_info("{} buffer enabled".format(self.name.upper()))
            self.belay_move_lane(self.last_state)

    def disable_buffer(self):
        self.enable = False
        if self.debug: self.gcode.respond_info("{} buffer disabled".format(self.name.upper()))
        if self.led:
            self.AFC.afc_led(self.AFC.led_buffer_disabled, self.led_index)
        if self.turtleneck:
            self.reset_multiplier()
        self.last_state = False

    # Turtleneck commands
    def set_multiplier(self, multiplier):
        if not self.enable: return
        if self.AFC.current is None: return

        cur_stepper = self.printer.lookup_object('AFC_stepper ' + self.AFC.current)
        cur_stepper.update_rotation_distance( multiplier )
        if self.led:
            if multiplier > 1:
                self.AFC.afc_led(self.AFC.led_trailing, self.led_index)
            elif multiplier < 1:
                self.AFC.afc_led(self.AFC.led_advancing, self.led_index)
        if self.debug:
            stepper = cur_stepper.extruder_stepper.stepper
            self.gcode.respond_info("New rotation distance after applying factor: {}".format(stepper.get_rotation_distance()[0]))

    def reset_multiplier(self):
        if self.debug: self.gcode.respond_info("Buffer multiplier reset")

        cur_stepper = self.printer.lookup_object('AFC_stepper ' + self.AFC.current)
        cur_stepper.update_rotation_distance( 1 )
        self.gcode.respond_info("Rotation distance reset : {}".format(cur_stepper.extruder_stepper.stepper.get_rotation_distance()[0]))

    def advance_callback(self, eventime, state):
        if self.printer.state_message == 'Printer is ready' and self.enable and self.last_state != ADVANCE_STATE_NAME:
            if self.AFC.tool_start.filament_present:
                if self.AFC.current != None:
                    self.set_multiplier( self.multiplier_low )
                    if self.debug: self.gcode.respond_info("Buffer Triggered State: Advanced")

        if state: self.last_state = ADVANCE_STATE_NAME
        if not state: self.last_state = False

    def trailing_callback(self, eventime, state):
        if self.printer.state_message == 'Printer is ready' and self.enable and self.last_state != TRAILING_STATE_NAME:
            if self.AFC.tool_start.filament_present:
                if self.AFC.current != None:
                    self.set_multiplier( self.multiplier_high )
                    if self.debug: self.gcode.respond_info("Buffer Triggered State: Trailing")

        if state: self.last_state = TRAILING_STATE_NAME
        if not state: self.last_state = False

    def buffer_status(self):
        state_info = ''
        if self.turtleneck:
            if self.last_state == TRAILING_STATE_NAME:
                state_info += "Compressed"
            elif self.last_state == ADVANCE_STATE_NAME:
                state_info = "Expanded"
            else:
                state_info += "buffer tube floating in the middle"
        else:
            if self.last_state:
                state_info += "compressed"
            else:
                state_info += "expanded"
        return state_info

    cmd_LANE_ROT_FACTOR_help = "change rotation distance by factor specified"
    def cmd_SET_ROTATION_FACTOR(self, gcmd):
        """
        Adjusts the rotation distance of the current AFC stepper motor by applying a
        specified factor. If no factor is provided, it defaults to 1.0, which resets
        the rotation distance to the base value.

        Args:
            gcmd: A G-code command object containing the parameters for the factor.
                The 'FACTOR' parameter is used to specify the multiplier for the
                rotation distance.

        Behavior:
            - The FACTOR must be greater than 0.
            - If the buffer is enabled and active, and a valid factor is provided,
            the function adjusts the rotation distance for the current AFC stepper.
            - If FACTOR is 1.0, the rotation distance is reset to the base value.
            - If FACTOR is a valid non-zero number, the rotation distance is updated
            by the provided factor.
            - If FACTOR is 0 or AFC is not enabled, an appropriate message is sent
            back through the G-code interface.
        """
        if self.turtleneck:
            if self.AFC.current != None and self.enable:
                change_factor = gcmd.get_float('FACTOR', 1.0)
                if change_factor <= 0:
                    self.gcode.respond_info("FACTOR must be greater than 0")
                    return
                elif change_factor == 1.0:
                    self.set_multiplier ( 1 )
                    self.gcode.respond_info("Rotation distance reset to base value")
                else:
                    self.set_multiplier( change_factor )
            else:
                self.gcode.respond_info("BUFFER {} NOT ENABLED".format(self.name.upper()))
        else:
            self.gcode.respond_info("BUFFER {} CAN'T CHANGE ROTATION DISTANCE".format(self.name.upper()))

    cmd_QUERY_BUFFER_help = "Report Buffer sensor state"
    def cmd_QUERY_BUFFER(self, gcmd):
        """
        Reports the current state of the buffer sensor and, if applicable, the rotation
        distance of the current AFC stepper motor.

        Behavior:
            - If the `turtleneck` feature is enabled and a tool is loaded, the rotation
            distance of the current AFC stepper motor is reported, along with the
            current state of the buffer sensor.
            - If the `turtleneck` feature is not enabled, only the buffer state is
            reported.
            - Both the buffer state and, if applicable, the stepper motor's rotation
            distance are sent back as G-code responses.
        """
        state_info = self.buffer_status()
        if self.turtleneck:
            if self.enable:
                tool_loaded=self.AFC.current
                LANE = self.printer.lookup_object('AFC_stepper ' + tool_loaded)
                stepper = LANE.extruder_stepper.stepper
                rotation_dist = stepper.get_rotation_distance()[0]
                state_info += ("\n{} Rotation distance: {}".format(LANE.name.upper(), rotation_dist))

        self.gcode.respond_info("{} : {}".format(self.name, state_info))

def load_config_prefix(config):
    return AFCtrigger(config)
