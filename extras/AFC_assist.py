# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import math

#respooler
PIN_MIN_TIME = 0.100
RESEND_HOST_TIME = 0.300 + PIN_MIN_TIME
MAX_SCHEDULE_TIME = 5.0

class AFCassistMotor:
    def __init__(self, config, type):
        self.printer = config.get_printer()
        ppins = self.printer.lookup_object("pins")
        # Determine pin type
        self.is_pwm = config.getboolean("pwm", False)
        if self.is_pwm and type != "enb":
            self.mcu_pin = ppins.setup_pin("pwm", config.get("afc_motor_{}".format(type)))
            cycle_time = config.getfloat("cycle_time", 0.100, above=0.,
                                         maxval=MAX_SCHEDULE_TIME)
            hardware_pwm = config.getboolean("hardware_pwm", False)
            self.mcu_pin.setup_cycle_time(cycle_time, hardware_pwm)
            self.scale = config.getfloat("scale", 1., above=0.)
        else:
            self.mcu_pin = ppins.setup_pin("digital_out", config.get("afc_motor_{}".format(type)))
            self.scale = 1.
            self.is_pwm = False

        self.last_print_time = 0.
        # Support mcu checking for maximum duration
        self.reactor = self.printer.get_reactor()
        self.resend_timer = None
        self.resend_interval = 0.
        max_mcu_duration = config.getfloat("maximum_mcu_duration", 0.,
                                           minval=0.500,
                                           maxval=MAX_SCHEDULE_TIME)
        self.mcu_pin.setup_max_duration(max_mcu_duration)
        if max_mcu_duration:
            config.deprecate("maximum_mcu_duration")
            self.resend_interval = max_mcu_duration - RESEND_HOST_TIME
        # Determine start and shutdown values
        static_value = config.getfloat("static_value", None,
                                       minval=0., maxval=self.scale)
        if static_value is not None:
            config.deprecate("static_value")
            self.last_value = self.shutdown_value = static_value / self.scale
        else:
            self.last_value = config.getfloat(
                "value", 0., minval=0., maxval=self.scale) / self.scale
            self.shutdown_value = config.getfloat(
                "shutdown_value", 0., minval=0., maxval=self.scale) / self.scale
        self.mcu_pin.setup_start_value(self.last_value, self.shutdown_value)

    def get_status(self, eventtime):
        return {"value": self.last_value}

    def _set_pin(self, print_time, value, is_resend=False):
        if value == self.last_value and not is_resend:
            return
        print_time = max(print_time, self.last_print_time + PIN_MIN_TIME)
        if self.is_pwm:
            self.mcu_pin.set_pwm(print_time, value)
        else:
            self.mcu_pin.set_digital(print_time, value)
        self.last_value = value
        self.last_print_time = print_time
        if self.resend_interval and self.resend_timer is None:
            self.resend_timer = self.reactor.register_timer(
                self._resend_current_val, self.reactor.NOW)

    def _resend_current_val(self, eventtime):
        if self.last_value == self.shutdown_value:
            self.reactor.unregister_timer(self.resend_timer)
            self.resend_timer = None
            return self.reactor.NEVER
        systime = self.reactor.monotonic()
        print_time = self.mcu_pin.get_mcu().estimated_print_time(systime)
        time_diff = (self.last_print_time + self.resend_interval) - print_time
        if time_diff > 0.:
            # Reschedule for resend time
            return systime + time_diff
        self._set_pin(print_time + PIN_MIN_TIME, self.last_value, True)
        return systime + self.resend_interval

