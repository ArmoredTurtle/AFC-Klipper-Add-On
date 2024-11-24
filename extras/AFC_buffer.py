# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from configparser import Error as error

ADVANCE_STATE_NAME = "Expanded"
TRAILING_STATE_NAME = "Compressed"
CHECK_RUNOUT_TIMEOUT = .5

class AFCtrigger:

    def __init__(self, config):
        self.printer       = config.get_printer()
        self.reactor       = self.printer.get_reactor()
        self.gcode         = self.printer.lookup_object('gcode')
        self.name          = config.get_name().split(' ')[-1]
        self.AFC           = self.printer.lookup_object('AFC')
        self.turtleneck    = False
        self.belay         = False
        self.last_state    = False
        self.enable        = False
        self.printer_ready = False
        self.is_printing   = False
        self.debug         = config.getboolean("debug", False)
        self.buttons       = self.printer.load_object(config, "buttons")

        # CLOG SETTINGS
        self.estimated_print_time = None
        self.min_event_systime    = self.reactor.NEVER
        # error sensitivity, 0 disables, 1 is the most, 10 is the least
        self.error_sensitivity    = config.getfloat("filament_error_sensitivity", default=0, minval=0, maxval=10)
        self.fault_sensitivity    = self.error_sensitivity * 10
        self.filament_error_pos   = None
        self.past_position        = None

        # LED SETTINGS
        self.led_index = config.get('led_index', None)
        self.led = False
        if self.led_index is not None:
            self.led = True
            self.led_index = config.get('led_index')

        # Try and get one of each pin to see how user has configured buffer
        self.advance_pin     = config.get('advance_pin', None)
        self.buffer_distance = config.getfloat('distance', None)

        if self.advance_pin is not None and self.buffer_distance is not None:
            # Throw an error as this is not a valid configuration, only Turtle neck or buffer can be configured not both
            msg = "Turtle neck or buffer can be configured not both, please fix buffer configuration"
            self.gcode._respond_error( msg )
            raise error( msg )

        # Pull config for Turtleneck style buffer (advance and training switches)
        if self.advance_pin is not None:
            self.turtleneck       = True
            self.advance_pin      = config.get('advance_pin')
            self.trailing_pin     = config.get('trailing_pin')
            self.multiplier_high  = config.getfloat("multiplier_high", default=1.1, minval=1.0)
            self.multiplier_low   = config.getfloat("multiplier_low", default=0.9, minval=0.0, maxval=1.0)
            self.velocity         = config.getfloat('velocity', 0)

        # Pull config for Belay style buffer (single switch)
        elif self.buffer_distance is not None:
            self.belay            = True
            self.pin              = config.get('pin')
            self.buffer_distance  = config.getfloat('distance', 0)
            self.velocity         = config.getfloat('velocity', 0)
            self.accel            = config.getfloat('accel', 0)

        # Error if buffer is not configured correctly
        else:
            msg = "Buffer is not configured correctly, please fix configuration"
            self.gcode._respond_error( msg )
            raise error( msg )

        self.printer.register_event_handler("klippy:connect"       , self._handle_ready)
        self.printer.register_event_handler('idle_timeout:printing', self._handle_printing)
        self.printer.register_event_handler('idle_timeout:ready'   , self._handle_printer_ready)
        self.printer.register_event_handler('idle_timeout:idle'    , self._handle_not_printing)

        self.gcode.register_mux_command("QUERY_BUFFER", "BUFFER", self.name, self.cmd_QUERY_BUFFER, desc=self.cmd_QUERY_BUFFER_help)

        # Belay Buffer
        if self.belay:
            self.buttons.register_buttons([self.pin], self.belay_sensor_callback)

        # Turtleneck Buffer
        if self.turtleneck:
            self.buttons.register_buttons([self.advance_pin] , self.advance_callback)
            self.buttons.register_buttons([self.trailing_pin], self.trailing_callback)
            self.gcode.register_mux_command("SET_ROTATION_FACTOR", "AFC_trigger", None, self.cmd_SET_ROTATION_FACTOR, desc=self.cmd_LANE_ROT_FACTOR_help)
            self.gcode.register_mux_command("SET_BUFFER_MULTIPLIER", "AFC_trigger", None, self.cmd_SET_MULTILIER, desc=self.cmd_SET_MULTILIER_help)

    def turtle_fault_enabled(self):
        """Checks if the turtleneck, fault detection. and enabled"""
        return self.turtleneck and self.error_sensitivity > 0 and self.enable

    def _handle_ready(self):
        # set startup delay time
        self.gcode.respond_info('filament error detection enabled')
        self.min_event_systime = self.reactor.monotonic() + 5.
        if self.turtleneck:
            self.extruder = self.printer.lookup_object('toolhead').get_extruder()
            self.estimated_print_time = (self.printer.lookup_object('mcu').estimated_print_time)
            # start process for filament error checking
            if self.error_sensitivity > 0:
                self.update_filament_error_pos()
                # register timer that will run to check buffer state changes
                self.extruder_pos_timer = self.reactor.register_timer(self.extruder_pos_update_event)

    def _handle_printer_ready(self, print_time):
        self.is_printing = False
        self.printer_ready = True
        if self.turtle_fault_enabled():
            self.reactor.update_timer(self.extruder_pos_timer, self.reactor.NEVER)

    def _handle_not_printing(self, print_time):
        self.is_printing = False
        if self.turtle_fault_enabled():
            self.reactor.update_timer(self.extruder_pos_timer, self.reactor.NEVER)

    def _handle_printing(self, print_time):
        if self.printer_ready:
            self.is_printing = True
            self.min_event_systime  = self.reactor.monotonic()

     # Belay Call back
    def belay_sensor_callback(self, eventtime, state):
        if not self.last_state and state:
            if self.printer.state_message == 'Printer is ready' and self.enable:
                cur_stepper = self.printer.lookup_object('AFC_stepper ' + self.AFC.current)
                if cur_stepper.hub.tool_state:
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
            else:
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
            if self.is_printing and self.error_sensitivity > 0:
                self.reactor.update_timer(self.extruder_pos_timer, self.reactor.NEVER)
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


    def advance_callback(self, eventtime, state):
        if self.printer.state_message == 'Printer is ready' and self.enable:
            CUR_LANE = self.printer.lookup_object('AFC_stepper ' + self.AFC.current)
            CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
            if CUR_EXTRUDER.tool_start_state:
                if self.AFC.current != None:
                    if state:
                        CUR_LANE.assist(self.velocity / 100)
                        self.reactor.pause(self.reactor.monotonic() + 1)
                        CUR_LANE.assist(0)
                        if self.debug:
                            self.gcode.respond_info("Buffer Triggered State: Advanced\nWATCHING FOR CLOG")
                        self.set_multiplier( (self.multiplier_low + self.multiplier_low) / 5 )
                        if self.debug: self.gcode.respond_info("Buffer Triggered State: Advanced, setting Extra low")
                        # Start clog watch
                        if self.turtle_fault_enabled():
                            self.update_filament_error_pos(eventtime)
                            self.reactor.update_timer(self.extruder_pos_timer, self.reactor.NOW)
                    else:
                        self.set_multiplier( self.multiplier_low )
                        if self.debug: self.gcode.respond_info("Buffer Triggered State: Off Advanced, cancel clog watch")
                        # if state changed before timer expires, disable clog timer
                        if self.turtle_fault_enabled():
                            self.update_filament_error_pos(eventtime)
                            self.reactor.update_timer(self.extruder_pos_timer, self.reactor.NEVER)

        if state: self.last_state = ADVANCE_STATE_NAME
        if not state: self.last_state = False

    def trailing_callback(self, eventtime, state):
        if self.printer.state_message == 'Printer is ready' and self.enable:
            CUR_LANE = self.printer.lookup_object('AFC_stepper ' + self.AFC.current)
            CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
            if CUR_EXTRUDER.tool_start_state:
                if self.AFC.current != None:
                    if state:
                        # forward assist to help keep filament on spool loose
                        CUR_LANE.assist(self.velocity / 100)
                        self.reactor.pause(self.reactor.monotonic() + 1)
                        CUR_LANE.assist(0)
                        self.set_multiplier( self.multiplier_high * 1.5)
                        if self.debug:
                            self.gcode.respond_info("Buffer Triggered State: Trailing, setting extra high")
                        if self.turtle_fault_enabled():
                            self.update_filament_error_pos(eventtime)
                            self.reactor.update_timer(self.extruder_pos_timer, self.reactor.NOW)
                    else:
                        self.set_multiplier( self.multiplier_high )
                        if self.debug:
                            self.gcode.respond_info("Buffer Triggered State: Trailing, setting high")
                        # Signal that no error was found
                        if self.turtle_fault_enabled():
                            self.update_filament_error_pos(eventtime)
                            self.reactor.update_timer(self.extruder_pos_timer, self.reactor.NEVER)

        if state: self.last_state = TRAILING_STATE_NAME
        if not state: self.last_state = False

    # get the position of the extruder for error reference
    def get_extruder_pos(self, eventtime=None):
        if eventtime is None:
            eventtime = self.reactor.monotonic()
        print_time = self.estimated_print_time(eventtime)
        last_position = self.extruder.find_past_position(print_time)

        if self.past_position is None or last_position > self.past_position:
            self.past_position = last_position
            if self.debug and last_position > 0: self.gcode.respond_info("Extruder last position: {}".format(last_position))
            return last_position

        else:
            return self.past_position

    # store error length
    def update_filament_error_pos(self, eventtime=None):
        if eventtime is None:
            eventtime = self.reactor.monotonic()
        self.filament_error_pos = (self.get_extruder_pos(eventtime) + self.fault_sensitivity)

    # watch for filament errors
    # if the extruder position is greater then the set error out length pause print
    def extruder_pos_update_event(self, eventtime):
        extruder_pos = self.get_extruder_pos(eventtime)
        # Check for filament problems
        if not self.printer_ready:
            if self.debug: self.gcode.respond_info("Printer not yet ready exiting fault detection")
            return self.reactor.NEVER

        if extruder_pos != None:
            msg = "AFC filament fault detected! Take necessary action."
            self.pause_on_error(msg, extruder_pos > self.filament_error_pos)

        return eventtime + CHECK_RUNOUT_TIMEOUT

    # pause print through AFC_error, check before stops repeat events
    def pause_on_error(self, msg, pause=False):
        eventtime = self.reactor.monotonic()
        CUR_LANE  = self.printer.lookup_object('AFC_stepper ' + self.AFC.current)
        if eventtime < self.min_event_systime or not self.enable:
            return
        if pause:
            if self.last_state == ADVANCE_STATE_NAME:
                msg += '\n CLOG DETECTED'
            if self.last_state == TRAILING_STATE_NAME:
                msg += '\n AFC NOT FEEDING'
            elif CUR_LANE.prep_state == False:
                msg += '\nFilament runout'
            self.min_event_systime = self.reactor.NEVER
            self.AFC.AFC_error( msg, True )

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

    cmd_SET_MULTILIER_help = "live adjust buffer high and low multiplier"
    def cmd_SET_MULTILIER(self, gcmd):
        if self.turtleneck:
            if self.AFC.current != None and self.enable:
                chg_multiplier = gcmd.get('MULTIPLIER', None)
                if chg_multiplier == None:
                    self.gcode.respond_info("Multiplier must be provided, HIGH or LOW")
                    return
                chg_factor = gcmd.get_float('FACTOR')
                if chg_factor <= 0:
                    self.gcode.respond_info("FACTOR must be greater than 0")
                    return
                if chg_multiplier == "HIGH" and chg_factor > 1:
                    self.multiplier_high = chg_factor
                    self.set_multiplier(chg_factor)
                    self.gcode.respond_info("multiplier_high set to {}").format(chg_factor)
                    self.gcode.respond_info('multiplier_high: {} MUST be updated under buffer config for value to be saved').format(chg_factor)
                elif chg_multiplier == "LOW" and chg_factor < 1:
                    self.multiplier_low = chg_factor
                    self.set_multiplier(chg_factor)
                    self.gcode.respond_info("multiplier_low set to {}").format(chg_factor)
                    self.gcode.respond_info('multiplier_low: {} MUST be updated under buffer config for value to be saved').format(chg_factor)

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