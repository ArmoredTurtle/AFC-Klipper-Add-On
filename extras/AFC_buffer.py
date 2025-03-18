# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from configparser import Error as error
try:
    from extras.AFC_utils import add_filament_switch
except:
    raise error("Error trying to import AFC_utils, please rerun install-afc.sh script in your AFC-Klipper-Add-On directory then restart klipper")

ADVANCE_STATE_NAME = "Trailing"
TRAILING_STATE_NAME = "Advancing"

class AFCtrigger:

    def __init__(self, config):
        self.printer    = config.get_printer()
        self.AFC        = self.printer.lookup_object('AFC')
        self.reactor    = self.AFC.reactor
        self.gcode      = self.AFC.gcode
        self.logger     = self.AFC.logger

        self.name       = config.get_name().split(' ')[-1]
        self.lanes      = {}
        self.turtleneck = False
        self.belay      = False
        self.last_state = "Unknown"
        self.enable     = False
        self.current    = ''
        self.advance_state = False
        self.trailing_state = False

        self.debug                  = config.getboolean("debug", False)
        self.enable_sensors_in_gui  = config.getboolean("enable_sensors_in_gui", self.AFC.enable_sensors_in_gui)  # Set to True toolhead sensors switches as filament sensors in mainsail/fluidd gui, overrides value set in AFC.cfg
        self.buttons                = self.printer.load_object(config, "buttons")

        # LED SETTINGS
        self.led                    = False
        self.led_index              = config.get('led_index', None)
        self.led_advancing          = config.get('led_buffer_advancing','0,0,1,0')
        self.led_trailing           = config.get('led_buffer_trailing','0,1,0,0')
        self.led_buffer_disabled    = config.get('led_buffer_disable', '0,0,0,0.25')

        if self.led_index is not None:
            self.led = True
            self.led_index = config.get('led_index')

        # Try and get one of each pin to see how user has configured buffer
        self.advance_pin        = config.get('advance_pin', None)
        self.buffer_distance    = config.getfloat('distance', None)

        if self.advance_pin is not None and self.buffer_distance is not None:
            # Throw an error as this is not a valid configuration, only Turtle neck or buffer can be configured not both
            msg = "Turtle neck or buffer can be configured not both, please fix buffer configuration"
            self.logger.error( msg )
            raise error( msg )

        # Pull config for Turtleneck style buffer (advance and training switches)
        if self.advance_pin is not None:
            self.turtleneck         = True
            self.advance_pin        = config.get('advance_pin') # Advance pin for buffer
            self.trailing_pin       = config.get('trailing_pin') # Trailing pin for buffer
            self.multiplier_high    = config.getfloat("multiplier_high", default=1.1, minval=1.0)
            self.multiplier_low     = config.getfloat("multiplier_low", default=0.9, minval=0.0, maxval=1.0)
            self.velocity           = config.getfloat('velocity', 0) # Velocity for forward assist

            if self.enable_sensors_in_gui:
                self.adv_filament_switch_name = "filament_switch_sensor {}_{}".format(self.name, "expanded")
                self.fila_avd = add_filament_switch(self.adv_filament_switch_name, self.advance_pin, self.printer )

                self.trail_filament_switch_name = "filament_switch_sensor {}_{}".format(self.name, "compressed")
                self.fila_trail = add_filament_switch(self.trail_filament_switch_name, self.trailing_pin, self.printer )

        # Pull config for Belay style buffer (single switch)
        elif self.buffer_distance is not None:
            self.belay              = True
            self.pin                = config.get('pin')
            self.buffer_distance    = config.getfloat('distance', 0)
            self.velocity           = config.getfloat('velocity', 0)
            self.accel              = config.getfloat('accel', 0)

        # Error if buffer is not configured correctly
        else:
            msg = "Buffer is not configured correctly, please fix configuration"
            self.logger.error( msg )
            raise error( msg )

        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.gcode.register_mux_command("QUERY_BUFFER",         "BUFFER", self.name, self.cmd_QUERY_BUFFER,         desc=self.cmd_QUERY_BUFFER_help)
        self.gcode.register_mux_command("SET_BUFFER_VELOCITY",  "BUFFER", self.name, self.cmd_SET_BUFFER_VELOCITY,  desc=self.cmd_SET_BUFFER_VELOCITY_help)
        self.gcode.register_mux_command("ENABLE_BUFFER",        "BUFFER", self.name, self.cmd_ENABLE_BUFFER)
        self.gcode.register_mux_command("DISABLE_BUFFER",       "BUFFER", self.name, self.cmd_DISABLE_BUFFER)

        # Belay Buffer
        if self.belay:
            self.buttons.register_buttons([self.pin], self.belay_sensor_callback)

        # Turtleneck Buffer
        if self.turtleneck:
            self.buttons.register_buttons([self.advance_pin], self.advance_callback)
            self.buttons.register_buttons([self.trailing_pin], self.trailing_callback)

            self.gcode.register_mux_command("SET_ROTATION_FACTOR",      "BUFFER", self.name, self.cmd_SET_ROTATION_FACTOR,  desc=self.cmd_LANE_ROT_FACTOR_help)
            self.gcode.register_mux_command("SET_BUFFER_MULTIPLIER",    "BUFFER", self.name, self.cmd_SET_BUFFER_MULTIPLIER,desc=self.cmd_SET_BUFFER_MULTIPLIER_help)

        self.AFC.buffers[self.name] = self

    def __str__(self):
        return self.name

    def _handle_ready(self):
        self.min_event_systime = self.reactor.monotonic() + 2.

        if self.led_index is not None:
            # Verify that LED config is found
            error_string, led = self.AFC.FUNCTION.verify_led_object(self.led_index)
            if led is None:
                raise error(error_string)

     # Belay Call back
    def belay_sensor_callback(self, eventime, state):
        if not self.last_state and state:
            if self.printer.state_message == 'Printer is ready' and self.enable:
                CUR_LANE = self.AFC.FUNCTION.get_current_lane_obj()
                if CUR_LANE is not None:
                    CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
                    if CUR_EXTRUDER.tool_start_state:
                        self.belay_move_lane(state)
        self.last_state = state

    def belay_move_lane(self, state):
        if not self.enable: return
        LANE = self.AFC.FUNCTION.get_current_lane_obj()
        if self.LANE is None: return

        if state:
            if LANE.status != 'unloading':
                if self.debug: self.logger.info("Buffer Triggered, Moving Lane {} forward {}mm".format(LANE.name, self.buffer_distance))
                LANE.move(self.buffer_distance, self.velocity ,self.accel)

    def enable_buffer(self):
        if self.led:
            self.AFC.FUNCTION.afc_led(self.led_buffer_disabled, self.led_index)
        if self.turtleneck:
            self.enable = True
            multiplier = 1.0
            if self.last_state == ADVANCE_STATE_NAME:
                multiplier = self.multiplier_low
            else:
                multiplier = self.multiplier_high
            self.set_multiplier( multiplier )
            if self.debug: self.logger.info("{} buffer enabled".format(self.name))
        elif self.belay:
            self.enable = True
            if self.debug: self.logger.info("{} buffer enabled".format(self.name))
            self.belay_move_lane(self.last_state)

    def disable_buffer(self):
        self.enable = False
        if self.debug: self.logger.info("{} buffer disabled".format(self.name))
        if self.led:
            self.AFC.FUNCTION.afc_led(self.led_buffer_disabled, self.led_index)
        if self.turtleneck:
            self.reset_multiplier()

    # Turtleneck commands
    def set_multiplier(self, multiplier):
        if not self.enable: return
        cur_stepper = self.AFC.FUNCTION.get_current_lane_obj()
        if cur_stepper is None: return

        cur_stepper.update_rotation_distance( multiplier )
        if multiplier > 1:
            self.last_state = TRAILING_STATE_NAME
            if self.led:
                self.AFC.FUNCTION.afc_led(self.led_trailing, self.led_index)
        elif multiplier < 1:
            self.last_state = ADVANCE_STATE_NAME
            if self.led:
                self.AFC.FUNCTION.afc_led(self.led_advancing, self.led_index)
        if self.debug:
            stepper = cur_stepper.extruder_stepper.stepper
            self.logger.info("New rotation distance after applying factor: {:.4f}".format(stepper.get_rotation_distance()[0]))

    def reset_multiplier(self):
        if self.debug: self.logger.info("Buffer multiplier reset")

        cur_stepper = self.AFC.FUNCTION.get_current_lane_obj()
        if cur_stepper is None: return

        cur_stepper.update_rotation_distance( 1 )
        self.logger.info("Rotation distance reset : {:.4f}".format(cur_stepper.extruder_stepper.stepper.get_rotation_distance()[0]))

    def advance_callback(self, eventime, state):
        self.advance_state = state
        if self.printer.state_message == 'Printer is ready' and self.enable:
            CUR_LANE = self.AFC.FUNCTION.get_current_lane_obj()

            if CUR_LANE != None and state:
                CUR_LANE.assist(CUR_LANE.calculate_pwm_value(self.AFC.gcode_move.speed * (self.velocity / 10)))
                self.reactor.pause(self.reactor.monotonic() + 1)
                CUR_LANE.assist(0)
                self.set_multiplier( self.multiplier_low )
                if self.debug: self.logger.info("Buffer Triggered State: Advanced")
        self.last_state = ADVANCE_STATE_NAME

    def trailing_callback(self, eventime, state):
        self.trailing_state = state
        if self.printer.state_message == 'Printer is ready' and self.enable:
            CUR_LANE = self.AFC.FUNCTION.get_current_lane_obj()

            if CUR_LANE != None and state:
                CUR_LANE.assist(CUR_LANE.calculate_pwm_value(self.AFC.gcode_move.speed * (self.velocity / 10)))
                self.reactor.pause(self.reactor.monotonic() + 1)
                CUR_LANE.assist(0)
                self.set_multiplier( self.multiplier_high )
                if self.debug: self.logger.info("Buffer Triggered State: Trailing")
        self.last_state = TRAILING_STATE_NAME

    def buffer_status(self):
        state_info = ''
        if self.turtleneck:
            state_info = self.last_state
        else:
            if self.last_state:
                state_info += "compressed"
            else:
                state_info += "expanded"
        return state_info

    cmd_SET_BUFFER_MULTIPLIER_help = "live adjust buffer high and low multiplier"
    def cmd_SET_BUFFER_MULTIPLIER(self, gcmd):
        """
        This function handles the adjustment of the buffer multipliers for the turtleneck buffer.
        It retrieves the multiplier type ('HIGH' or 'LOW') and the factor to be applied. The function
        ensures that the factor is valid and updates the corresponding multiplier.

        Usage: SET_BUFFER_MULTIPLIER BUFFER=<buffer_name> MULTIPLIER=<HIGH/LOW> FACTOR=<factor>
        Example: SET_BUFFER_MULTIPLIER BUFFER=TN MULTIPLIER=HIGH FACTOR=1.2

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  - MULTIPLIER: The type of multiplier to be adjusted ('HIGH' or 'LOW').
                  - FACTOR: The factor to be applied to the multiplier.

        Returns:
            None
        """
        if self.turtleneck:
            cur_stepper = self.AFC.FUNCTION.get_current_lane_obj()
            if cur_stepper != None and self.enable:
                chg_multiplier = gcmd.get('MULTIPLIER', None)
                if chg_multiplier == None:
                    self.logger.info("Multiplier must be provided, HIGH or LOW")
                    return
                chg_factor = gcmd.get_float('FACTOR')
                if chg_factor <= 0:
                    self.logger.info("FACTOR must be greater than 0")
                    return
                if chg_multiplier == "HIGH" and chg_factor > 1:
                    self.multiplier_high = chg_factor
                    self.set_multiplier(chg_factor)
                    self.logger.info("multiplier_high set to {}".format(chg_factor))
                    self.logger.info('multiplier_high: {} MUST be updated under buffer config for value to be saved'.format(chg_factor))
                elif chg_multiplier == "LOW" and chg_factor < 1:
                    self.multiplier_low = chg_factor
                    self.set_multiplier(chg_factor)
                    self.logger.info("multiplier_low set to {}".format(chg_factor))
                    self.logger.info('multiplier_low: {} MUST be updated under buffer config for value to be saved'.format(chg_factor))
                else:
                    self.logger.info('multiplier_high must be greater than 1, multiplier_low must be less than 1')

    cmd_LANE_ROT_FACTOR_help = "change rotation distance by factor specified"
    def cmd_SET_ROTATION_FACTOR(self, gcmd):
        """
        Adjusts the rotation distance of the current AFC stepper motor by applying a
        specified factor. If no factor is provided, it defaults to 1.0, which resets
        the rotation distance to the base value.

        Usage: SET_ROTATION_FACTOR BUFFER=<buffer_name> FACTOR=<factor>
        Example: SET_ROTATION_FACTOR BUFFER=TN FACTOR=1.2

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
            cur_stepper = self.AFC.FUNCTION.get_current_lane_obj()
            if cur_stepper != None and self.enable:
                change_factor = gcmd.get_float('FACTOR', 1.0)
                if change_factor <= 0:
                    self.logger.info("FACTOR must be greater than 0")
                    return
                elif change_factor == 1.0:
                    self.set_multiplier ( 1 )
                    self.logger.info("Rotation distance reset to base value")
                else:
                    self.set_multiplier( change_factor )
            else:
                self.logger.info("BUFFER {} NOT ENABLED".format(self.name))
        else:
            self.logger.info("BUFFER {} CAN'T CHANGE ROTATION DISTANCE".format(self.name))

    cmd_QUERY_BUFFER_help = "Report Buffer sensor state"
    def cmd_QUERY_BUFFER(self, gcmd):
        """
        Reports the current state of the buffer sensor and, if applicable, the rotation
        distance of the current AFC stepper motor.

        Usage: QUERY_BUFFER BUFFER=<buffer_name>
        Example: QUERY_BUFFER BUFFER=TN

        Behavior:
            - If the `turtleneck` feature is enabled and a tool is loaded, the rotation
            distance of the current AFC stepper motor is reported, along with the
            current state of the buffer sensor.
            - If the `turtleneck` feature is not enabled, only the buffer state is
            reported.
            - Both the buffer state and, if applicable, the stepper motor's rotation
            distance are sent back as G-code responses.
        """
        state_mapping = {
            TRAILING_STATE_NAME: ' (Compressed)',
            ADVANCE_STATE_NAME: ' (Expanded)',
            }
        state_info = self.buffer_status()
        state_info += state_mapping.get(state_info, '')
        if self.turtleneck:
            if self.enable:
                LANE = self.AFC.FUNCTION.get_current_lane_obj()
                stepper = LANE.extruder_stepper.stepper
                rotation_dist = stepper.get_rotation_distance()[0]
                state_info += ("\n{} Rotation distance: {:.4f}".format(LANE.name, rotation_dist))

        self.logger.info("{} : {}".format(self.name, state_info))

    cmd_SET_BUFFER_VELOCITY_help = "Set buffer velocity realtime for forward assist"
    def cmd_SET_BUFFER_VELOCITY(self, gcmd):
        """
        Allows users to tweak buffer velocity setting while printing. This setting is not
        saved in configuration. Please update your configuration file once you find a velocity that
        works for your setup.

        Usage: SET_BUFFER_VELOCITY BUFFER=<buffer_name> VELOCITY=<value>
        Example: SET_BUFFER_VELOCITY BUFFER=TN2 VELOCITY=100

        Behavior:
            - Updates the value that the espooler use for forward assist during printing.
            - Setting value to zero disables forward assist during printing.
            - Velocity is not saved to configuration file, needs to be manually updated.
        """
        old_velocity = self.velocity
        self.velocity = gcmd.get_float('VELOCITY', 0.0)
        self.logger.info("VELOCITY for {} was updated from {} to {}".format(self.name, old_velocity, self.velocity))

    def cmd_ENABLE_BUFFER(self, gcmd):
        self.enable_buffer()

    def cmd_DISABLE_BUFFER(self, gcmd):
        self.disable_buffer()

    def get_status(self, eventtime=None):
        self.response = {}
        self.response['state'] = self.last_state
        self.response['lanes'] = [lane.name for lane in self.lanes.values()]
        self.response['enabled'] = self.enable
        self.response['belay'] = self.belay
        return self.response

def load_config_prefix(config):
    return AFCtrigger(config)