class Espooler_values:
    """
    This class holds the common values for espooler assist, it consists of setters and getters for the values so that
    some values can easily hold a raw value and also return the value scaled.

    Parameters
    ----------------
    config : object
        Configuration object containing settings

    """
    def __init__(self, config):
        # Time in seconds to enable spooler at full speed to help with getting the spool to spin. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self._kick_start_time        = config.getfloat("kick_start_time",       None)
        # Distance per full rotation in mm. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self._mm_per_rotation        = config.getfloat("mm_per_rotation",       None)
        # Cycles per rotation in milliseconds. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self._cycles_per_rotation    = config.getfloat("cycles_per_rotation",   None)
        # PWM cycle time. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self._pwm_value              = config.getfloat("pwm_value",             None)
        # Delta amount in mm from last move to trigger assist. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self._delta_movement         = config.getfloat("delta_movement",        None)
        # Amount to move in mm once filament has moved by delta movement amount. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self._mm_movement            = config.getfloat("mm_movement",           None)
        # Scaling factor for the following variables: kick_start_time, mm_per_rotation, cycles_per_rotation, pwm_value, delta_movement, mm_movement. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self._scaling                = config.getfloat("spoolrate",             None)

    def calculate_cruise_time(self, mm_movement):
        """
        This function calculates cruise time which is the amount of time to enable motors to rotate spool mm movement amount

        :param mm_movement: Amount to move spool in mm
        :return float: Amount of time to be enabled to move mm amount
        """
        rotations = mm_movement / self.mm_per_rotation
        correction_factor = 1.0 + ( 1.68 * math.exp(-rotations * 5.0) )
        cruise_time = rotations * self.cycles_per_rotation * correction_factor

        return cruise_time/1000

    def handle_connect(self, unit_obj):
        """
        Should only be called during handle_connect callback to update values from unit. If values are not set per
        lane this function will update values from their unit.
        """
        if self._kick_start_time     is None: self.kick_start_time      = unit_obj.kick_start_time
        if self._mm_per_rotation     is None: self.mm_per_rotation      = unit_obj.mm_per_rotation
        if self._cycles_per_rotation is None: self.cycles_per_rotation  = unit_obj.cycles_per_rotation
        if self._pwm_value           is None: self.pwm_value            = unit_obj.pwm_value
        if self._mm_movement         is None: self.mm_movement          = unit_obj.mm_movement
        if self._delta_movement      is None: self.delta_movement       = unit_obj.delta_movement
        if self._scaling             is None: self.scaling              = unit_obj.scaling

        # Since cruise time is always going to be the same, calculate it now instead of everytime inside the timer callback
        self._cruise_time            = self.calculate_cruise_time(self.mm_movement)

    @property
    def cruise_time(self):
        """
        Returns calculated cruise time
        """
        return self._cruise_time
    @cruise_time.setter
    def cruise_time(self, value):
        self._cruise_time = value

    @property
    def kick_start_time(self):
        """
        Returns software kick start time, this value is scaled by scaling factor
        """
        return self._kick_start_time * self._scaling
    @kick_start_time.setter
    def kick_start_time(self, value):
        self._kick_start_time = value

    @property
    def mm_per_rotation(self):
        """
        Returns mm per rotation, this value is scaled by scaling factor
        """
        return self._mm_per_rotation * self._scaling
    @mm_per_rotation.setter
    def mm_per_rotation(self, value):
        self._mm_per_rotation = value

    @property
    def cycles_per_rotation(self):
        """
        Returns cycles per rotation, this value is scaled by scaling factor
        """
        return self._cycles_per_rotation * self._scaling
    @cycles_per_rotation.setter
    def cycles_per_rotation(self, value):
        self._cycles_per_rotation = value

    @property
    def pwm_value(self):
        """
        Returns pwm value, this value is scaled by scaling factor
        """
        return self._pwm_value * self._scaling
    @pwm_value.setter
    def pwm_value(self, value):
        self._pwm_value = value

    @property
    def mm_movement(self):
        """
        Returns mm movement, this value is scaled by scaling factor
        """
        return self._mm_movement * self._scaling
    @mm_movement.setter
    def mm_movement(self, value):
        self._mm_movement = value

    @property
    def delta_movement(self):
        """
        Returns delta movement, this value is scaled by scaling factor
        """
        return self._delta_movement * self._scaling
    @delta_movement.setter
    def delta_movement(self, value):
        self._delta_movement = value

    @property
    def scaling(self):
        """
        Return scaling factor
        """
        return self._scaling
    @scaling.setter
    def scaling(self, value):
        self._scaling = value

