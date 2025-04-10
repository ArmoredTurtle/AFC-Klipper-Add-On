# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from contextlib import contextmanager
from . import AFC_assist
from configfile import error
try:
    from extras.AFC_utils import add_filament_switch
except:
    raise error("Error trying to import AFC_utils, please rerun install-afc.sh script in your AFC-Klipper-Add-On directory then restart klipper")

#LED
BACKGROUND_PRIORITY_CLOCK = 0x7fffffff00000000
BIT_MAX_TIME=.000004
RESET_MIN_TIME=.000050
MAX_MCU_SIZE = 500  # Sanity check on LED chain length

class AFCExtruderStepper:
    def __init__(self, config):
        self.printer            = config.get_printer()
        self.AFC                = self.printer.lookup_object('AFC')
        self.gcode              = self.printer.lookup_object('gcode')
        self.reactor            = self.printer.get_reactor()
        self.extruder_stepper   = None
        self.logger             = self.AFC.logger
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

        self.unit_obj           = None
        self.hub_obj            = None
        self.buffer_obj         = None
        self.extruder_obj       = None

        #stored status variables
        self.fullname           = config.get_name()
        self.name               = self.fullname.split()[-1]
        self.tool_loaded        = False
        self.loaded_to_hub      = False
        self.spool_id           = None
        self.material           = None
        self.color              = None
        self.weight             = None
        self.material           = None
        self.extruder_temp      = None
        self.runout_lane        = 'NONE'
        self.status             = None
        self.multi_hubs_found   = False
        self.drive_stepper      = None
        self.selector_stepper   = None
        unit                    = config.get('unit')                                    # Unit name(AFC_BoxTurtle/NightOwl/etc) that belongs to this stepper.
        # Overrides buffers set at the unit level
        self.hub 				= config.get('hub',None)                                # Hub name(AFC_hub) that belongs to this stepper, overrides hub that is set in unit(AFC_BoxTurtle/NightOwl/etc) section.
        # Overrides buffers set at the unit and extruder level
        self.buffer_name        = config.get("buffer", None)                            # Buffer name(AFC_buffer) that belongs to this stepper, overrides buffer that is set in extruder(AFC_extruder) or unit(AFC_BoxTurtle/NightOwl/etc) sections.
        self.unit               = unit.split(':')[0]
        try:
            self.index              = int(unit.split(':')[1])
        except:
            self.index              = 0
            pass

        self.extruder_name      = config.get('extruder', None)                          # Extruder name(AFC_extruder) that belongs to this stepper, overrides extruder that is set in unit(AFC_BoxTurtle/NightOwl/etc) section.
        self.map                = config.get('cmd','NONE')
        self.led_index 			= config.get('led_index', None)                         # LED index of lane in chain of lane LEDs
        self.led_name 			= config.get('led_name',None)
        self.led_fault 			= config.get('led_fault',None)                          # LED color to set when faults occur in lane        (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.led_ready 			= config.get('led_ready',None)                          # LED color to set when lane is ready               (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.led_not_ready 		= config.get('led_not_ready',None)                      # LED color to set when lane not ready              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.led_loading 		= config.get('led_loading',None)                        # LED color to set when lane is loading             (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.led_prep_loaded 	= config.get('led_loading',None)                        # LED color to set when lane is loaded              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.led_unloading 		= config.get('led_unloading',None)                      # LED color to set when lane is unloading           (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.led_tool_loaded 	= config.get('led_tool_loaded',None)                    # LED color to set when lane is loaded into tool    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section

        self.long_moves_speed 	= config.getfloat("long_moves_speed", None)             # Speed in mm/s to move filament when doing long moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.long_moves_accel 	= config.getfloat("long_moves_accel", None)             # Acceleration in mm/s squared when doing long moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.short_moves_speed 	= config.getfloat("short_moves_speed", None)            # Speed in mm/s to move filament when doing short moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.short_moves_accel	= config.getfloat("short_moves_accel", None)            # Acceleration in mm/s squared when doing short moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.short_move_dis 	= config.getfloat("short_move_dis", None)               # Move distance in mm for failsafe moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.max_move_dis       = config.getfloat("max_move_dis", None)                 # Maximum distance to move filament. AFC breaks filament moves over this number into multiple moves. Useful to lower this number if running into timer too close errors when doing long filament moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
        self.n20_break_delay_time= config.getfloat("n20_break_delay_time", None)        # Time to wait between breaking n20 motors(nSleep/FWD/RWD all 1) and then releasing the break to allow coasting. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section

        self.dist_hub           = config.getfloat('dist_hub', 60)                       # Bowden distance between Box Turtle extruder and hub
        self.park_dist          = config.getfloat('park_dist', 10)                      # Currently unused

        self.load_to_hub        = config.getboolean("load_to_hub", self.AFC.load_to_hub) # Fast loads filament to hub when inserted, set to False to disable. Setting here overrides global setting in AFC.cfg
        self.enable_sensors_in_gui  = config.getboolean("enable_sensors_in_gui", self.AFC.enable_sensors_in_gui) # Set to True to show prep and load sensors switches as filament sensors in mainsail/fluidd gui, overrides value set in AFC.cfg
        self.sensor_to_show         = config.get("sensor_to_show", None)                # Set to prep to only show prep sensor, set to load to only show load sensor. Do not add if you want both prep and load sensors to show in web gui

        self.assisted_unload = config.getboolean("assisted_unload", None) # If True, the unload retract is assisted to prevent loose windings, especially on full spools. This can prevent loops from slipping off the spool. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section

        self.printer.register_event_handler("AFC_unit_{}:connect".format(self.unit),self.handle_unit_connect)

        self.config_dist_hub = self.dist_hub

        # lane triggers
        buttons = self.printer.load_object(config, "buttons")
        self.prep = config.get('prep', None)                                                        # MCU pin for prep trigger
        self.prep_state = False
        if self.prep is not None:
            buttons.register_buttons([self.prep], self.prep_callback)

        self.load = config.get('load', None)                                                        # MCU pin load trigger
        self.load_state = False
        if self.load is not None:
            buttons.register_buttons([self.load], self.load_callback)
        else: self.load_state = True

        # Respoolers
        self.afc_motor_rwd = config.get('afc_motor_rwd', None)                                      # Reverse pin on MCU for spoolers
        self.afc_motor_fwd = config.get('afc_motor_fwd', None)                                      # Forwards pin on MCU for spoolers
        self.afc_motor_enb = config.get('afc_motor_enb', None)                                      # Enable pin on MCU for spoolers
        if self.afc_motor_rwd is not None:
            self.afc_motor_rwd = AFC_assist.AFCassistMotor(config, 'rwd')
        if self.afc_motor_fwd is not None:
            self.afc_motor_fwd = AFC_assist.AFCassistMotor(config, 'fwd')
        if self.afc_motor_enb is not None:
            self.afc_motor_enb = AFC_assist.AFCassistMotor(config, 'enb')

        # self.filament_diameter = config.getfloat("filament_diameter", 1.75)                         # Diameter of filament being used
        # self.filament_density = config.getfloat("filament_density", 1.24)                           # Density of filament being used
        # self.inner_diameter = config.getfloat("spool_inner_diameter", 100)                          # Inner diameter in mm
        # self.outer_diameter = config.getfloat("spool_outer_diameter", 200)                          # Outer diameter in mm
        # self.empty_spool_weight = config.getfloat("empty_spool_weight", 190)                        # Empty spool weight in g
        # self.remaining_weight = config.getfloat("spool_weight", 1000)                               # Remaining spool weight in g
        # self.max_motor_rpm = config.getfloat("assist_max_motor_rpm", 500)                           # Max motor RPM
        # self.diameter_range = self.outer_diameter - self.inner_diameter  # Range for effective diameter
        self.rwd_speed_multi = config.getfloat("rwd_speed_multiplier", 0.5)                         # Multiplier to apply to rpm
        self.fwd_speed_multi = config.getfloat("fwd_speed_multiplier", 0.5)                         # Multiplier to apply to rpm


        # Defaulting to false so that extruder motors to not move until PREP has been called
        self._afc_prep_done = False

        if self.enable_sensors_in_gui:
            if self.prep is not None and (self.sensor_to_show is None or self.sensor_to_show == 'prep'):
                self.prep_filament_switch_name = "filament_switch_sensor {}_prep".format(self.name)
                self.fila_prep = add_filament_switch(self.prep_filament_switch_name, self.prep, self.printer )

            if self.load is not None and (self.sensor_to_show is None or self.sensor_to_show == 'load'):
                self.load_filament_switch_name = "filament_switch_sensor {}_load".format(self.name)
                self.fila_load = add_filament_switch(self.load_filament_switch_name, self.load, self.printer )
        self.connect_done = False
        self.prep_active = False
        self.last_prep_time = 0

    def __str__(self):
        return self.name

    def _handle_ready(self):
        """
        Handles klippy:ready callback and verifies that steppers have units defined in their config
        """
        if self.unit_obj is None:
            raise error("Unit {unit} is not defined in your configuration file. Please defined unit ex. [AFC_BoxTurtle {unit}]".format(unit=self.unit))

        if self.led_index is not None:
            # Verify that LED config is found
            error_string, led = self.AFC.FUNCTION.verify_led_object(self.led_index)
            if led is None:
                raise error(error_string)

    def handle_unit_connect(self, unit_obj):
        """
        Callback from <unit_name>:connect to verify units/hub/buffer/extruder object. Errors out if user specified names and they do not exist in their configuration
        """
        # Saving reference to unit
        self.unit_obj = unit_obj
        self.buffer_obj = self.unit_obj.buffer_obj

        # Registering lane name in unit
        self.unit_obj.lanes[self.name] = self
        self.AFC.lanes[self.name] = self

        self.hub_obj = self.unit_obj.hub_obj
        if self.hub != 'direct':
            if self.hub is not None:
                try:
                    self.hub_obj = self.printer.lookup_object("AFC_hub {}".format(self.hub))
                except:
                    error_string = 'Error: No config found for hub: {hub} in [AFC_stepper {stepper}]. Please make sure [AFC_hub {hub}] section exists in your config'.format(
                    hub=self.hub, stepper=self.name )
                    raise error(error_string)
            elif self.hub_obj is None:
                # Check to make sure at least 1 hub exists in config, if not error out with message
                if len(self.AFC.hubs) == 0:
                    error_string = "Error: AFC_hub not found in configuration please make sure there is a [AFC_hub <hub_name>] defined in your configuration"
                    raise error(error_string)
                # Setting hub to first hub in AFC hubs dictionary
                if len(self.AFC.hubs) > 0:
                    self.hub_obj = next(iter(self.AFC.hubs.values()))
                # Set flag to warn during prep that multiple hubs were found
                if len(self.AFC.hubs) > 1:
                    self.multi_hubs_found = True

            # Assigning hub name just in case stepper is using hub defined in units config
            self.hub = self.hub_obj.name
            self.hub_obj.lanes[self.name] = self
        else:
            self.hub_obj = lambda: None
            self.hub_obj.state = False

        self.extruder_obj = self.unit_obj.extruder_obj
        if self.extruder_name is not None:
            try:
                self.extruder_obj = self.printer.lookup_object('AFC_extruder {}'.format(self.extruder_name))
            except:
                error_string = 'Error: No config found for extruder: {extruder} in [AFC_stepper {stepper}]. Please make sure [AFC_extruder {extruder}] section exists in your config'.format(
                    extruder=self.extruder_name, stepper=self.name )
                raise error(error_string)
        elif self.extruder_obj is None:
            error_string = "Error: Extruder has not been configured for stepper {name}, please add extruder variable to either [AFC_stepper {name}] or [AFC_{unit_type} {unit_name}] in your config file".format(
                        name=self.name, unit_type=self.unit_obj.type.replace("_", ""), unit_name=self.unit_obj.name)
            raise error(error_string)

        # Assigning extruder name just in case stepper is using extruder defined in units config
        self.extruder_name = self.extruder_obj.name
        self.extruder_obj.lanes[self.name] = self

        # Use buffer defined in stepper and override buffers that maybe set at the UNIT or extruder levels
        self.buffer_obj = self.unit_obj.buffer_obj
        if self.buffer_name is not None:
            try:
                self.buffer_obj = self.printer.lookup_object("AFC_buffer {}".format(self.buffer_name))
            except:
                error_string = 'Error: No config found for buffer: {buffer} in [AFC_stepper {stepper}]. Please make sure [AFC_buffer {buffer}] section exists in your config'.format(
                    buffer=self.buffer_name, stepper=self.name )
                raise error(error_string)

        # Checking if buffer was defined in extruder if not defined in unit/stepper
        elif self.buffer_obj is None and self.extruder_obj.tool_start == "buffer":
            if self.extruder_obj.buffer_name is not None:
                self.buffer_obj = self.printer.lookup_object("AFC_buffer {}".format(self.extruder_obj.buffer_name))
            else:
                error_string = 'Error: Buffer was defined as tool_start in [AFC_extruder {extruder}] config, but buffer variable has not been configured. Please add buffer variable to either [AFC_extruder {extruder}], [AFC_stepper {name}] or [AFC_{unit_type} {unit_name}] section in your config file'.format(
                    extruder=self.extruder_obj.name, name=self.name, unit_type=self.unit_obj.type.replace("_", ""), unit_name=self.unit_obj.name )
                raise error(error_string)

        # Valid to not have a buffer defined, check to make sure object exists before adding lane to buffer
        if self.buffer_obj is not None:
            if self.extruder_obj.tool_start == "buffer" and self.buffer_obj.belay:
                raise error("Belay cannot be used in place of a toolhead sensor, only turtleneck buffer can do this.")

            self.buffer_obj.lanes[self.name] = self
            # Assigning buffer name just in case stepper is using buffer defined in units/extruder config
            self.buffer_name = self.buffer_obj.name

        self.get_steppers()

        if self.led_name is None: self.led_name = self.unit_obj.led_name
        if self.led_fault is None: self.led_fault = self.unit_obj.led_fault
        if self.led_ready is None: self.led_ready = self.unit_obj.led_ready
        if self.led_not_ready is None: self.led_not_ready = self.unit_obj.led_not_ready
        if self.led_loading is None: self.led_loading = self.unit_obj.led_loading
        if self.led_prep_loaded is None: self.led_prep_loaded = self.unit_obj.led_prep_loaded
        if self.led_unloading is None: self.led_unloading = self.unit_obj.led_unloading
        if self.led_tool_loaded is None: self.led_tool_loaded = self.unit_obj.led_tool_loaded

        if self.long_moves_speed is None: self.long_moves_speed = self.unit_obj.long_moves_speed
        if self.long_moves_accel is None: self.long_moves_accel = self.unit_obj.long_moves_accel
        if self.short_moves_speed is None: self.short_moves_speed = self.unit_obj.short_moves_speed
        if self.short_moves_accel is None: self.short_moves_accel = self.unit_obj.short_moves_accel
        if self.short_move_dis is None: self.short_move_dis = self.unit_obj.short_move_dis
        if self.max_move_dis is None: self.max_move_dis = self.unit_obj.max_move_dis
        if self.n20_break_delay_time is None: self.n20_break_delay_time = self.unit_obj.n20_break_delay_time

        # Set hub loading speed depending on distance between extruder and hub
        self.dist_hub_move_speed = self.long_moves_speed if self.dist_hub >= 200 else self.short_moves_speed
        self.dist_hub_move_accel = self.long_moves_accel if self.dist_hub >= 200 else self.short_moves_accel

        # Register macros
        self.gcode.register_mux_command('SET_LANE_LOADED',    "LANE", self.name, self.cmd_SET_LANE_LOADED, desc=self.cmd_SET_LANE_LOADED_help)

        self.AFC.gcode.register_mux_command('SET_SPEED_MULTIPLIER',  "LANE", self.name, self.cmd_SET_SPEED_MULTIPLIER,   desc=self.cmd_SET_SPEED_MULTIPLIER_help)
        self.AFC.gcode.register_mux_command('SAVE_SPEED_MULTIPLIER', "LANE", self.name, self.cmd_SAVE_SPEED_MULTIPLIER,  desc=self.cmd_SAVE_SPEED_MULTIPLIER_help)
        self.AFC.gcode.register_mux_command('SET_HUB_DIST',          "LANE", self.name, self.cmd_SET_HUB_DIST,           desc=self.cmd_SET_HUB_DIST_help)
        self.AFC.gcode.register_mux_command('SAVE_HUB_DIST',         "LANE", self.name, self.cmd_SAVE_HUB_DIST,          desc=self.cmd_SAVE_HUB_DIST_help)

        if self.assisted_unload is None: self.assisted_unload = self.unit_obj.assisted_unload

        # Send out event so that macros and be registered properly with valid lane names
        self.printer.send_event("afc_stepper:register_macros", self)

        self.connect_done = True

    def get_steppers(self):
        """
        Helper function to get steppers for lane
        """
        if self.unit_obj.type == "HTLF":
            self.drive_stepper      = self.unit_obj.drive_stepper_obj
            self.selector_stepper   = self.unit_obj.selector_stepper_obj
            self.extruder_stepper   = self.drive_stepper.extruder_stepper

    def brake_n20(self):
        '''
        Helper function to "brake" n20 motors to hopefully help with keeping down backfeeding into MCU board
        '''
        self.AFC.toolhead.register_lookahead_callback(lambda print_time: self.afc_motor_rwd._set_pin(print_time, 1))
        self.AFC.toolhead.register_lookahead_callback(lambda print_time: self.afc_motor_enb._set_pin(print_time, 1))
        if self.afc_motor_fwd is not None:
            self.AFC.toolhead.register_lookahead_callback(lambda print_time: self.afc_motor_fwd._set_pin(print_time, 1))

        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + self.n20_break_delay_time)

        self.AFC.toolhead.register_lookahead_callback(lambda print_time: self.afc_motor_rwd._set_pin(print_time, 0))
        self.AFC.toolhead.register_lookahead_callback(lambda print_time: self.afc_motor_enb._set_pin(print_time, 0))
        if self.afc_motor_fwd is not None:
            self.AFC.toolhead.register_lookahead_callback(lambda print_time: self.afc_motor_fwd._set_pin(print_time, 0))

    def assist(self, value, is_resend=False):
        if self.afc_motor_rwd is None:
            return
        if value < 0:
            value *= -1
            assit_motor=self.afc_motor_rwd
        elif value > 0:
            if self.afc_motor_fwd is None:
                return
            else:
                assit_motor=self.afc_motor_fwd
        elif value == 0:
            if self.afc_motor_enb is not None:
                self.brake_n20()
            else:
                self.AFC.toolhead.register_lookahead_callback(lambda print_time: self.afc_motor_rwd._set_pin(print_time, value))

            return
        value /= assit_motor.scale
        if not assit_motor.is_pwm and value not in [0., 1.]:
            if value > 0:
                value = 1
        if self.afc_motor_enb is not None:
            if value != 0:
                enable = 1
            else:
                enable = 0
            self.AFC.toolhead.register_lookahead_callback(
            lambda print_time: self.afc_motor_enb._set_pin(print_time, enable))

        self.AFC.toolhead.register_lookahead_callback(
            lambda print_time: assit_motor._set_pin(print_time, value))

    @contextmanager
    def assist_move(self, speed, rewind, assist_active=True):
        """
        Starts an assist move and returns a context manager that turns off the assist move when it exist.
        :param speed:         The speed of the move
        :param rewind:        True for a rewind, False for a forward assist
        :param assist_active: Whether to assist
        :return:              the Context manager
        """
        if assist_active:
            if rewind:
                # Calculate Rewind Speed
                value = self.calculate_pwm_value(speed, True) * -1
            else:
                # Calculate Forward Assist Speed
                value = self.calculate_pwm_value(speed)

            # Clamp value to a maximum of 1
            if value > 1:
                value = 1

            self.assist(value)
        try:
            yield
        finally:
            if assist_active:
                self.assist(0)

    def move(self, distance, speed, accel, assist_active=False):
        """
        Move the specified lane a given distance with specified speed and acceleration.
        This function calculates the movement parameters and commands the stepper motor
        to move the lane accordingly.
        Parameters:
        distance (float): The distance to move.
        speed (float): The speed of the movement.
        accel (float): The acceleration of the movement.
        """
        self.unit_obj.select_lane( self )
        with self.assist_move( speed, distance < 0, assist_active):
            self.drive_stepper.move(distance, speed, accel, assist_active)

    def set_afc_prep_done(self):
        """
        set_afc_prep_done function should only be called once AFC PREP function is done. Once this
            function is called it sets afc_prep_done to True. Once this is done the prep_callback function will
            now load once filament is inserted.
        """
        self._afc_prep_done = True

    def _perform_infinite_runout(self):
        """
        Common function for infinite spool runout
            - Unloads current lane and loads the next lane as specified by runout variable.
            - Swaps mapping between current lane and runout lane so correct lane is loaded with T(n) macro
            - Once changeover is successful print is automatically resumed
        """
        self.status = None
        self.AFC.FUNCTION.afc_led(self.AFC.led_not_ready, self.led_index)
        self.logger.info("Infinite Spool triggered for {}".format(self.name))
        empty_LANE = self.AFC.lanes[self.AFC.current]
        change_LANE = self.AFC.lanes[self.runout_lane]
        # Pause printer with manual command
        self.AFC.ERROR.pause_resume.send_pause_command()
        # Saving position after printer is paused
        self.AFC.save_pos()
        # Change Tool and don't restore position. Position will be restored after lane is unloaded
        #  so that nozzle does not sit on print while lane is unloading
        self.AFC.CHANGE_TOOL(change_LANE, restore_pos=False)
        # Change Mapping
        self.gcode.run_script_from_command('SET_MAP LANE={} MAP={}'.format(change_LANE.name, empty_LANE.map))
        # Only continue if a error did not happen
        if not self.AFC.error_state:
            # Eject lane from BT
            self.gcode.run_script_from_command('LANE_UNLOAD LANE={}'.format(empty_LANE.name))
            # Resume pos
            self.AFC.restore_pos()
            # Resume with manual issued command
            self.AFC.ERROR.pause_resume.send_resume_command()
            # Set LED to not ready
            self.AFC.FUNCTION.afc_led(self.led_not_ready, self.led_index)

    def _perform_pause_runout(self):
        """
        Common function to pause print when runout occurs, fully unloads and ejects spool if specified by user
        """
        # Unload if user has set AFC to unload on runout
        if self.unit_obj.unload_on_runout:
            # Pause printer
            self.AFC.ERROR.pause_resume.send_pause_command()
            self.AFC.save_pos()
            # self.gcode.run_script_from_command('PAUSE')
            self.AFC.TOOL_UNLOAD(self)
            if not self.AFC.error_state:
                self.AFC.LANE_UNLOAD(self)
        # Pause print
        self.status = None
        msg = "Runout triggered for lane {} and runout lane is not setup to switch to another lane".format(self.name)
        msg += "\nPlease manually load next spool into toolhead and then hit resume to continue"
        self.AFC.FUNCTION.afc_led(self.AFC.led_not_ready, self.led_index)
        self.AFC.ERROR.AFC_error(msg)

    def load_callback(self, eventtime, state):
        self.load_state = state
        if self.printer.state_message == 'Printer is ready' and self.unit_obj.type == "HTLF":
            self.prep_state = state

            if self.load_state:
                self.AFC.FUNCTION.afc_led(self.led_ready, self.led_index)
            else:
                if self.unit_obj.check_runout(self):
                    # Checking to make sure runout_lane is set and does not equal 'NONE'
                    if  self.runout_lane != 'NONE':
                        self._perform_runout()
                    else:
                        self._perform_pause_runout()
                elif self.status != "calibrating":
                    self.AFC.FUNCTION.afc_led(self.led_not_ready, self.led_index)
                    self.status = None
                    self.loaded_to_hub = False
                    self.AFC.SPOOL._clear_values(self)
                    self.AFC.FUNCTION.afc_led(self.AFC.led_not_ready, self.led_index)

        self.AFC.save_vars()

    def prep_callback(self, eventtime, state):
        self.prep_state = state

        delta_time = eventtime - self.last_prep_time
        self.last_prep_time = eventtime

        if self.prep_active:
            return

        if self.hub =='direct' and not self.AFC.FUNCTION.is_homed():
            self.AFC.ERROR.AFC_error("Please home printer before directly loading to toolhead", False)
            return False

        self.prep_active = True

        # Checking to make sure printer is ready and making sure PREP has been called before trying to load anything
        for i in range(1):
        # Hacky way for do{}while(0) loop, DO NOT return from this for loop, use break instead so that self.prep_state variable gets sets correctly
        #  before exiting function
            if self.printer.state_message == 'Printer is ready' and True == self._afc_prep_done and self.status != 'Tool Unloading':
                # Only try to load when load state trigger is false
                if self.prep_state == True and self.load_state == False:
                    x = 0
                    # Checking to make sure last time prep switch was activated was less than 1 second, returning to keep is printing message from spamming
                    # the console since it takes klipper some time to transition to idle when idle_resume=printing
                    if delta_time < 1.0:
                        break

                    # Check to see if the printer is printing or moving, as trying to load while printer is doing something will crash klipper
                    if self.AFC.FUNCTION.is_printing(check_movement=True):
                        self.AFC.ERROR.AFC_error("Cannot load spools while printer is actively moving or homing", False)
                        break

                    while self.load_state == False and self.prep_state == True and self.load != None:
                        x += 1
                        self.do_enable(True)
                        self.move(10,500,400)
                        self.reactor.pause(self.reactor.monotonic() + 0.1)
                        if x> 40:
                            msg = (' FAILED TO LOAD, CHECK FILAMENT AT TRIGGER\n||==>--||----||------||\nTRG   LOAD   HUB    TOOL')
                            self.AFC.ERROR.AFC_error(msg, False)
                            self.AFC.FUNCTION.afc_led(self.AFC.led_fault, self.led_index)
                            self.status=''
                            break
                    self.status=''

                    # Verify that load state is still true as this would still trigger if prep sensor was triggered and then filament was removed
                    #   This is only really a issue when using direct and still using load sensor
                    if self.hub == 'direct' and self.prep_state:
                        self.AFC.afcDeltaTime.set_start_time()
                        self.AFC.TOOL_LOAD(self)
                        self.material = self.AFC.default_material_type
                        break

                    # Checking if loaded to hub(it should not be since filament was just inserted), if false load to hub. Does a fast load if hub distance is over 200mm
                    if self.load_to_hub and not self.loaded_to_hub and self.load_state and self.prep_state:
                        self.move(self.dist_hub, self.dist_hub_move_speed, self.dist_hub_move_accel, self.dist_hub > 200)
                        self.loaded_to_hub = True

                    self.do_enable(False)
                    if self.load_state == True and self.prep_state == True:
                        self.status = 'Loaded'
                        self.AFC.FUNCTION.afc_led(self.AFC.led_ready, self.led_index)
                        self.material = self.AFC.default_material_type

                elif self.prep_state == False and self.name == self.AFC.current and self.AFC.FUNCTION.is_printing() and self.load_state and self.status != 'ejecting':
                    # Checking to make sure runout_lane is set and does not equal 'NONE'
                    if  self.runout_lane != 'NONE':
                        self._perform_runout()
                    else:
                        self._perform_pause_runout()

                elif self.prep_state == True and self.load_state == True and not self.AFC.FUNCTION.is_printing():
                    message = 'Cannot load {} load sensor is triggered.'.format(self.name)
                    message += '\n    Make sure filament is not stuck in load sensor or check to make sure load sensor is not stuck triggered.'
                    message += '\n    Once cleared try loading again'
                    self.AFC.ERROR.AFC_error(message, pause=False)
                else:
                    self.status = None
                    self.loaded_to_hub = False
                    self.AFC.SPOOL._clear_values(self)
                    self.AFC.FUNCTION.afc_led(self.AFC.led_not_ready, self.led_index)

        self.prep_active = False
        self.AFC.save_vars()

    def do_enable(self, enable):
        self.drive_stepper.do_enable(enable)

    def sync_to_extruder(self, update_current=True):
        """
        Helper function to sync lane to extruder and set print current if specified.

        :param update_current: Sets current to specified print current when True
        """
        self.drive_stepper.sync_to_extruder(self.extruder_name)
        if update_current: self.drive_stepper.set_print_current()

    def unsync_to_extruder(self, update_current=True):
        """
        Helper function to un-sync lane to extruder and set load current if specified.

        :param update_current: Sets current to specified load current when True
        """
        self.drive_stepper.unsync_to_extruder(None)
        if update_current: self.drive_stepper.set_load_current()

    def set_load_current(self):
        """
        Helper function to update TMC current to use run current value
        """
        self.drive_stepper.set_load_current()

    def set_print_current(self):
        """
        Helper function to update TMC current to use print current value
        """
        self.drive_stepper.set_print_current()

    def update_rotation_distance(self, multiplier):
        self.drive_stepper.update_rotation_distance( multiplier )

    def calculate_pwm_value(self, feed_rate, rewind=False):
        return self.drive_stepper.calculate_pwm_value( feed_rate, rewind )

    def set_loaded(self):
        """
        Helper function for setting multiple variables when lane is loaded
        """
        self.tool_loaded = True
        self.AFC.current = self.extruder_obj.lane_loaded = self.name
        self.AFC.current_loading = None
        self.status = 'Tooled'
        self.AFC.SPOOL.set_active_spool(self.spool_id)

    def set_unloaded(self):
        """
        Helper function for setting multiple variables when lane is unloaded
        """
        self.tool_loaded = False
        self.extruder_obj.lane_loaded = ""
        self.status = None
        self.AFC.current = None
        self.AFC.current_loading = None
        self.AFC.SPOOL.set_active_spool( None )

    def enable_buffer(self):
        """
        Enable the buffer if `buffer_name` is set.
        Retrieves the buffer object and calls its `enable_buffer()` method to activate it.
        """
        if self.buffer_obj is not None:
            self.buffer_obj.enable_buffer()

    def disable_buffer(self):
        """
        Disable the buffer if `buffer_name` is set.
        Calls the buffer's `disable_buffer()` method to deactivate it.
        """
        if self.buffer_obj is not None:
            self.buffer_obj.disable_buffer()

    def buffer_status(self):
        """
        Retrieve the current status of the buffer.
        If `buffer_name` is set, returns the buffer's status using `buffer_status()`.
        Otherwise, returns None.
        """
        if self.buffer_obj is not None:
            return self.buffer_obj.buffer_status()

        else: return None

    def get_toolhead_pre_sensor_state(self):
        """
        Helper function that returns current state of toolhead pre sensor or buffer if user has extruder setup for ramming

        returns Status of toolhead pre sensor or the current buffer advance state
        """
        if self.extruder_obj.tool_start == "buffer":
            return self.buffer_obj.advance_state
        else:
            return self.extruder_obj.tool_start_state

    def get_trailing(self):
        """
        Helper function to get trailing status, returns none if buffer is not defined
        """
        if self.buffer_obj is not None:
            return self.buffer_obj.trailing_state
        else: return None

    cmd_SET_LANE_LOADED_help = "Sets current lane as loaded to toolhead, useful when manually loading lanes during prints if AFC detects an error when trying to unload/load a lane"
    def cmd_SET_LANE_LOADED(self, gcmd):
        """
        This macro handles manually setting a lane loaded into the toolhead. This is useful when manually loading lanes
        during prints after AFC detects an error when loading/unloading and pauses.

        If there is a lane already loaded this macro will also desync that lane extruder from the toolhead extruder
        and set its values and led appropriately.

        Retrieves the lane specified by the 'LANE' parameter and sets the appropriate values in AFC to continue using the lane.

        Usage
        -----
        `SET_LANE_LOADED LANE=<lane>`

        Example
        -------
        ```
        SET_LANE_LOADED LANE=lane1
        ```
        """
        if not self.load_state:
            self.AFC.ERROR.AFC_error("Lane:{} is not loaded, cannot set loaded to toolhead for this lane.".format(self.name), pause=False)
            return

        self.AFC.FUNCTION.unset_lane_loaded()

        self.set_loaded()
        self.sync_to_extruder()
        self.AFC.FUNCTION.handle_activate_extruder()
        self.AFC.save_vars()
        self.unit_obj.select_lane(self)
        self.logger.info("Manually set {} loaded to toolhead".format(self.name))

    cmd_SET_SPEED_MULTIPLIER_help = "Gives ability to set fwd_speed_multiplier or rwd_speed_multiplier values without having to update config and restart"
    def cmd_SET_SPEED_MULTIPLIER(self, gcmd):
        """
        Macro call to update fwd_speed_multiplier or rwd_speed_multiplier values without having to set in config and restart klipper. This macro allows adjusting
        these values while printing. Multiplier values must be between 0.0 - 1.0

        Use `FWD` variable to set forward multiplier, use `RWD` to set reverse multiplier

        After running this command run `SAVE_SPEED_MULTIPLIER LANE=<lane_name>` to save value to config file

        Usage
        -----
        `SET_SPEED_MULTIPLIER LANE=<lane_name> FWD=<fwd_multiplier> RWD=<rwd_multiplier>`

        Example
        -----
        ```
        SET_SPEED_MULTIPLIER LANE=lane1 RWD=0.9
        ```
        """
        updated = False
        old_fwd_value = self.fwd_speed_multi
        old_rwd_value = self.rwd_speed_multi

        self.fwd_speed_multi = gcmd.get_float("FWD", self.fwd_speed_multi, minval=0.0, maxval=1.0)
        self.rwd_speed_multi = gcmd.get_float("RWD", self.rwd_speed_multi, minval=0.0, maxval=1.0)

        if self.fwd_speed_multi != old_fwd_value:
            self.logger.info("{name} forward speed multiplier set, New: {new}, Old: {old}".format(name=self.name, new=self.fwd_speed_multi, old=old_fwd_value))
            updated = True

        if self.rwd_speed_multi != old_rwd_value:
            self.logger.info("{name} reverse speed multiplier set, New: {new}, Old: {old}".format(name=self.name, new=self.rwd_speed_multi, old=old_rwd_value))
            updated = True

        if updated:
            self.logger.info("Run SAVE_SPEED_MULTIPLIER LANE={} to save values to config file".format(self.name))

    cmd_SAVE_SPEED_MULTIPLIER_help = "Saves fwd_speed_multiplier and rwd_speed_multiplier values to config file "
    def cmd_SAVE_SPEED_MULTIPLIER(self, gcmd):
        """
        Macro call to write fwd_speed_multiplier and rwd_speed_multiplier variables to config file for specified lane.

        Usage
        -----
        `SAVE_SPEED_MULTIPLIER LANE=<lane_name>`

        Example
        -----
        ```
        SAVE_SPEED_MULTIPLIER LANE=lane1
        ```
        """
        self.AFC.FUNCTION.ConfigRewrite(self.fullname, 'fwd_speed_multiplier',  self.fwd_speed_multi, '')
        self.AFC.FUNCTION.ConfigRewrite(self.fullname, 'rwd_speed_multiplier',  self.rwd_speed_multi, '')

    cmd_SET_HUB_DIST_help = "Helper to dynamically set distance between a lanes extruder and hub"
    def cmd_SET_HUB_DIST(self, gcmd):
        """
        This function adjusts the distance between a lanes extruder and hub. Adding +/- in front of the length will
        increase/decrease length by that amount. To reset length back to config value, pass in `reset` for length to
        reset to value in config file.

        Usage
        -----
        `SET_HUB_DIST LANE=<lane_name> LENGTH=+/-<fwd_multiplier>`

        Example
        -----
        ```
        SET_HUB_DIST LANE=lane1 LENGTH=+100
        ```
        """
        old_dist_hub = self.dist_hub

        length = gcmd.get("LENGTH", self.dist_hub)

        if length != old_dist_hub:
            self.dist_hub = self.AFC.FUNCTION._calc_length(self.config_dist_hub, self.dist_hub, length)
        msg =  "//{} dist_hub:\n".format(self.name)
        msg += '//   Config Length:   {}\n'.format(self.config_dist_hub)
        msg += '//   Previous Length: {}\n'.format(old_dist_hub)
        msg += '//   New Length:      {}\n'.format(self.dist_hub)
        self.logger.raw(msg)
        self.logger.info("Run SAVE_HUB_DIST LANE={} to save value to config file".format(self.name))

    cmd_SAVE_HUB_DIST_help = "Saves dist_hub value to config file "
    def cmd_SAVE_HUB_DIST(self, gcmd):
        """
        Macro call to write dist_hub variable to config file for specified lane.

        Usage
        -----
        `SAVE_HUB_DIST LANE=<lane_name>`

        Example
        -----
        ```
        SAVE_HUB_DIST LANE=lane1
        ```
        """
        self.AFC.FUNCTION.ConfigRewrite(self.fullname, 'dist_hub',  self.dist_hub, '')

    def get_status(self, eventtime=None):
        response = {}
        if not self.connect_done: return response
        response['name'] = self.name
        response['unit'] = self.unit
        response['hub'] = self.hub
        response['extruder'] = self.extruder_name
        response['buffer'] = self.buffer_name
        response['buffer_status'] = self.buffer_status()
        response['lane'] = self.index
        response['map'] = self.map
        response['load'] = bool(self.load_state)
        response["prep"] =bool(self.prep_state)
        response["tool_loaded"] = self.tool_loaded
        response["loaded_to_hub"] = self.loaded_to_hub
        response["material"]=self.material
        response["spool_id"]=self.spool_id
        response["color"]=self.color
        response["weight"]=self.weight
        response["extruder_temp"] = self.extruder_temp
        response["runout_lane"]=self.runout_lane
        filiment_stat=self.AFC.FUNCTION.get_filament_status(self).split(':')
        response['filament_status'] = filiment_stat[0]
        response['filament_status_led'] = filiment_stat[1]
        response['status'] = self.status
        return response

def load_config_prefix(config):
    return AFCExtruderStepper(config)