class Espooler:
    """
    This class is used to drive espooler for a lane when loading/unloading and has print forward assist logic.

    Parameters
    ----------------
    name: string
        Lane name of espooler
    config : object
        Configuration object containing settings

    """
    def __init__(self, name, config):
        self.name                   = name
        self.printer                = config.get_printer()
        self.afc                    = self.printer.lookup_object("AFC")
        self.logger                 = self.afc.logger
        self.reactor                = self.printer.get_reactor()
        self.callback_timer         = self.reactor.register_timer( self.timer_callback )    # Defaults to never trigger

        self.afc_motor_rwd          = config.get("afc_motor_rwd", None)                     # Reverse pin on MCU for spoolers
        self.afc_motor_fwd          = config.get("afc_motor_fwd", None)                     # Forwards pin on MCU for spoolers
        self.afc_motor_enb          = config.get("afc_motor_enb", None)                     # Enable pin on MCU for spoolers

        # Forward multiplier to apply to rpm
        self.rwd_speed_multi        = config.getfloat("rwd_speed_multiplier",   0.5)
        # Reverse multiplier to apply to rpm
        self.fwd_speed_multi        = config.getfloat("fwd_speed_multiplier",   0.5)
        # Time to wait between breaking n20 motors(nSleep/FWD/RWD all 1) and then releasing the break to allow coasting. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.n20_break_delay_time   = config.getfloat("n20_break_delay_time",   None)
        # Number of seconds to wait before checking filament movement for espooler assist. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.timer_delay            = config.getfloat("timer_delay",            None)
        # Setting to True enables espooler assist while printing. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.enable_assist          = config.getboolean("enable_assist",        None)
        # Turns on/off debug messages to console. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.debug                  = config.getboolean("debug",                None)
        # Setting to True enables full speed espoolers for kick_start_time amount. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.enable_kick_start      = config.getboolean("enable_kick_start",    None)

        self.past_extruder_position = -1

        self.espooler_values        = Espooler_values(config)

        if self.afc_motor_rwd is not None:
            self.afc_motor_rwd = AFCassistMotor(config, "rwd")
        if self.afc_motor_fwd is not None:
            self.afc_motor_fwd = AFCassistMotor(config, "fwd")
            # Only register macros if forward pin is defined
            self.afc.gcode.register_mux_command("SET_ESPOOLER_VALUES"       , "LANE", self.name, self.cmd_SET_ESPOOLER_VALUES,      desc=self.cmd_SET_ESPOOLER_VALUES_help)
            self.afc.gcode.register_mux_command("TEST_ESPOOLER_ASSIST"      , "LANE", self.name, self.cmd_TEST_ESPOOLER_ASSIST,     desc=self.cmd_TEST_ESPOOLER_ASSIST_help)
            self.afc.gcode.register_mux_command("ENABLE_ESPOOLER_ASSIST"    , "LANE", self.name, self.cmd_ENABLE_ESPOOLER_ASSIST,   desc=self.cmd_ENABLE_ESPOOLER_ASSIST_help)
            self.afc.gcode.register_mux_command("DISABLE_ESPOOLER_ASSIST"   , "LANE", self.name, self.cmd_DISABLE_ESPOOLER_ASSIST,  desc=self.cmd_DISABLE_ESPOOLER_ASSIST_help)
        if self.afc_motor_enb is not None:
            self.afc_motor_enb = AFCassistMotor(config, "enb")

    def handle_connect(self, unit_obj):
        """
        Should only be called during handle_connect callback to update values from unit. If values are not set per
        lane this function will update values from their unit.
        """
        self.espooler_values.handle_connect(unit_obj)

        if self.n20_break_delay_time    is None: self.n20_break_delay_time  = unit_obj.n20_break_delay_time
        if self.timer_delay             is None: self.timer_delay           = unit_obj.timer_delay
        if self.enable_assist           is None: self.enable_assist         = unit_obj.enable_assist
        if self.debug                   is None: self.debug                 = unit_obj.debug
        if self.enable_kick_start       is None: self.enable_kick_start     = unit_obj.enable_kick_start

    def timer_callback(self, eventtime):
        """
        Callback function that checks to see how far filament moved since last check. If filament has moved more than delta_movement
        espooler is activated.

        :param eventtime: Reactor time when callback was called
        :return float   : Time when to call the callback again
        """
        if self.enable_assist and self.afc.function.in_print() and not self.afc.function.is_paused() and not self.afc.in_toolchange:
            extruder_pos = self.afc.function.get_extruder_pos( eventtime, self.past_extruder_position )
            delta_length = extruder_pos - self.past_extruder_position

            if -1 == self.past_extruder_position:
                self.past_extruder_position = extruder_pos

            elif delta_length > self.espooler_values.delta_movement:
                self.past_extruder_position = extruder_pos
                self.do_assist_move()

            if self.debug:
                self.logger.info(f"Timer Callback {eventtime:0.03f} e:{extruder_pos:0.03f} d:{delta_length:0.03f} p:{self.past_extruder_position:0.03f}")

        return self.reactor.monotonic() + self.timer_delay

    def _kick_start(self, reverse=False):
        """
        Helper function to perform a kick start to help with spool movement

        :param reverse: When set to True, moves espooler in reverse direction
        :return float: Print time with kick_start_time offset
        """
        print_time = self.afc.toolhead.get_last_move_time()

        if reverse:
            self.move_reverse(print_time, 1)
        else:
            self.move_forwards(print_time, 1)
        print_time += self.espooler_values.kick_start_time

        return print_time

    def set_enable_pin(self, print_time, value):
        """
        Helper function to set enable pin if its defined

        :param print_time: This value should be a float and is a time when to set the pin
        :param value: This value should be either 0 to disable or 1 to enable pin
        """
        if self.afc_motor_enb is not None:
            self.afc_motor_enb._set_pin( print_time, value)

    def do_assist_move(self, movement=100):
        """
        Helper function to perform assist move while printing

        :param movement: Amount in mm to move spool
        """
        print_time = self._kick_start()
        time = print_time

        self.move_forwards( print_time, self.espooler_values.pwm_value )
        print_time += self.espooler_values.cruise_time

        self.afc_motor_fwd._set_pin( print_time, 0)
        self.set_enable_pin( print_time, 0)

        if self.debug:
            self.logger.debug(f"Cruise time: {self.espooler_values.cruise_time:0.03f} {time:0.03f} {print_time:0.03f}")

    def move_forwards(self, print_time, value):
        """
        Helper function to set PWM value to forward pin

        :param print_time: This value should be a float and is a time when to set the pin
        :param value: This value should be a float between 0.0 and 1.0
        """
        self.set_enable_pin(print_time, 1)
        self.afc_motor_fwd._set_pin(print_time, value)

    def move_reverse(self, print_time, value):
        """
        Helper function to set PWM value to reverse pin

        :param print_time: This value should be a float and is a time when to set the pin
        :param value: This value should be a float between 0.0 and 1.0
        """
        self.set_enable_pin(print_time, 1)
        self.afc_motor_rwd._set_pin(print_time, value)

    def assist(self, value):
        """
        This function is for setting espooler FWD/RWD/EN signals. FWD/RWD is dependent on the value that is
        passed in.  < 0 for RWD, > 0 for FWD and 0 for disable

        :param value: Direction and PWM value to set espooler pins. < 0 RWD, > 0 FWD and 0 disable and enable espooler braking
        """
        reverse = False
        print_time = self.afc.toolhead.get_last_move_time()
        if self.afc_motor_rwd is None:
            return

        if value < 0:
            value *= -1
            assist_motor=self.afc_motor_rwd
            reverse = True
        elif value > 0:
            if self.afc_motor_fwd is None:
                return
            assist_motor=self.afc_motor_fwd
        elif value == 0:
            self.break_espooler()
            return

        value /= assist_motor.scale
        if not assist_motor.is_pwm and value not in [0., 1.]:
            if value > 0: value = 1
        if self.afc_motor_enb is not None:
            enable = 1 if value != 0 else 0

            self.afc_motor_enb._set_pin(print_time, enable)

        if self.enable_kick_start:
            print_time = self._kick_start(reverse)
        assist_motor._set_pin(print_time, value)

    def break_espooler(self):
        """
        Helper function to "brake" n20 motors to hopefully help with keeping down backfeeding into MCU board
        """
        print_time = self.afc.toolhead.get_last_move_time()
        if self.afc_motor_enb is not None:
            self.afc_motor_rwd._set_pin(print_time, 1)
            self.set_enable_pin(print_time, 1)
            if self.afc_motor_fwd is not None:
                self.afc_motor_fwd._set_pin(print_time, 1)

            # Forward predict delay time instead of adding reactor pause in code
            print_time += self.n20_break_delay_time

            self.set_enable_pin(print_time, 0)
            self.afc_motor_rwd._set_pin(print_time, 0)
            if self.afc_motor_fwd is not None:
                self.afc_motor_fwd._set_pin(print_time, 0)
        else:
            self.afc_motor_rwd._set_pin(print_time, 0)

    def enable_timer(self):
        """
        Enables espooler timer if enable_assist variable is True. This should be called after loading a lane
        into toolhead.
        """

        # Checking to see if forward pin is defined, return if it's not defined
        if self.afc_motor_fwd is None: return

        self.past_extruder_position = -1
        if self.enable_assist:
            if self.debug: self.logger.info(f"{self.name} espooler timer enabled")
            self.reactor.update_timer( self.callback_timer, self.reactor.monotonic() + self.timer_delay )

    def disable_timer(self):
        """
        Disables callback function for moving espooler. This should be called before unload a lane.
        """

        # Checking to see if forward pin is defined, return if it's not defined
        if self.afc_motor_fwd is None: return

        self.past_extruder_position = -1
        self.reactor.update_timer( self.callback_timer, self.reactor.NEVER)

    ### MACROS ###
    cmd_TEST_ESPOOLER_ASSIST_help="Test espooler print assist for a specified lane"
    def cmd_TEST_ESPOOLER_ASSIST(self, gcmd):
        """
        Macro call to test espooler print assist to see how current values work

        USAGE
        -----
        `TEST_ESPOOLER_ASSIST LANE=<lane_name>`

        Example
        -----
        ```
        TEST_ESPOOLER_ASSIST LANE=lane1
        ```
        """
        self.do_assist_move(100)

    cmd_ENABLE_ESPOOLER_ASSIST_help="Enabled espooler print assist for a specified lane, this can be used while printing"
    def cmd_ENABLE_ESPOOLER_ASSIST(self, gcmd):
        """
        Macro call to enable espooler print assist

        USAGE
        -----
        `ENABLE_ESPOOLER_ASSIST LANE=<lane_name>`

        Example
        -----
        ```
        ENABLE_ESPOOLER_ASSIST LANE=lane1
        ```
        """

        self.enable_assist = True
        if self.afc.function.get_current_lane() == self.name:
            self.enable_timer()
            self.logger.info(f"Espooler assist enabled for {self.name}")
        else:
            self.logger.info(f"{self.name} currently not loaded only enabling assist, not enabling timer")

    cmd_DISABLE_ESPOOLER_ASSIST_help="Disables espooler print assist for a specified lane, this can be used while printing"
    def cmd_DISABLE_ESPOOLER_ASSIST(self, gcmd):
        """
        Macro call to disable espooler print assist

        USAGE
        -----
        `DISABLE_ESPOOLER_ASSIST LANE=<lane_name>`

        Example
        -----
        ```
        DISABLE_ESPOOLER_ASSIST LANE=lane1
        ```
        """
        self.disable_timer()
        self.enable_assist = False
        self.logger.info(f"Espooler assist disabled for {self.name}")

    cmd_SET_ESPOOLER_VALUES_help="Macro for setting/updating espooler values without having to restart klipper."
    def cmd_SET_ESPOOLER_VALUES( self, gcmd ):
        """
        Macro to allow updating espooler print assist values. If optional value is not passed, current values will be used.

        Optional Values
        ----
        BREAK_DELAY - Time in seconds to wait between breaking n20 motors(nSleep/FWD/RWD all 1) and then releasing the break to allow coasting.
        KICK_START_TIME - Time in seconds to enable spooler at full speed to help with getting the spool to spin
        MM_PER_ROTATION - Distance per full rotation in mm
        CYCLES_PER_ROTATION - Cycles per rotation in milliseconds
        PWM_VALUE - PWM cycle time
        MM_MOVEMENT - Amount to move in mm once filament has moved by delta movement amount
        DELTA_MOVEMENT - Delta amount in mm from last move to trigger assist
        SPOOLRATE - Scaling factor for the following variables: kick_start_time, mm_per_rotation, cycles_per_rotation, pwm_value, delta_movement, mm_movement
        TIMER_DELAY - Number of seconds to wait before checking filament movement for espooler assist
        ENABLE_ASSIST - Setting to True enables espooler assist while printing
        DEBUG - Turns on/off debug messages to console
        ENABLE_KICK_START - Setting to True enables full speed espoolers for kick_start_time amount

        USAGE
        -----
        `SET_ESPOOLER_VALUES LANE=<lane_name> DEBUG=<True/False> ENABLE_ASSIST=<True/False> ...(other optional values)`

        Example
        -----
        ```
        `SET_ESPOOLER_VALUES LANE=lane1 DEBUG=True ENABLE_ASSIST=True`
        ```
        """
        self.n20_break_delay_time                   = gcmd.get_float("BREAK_DELAY"          , self.n20_break_delay_time)
        self.espooler_values.kick_start_time        = gcmd.get_float("KICK_START_TIME"      , self.espooler_values._kick_start_time)
        self.espooler_values.mm_per_rotation        = gcmd.get_float("MM_PER_ROTATION"      , self.espooler_values._mm_per_rotation)
        self.espooler_values.cycles_per_rotation    = gcmd.get_float("CYCLES_PER_ROTATION"  , self.espooler_values._cycles_per_rotation)
        self.espooler_values.pwm_value              = gcmd.get_float("PWM_VALUE"            , self.espooler_values._pwm_value)
        self.espooler_values.mm_movement            = gcmd.get_float("MM_MOVEMENT"          , self.espooler_values._mm_movement)
        self.espooler_values.delta_movement         = gcmd.get_float("DELTA_MOVEMENT"       , self.espooler_values._delta_movement)
        self.espooler_values.scaling                = gcmd.get_float("SPOOLRATE"            , self.espooler_values._scaling)
        self.timer_delay                            = gcmd.get_float("TIMER_DELAY"          , self.timer_delay)
        self.enable_assist                          = bool(gcmd.get_int("ENABLE_ASSIST"     , self.enable_assist))
        self.debug                                  = bool(gcmd.get_int("DEBUG"             , self.debug))
        self.enable_kick_start                      = bool(gcmd.get_int("ENABLE_KICK_START" , self.enable_kick_start))

        # update cruise time with new values
        self.espooler_values.cruise_time = self.espooler_values.calculate_cruise_time( self.espooler_values._mm_movement )

        self.logger.info(f"Espooler values updated for {self.name}, please manually save values in config file.")
