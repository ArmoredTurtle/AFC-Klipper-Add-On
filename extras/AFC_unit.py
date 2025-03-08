# Armored Turtle Automated Filament Control
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from configfile import error
try:
    from extras.AFC_respond import AFCprompt
except:
    raise error("Error trying to import AFC_respond, please rerun install-afc.sh script in your AFC-Klipper-Add-On directory then restart klipper")

class afcUnit:
    def __init__(self, config):
        self.printer        = config.get_printer()
        self.gcode          = self.printer.lookup_object('gcode')
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.AFC            = self.printer.lookup_object('AFC')
        self.logger         = self.AFC.logger

        self.lanes      = {}

        # Objects
        self.buffer_obj     = None
        self.hub_obj        = None
        self.extruder_obj   = None

        # Config get section
        self.full_name          = config.get_name().split()
        self.name               = self.full_name[-1]
        self.screen_mac         = config.get('screen_mac', None)
        self.hub                = config.get("hub", None)                                           # Hub name(AFC_hub) that belongs to this unit, can be overridden in AFC_stepper section
        self.extruder           = config.get("extruder", None)                                      # Extruder name(AFC_extruder) that belongs to this unit, can be overridden in AFC_stepper section
        self.buffer_name        = config.get('buffer', None)                                        # Buffer name(AFC_buffer) that belongs to this unit, can be overridden in AFC_stepper section
        self.led_name           = config.get('led_name', self.AFC.led_name)
        self.led_fault          = config.get('led_fault', self.AFC.led_fault)                       # LED color to set when faults occur in lane        (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
        self.led_ready          = config.get('led_ready', self.AFC.led_ready)                       # LED color to set when lane is ready               (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
        self.led_not_ready      = config.get('led_not_ready', self.AFC.led_not_ready)               # LED color to set when lane not ready              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
        self.led_loading        = config.get('led_loading', self.AFC.led_loading)                   # LED color to set when lane is loading             (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
        self.led_prep_loaded    = config.get('led_loading', self.AFC.led_loading)                   # LED color to set when lane is loaded              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
        self.led_unloading      = config.get('led_unloading', self.AFC.led_unloading)               # LED color to set when lane is unloading           (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
        self.led_tool_loaded    = config.get('led_tool_loaded', self.AFC.led_tool_loaded)           # LED color to set when lane is loaded into tool    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file

        self.long_moves_speed   = config.getfloat("long_moves_speed",  self.AFC.long_moves_speed)   # Speed in mm/s to move filament when doing long moves. Setting value here overrides values set in AFC.cfg file
        self.long_moves_accel   = config.getfloat("long_moves_accel",  self.AFC.long_moves_accel)   # Acceleration in mm/s squared when doing long moves. Setting value here overrides values set in AFC.cfg file
        self.short_moves_speed  = config.getfloat("short_moves_speed",  self.AFC.short_moves_speed) # Speed in mm/s to move filament when doing short moves. Setting value here overrides values set in AFC.cfg file
        self.short_moves_accel  = config.getfloat("short_moves_accel",  self.AFC.short_moves_accel) # Acceleration in mm/s squared when doing short moves. Setting value here overrides values set in AFC.cfg file
        self.short_move_dis     = config.getfloat("short_move_dis",  self.AFC.short_move_dis)       # Move distance in mm for failsafe moves. Setting value here overrides values set in AFC.cfg file
        self.max_move_dis       = config.getfloat("max_move_dis", self.AFC.max_move_dis)            # Maximum distance to move filament. AFC breaks filament moves over this number into multiple moves. Useful to lower this number if running into timer too close errors when doing long filament moves. Setting value here overrides values set in AFC.cfg file
        self.n20_break_delay_time = config.getfloat("n20_break_delay_time", self.AFC.n20_break_delay_time) # Time to wait between breaking n20 motors(nSleep/FWD/RWD all 1) and then releasing the break to allow coasting. Setting value here overrides values set in AFC.cfg file

        self.assisted_unload    = config.getboolean("assisted_unload", self.AFC.assisted_unload)    # If True, the unload retract is assisted to prevent loose windings, especially on full spools. This can prevent loops from slipping off the spool. Setting value here overrides values set in AFC.cfg file
        self.unload_on_runout   = config.getboolean("unload_on_runout", self.AFC.unload_on_runout)  # When True AFC will unload lane and then pause when runout is triggered and spool to swap to is not set(infinite spool). Setting value here overrides values set in AFC.cfg file

    def __str__(self):
        return self.name

    def handle_connect(self):
        """
        Handles klippy:connect event, and does error checking to make sure users have hub/extruder/buffers sections if these variables are defined at the unit level
        """
        self.AFC = self.printer.lookup_object('AFC')
        self.AFC.units[self.name] = self

        # Error checking for hub
        # TODO: once supported add check if users is not using a hub
        if self.hub is not None:
            try:
                self.hub_obj = self.printer.lookup_object("AFC_hub {}".format(self.hub))
            except:
                error_string = 'Error: No config found for hub: {hub} in [AFC_{unit_type} {unit_name}]. Please make sure [AFC_hub {hub}] section exists in your config'.format(
                hub=self.hub, unit_type=self.type.replace("_", ""), unit_name=self.name )
                raise error(error_string)

        # Error checking for extruder
        if self.extruder is not None:
            try:
                self.extruder_obj = self.printer.lookup_object("AFC_extruder {}".format(self.extruder))
            except:
                error_string = 'Error: No config found for extruder: {extruder} in [AFC_{unit_type} {unit_name}]. Please make sure [AFC_extruder {extruder}] section exists in your config'.format(
                    extruder=self.extruder, unit_type=self.type.replace("_", ""), unit_name=self.name )
                raise error(error_string)

        # Error checking for buffer
        if self.buffer_name is not None:
            try:
                self.buffer_obj = self.printer.lookup_object('AFC_buffer {}'.format(self.buffer_name))
            except:
                error_string = 'Error: No config found for buffer: {buffer} in [AFC_{unit_type} {unit_name}]. Please make sure [AFC_buffer {buffer}] section exists in your config'.format(
                    buffer=self.buffer_name, unit_type=self.type.replace("_", ""), unit_name=self.name )
                raise error(error_string)

        # Send out event so lanes can store units object
        self.printer.send_event("AFC_unit_{}:connect".format(self.name), self)

        self.gcode.register_mux_command('UNIT_CALIBRATION', "UNIT", self.name, self.cmd_UNIT_CALIBRATION, desc=self.cmd_UNIT_CALIBRATION_help)
        self.gcode.register_mux_command('UNIT_LANE_CALIBRATION', "UNIT", self.name, self.cmd_UNIT_LANE_CALIBRATION, desc=self.cmd_UNIT_LANE_CALIBRATION_help)
        self.gcode.register_mux_command('UNIT_BOW_CALIBRATION', "UNIT", self.name, self.cmd_UNIT_BOW_CALIBRATION, desc=self.cmd_UNIT_BOW_CALIBRATION_help)

    def get_status(self, eventtime=None):
        response = {}
        response['lanes'] = [lane.name for lane in self.lanes.values()]
        response["extruders"]=[]
        response["hubs"] = []
        response["buffers"] = []

        for lane in self.lanes.values():
            if lane.hub is not None and lane.hub not in response["hubs"]: response["hubs"].append(lane.hub)
            if lane.extruder_name is not None and lane.extruder_name not in response["extruders"]: response["extruders"].append(lane.extruder_name)
            if lane.buffer_name is not None and lane.buffer_name not in response["buffers"]: response["buffers"].append(lane.buffer_name)

        return response

    cmd_UNIT_CALIBRATION_help = 'open prompt to calibrate the dist hub for lanes in selected unit'
    def cmd_UNIT_CALIBRATION(self, gcmd):
        """
        Open a prompt to calibrate either the distance between the extruder and the hub or the Bowden length
        for the selected unit. Provides buttons for lane calibration, Bowden length calibration, and a back option.

        Usage:`UNIT_CALIBRATION UNIT=<unit>`
        Example: `UNIT_CALIBRATION UNIT=Turtle_1`
        Args:
            None

        Returns:
            None
        """
        prompt = AFCprompt(gcmd, self.logger)
        buttons = []
        title = '{} Calibration'.format(self.name)
        text = 'Select to calibrate the distance from extruder to hub or bowden length'
        # Selection buttons
        buttons.append(("Calibrate Lanes", "UNIT_LANE_CALIBRATION UNIT={}".format(self.name), "primary"))
        buttons.append(("Calibrate afc_bowden_length", "UNIT_BOW_CALIBRATION UNIT={}".format(self.name), "secondary"))
        # Button back to previous step
        back = [('Back to unit selection', 'AFC_CALIBRATION', 'info')]

        prompt.create_custom_p(title, text, buttons, True, None, back)

    cmd_UNIT_LANE_CALIBRATION_help = 'open prompt to calibrate the length from extruder to hub'
    def cmd_UNIT_LANE_CALIBRATION(self, gcmd):
        """
        Open a prompt to calibrate the extruder-to-hub distance for each lane in the selected unit. Creates buttons
        for each lane, grouped in sets of two, and allows calibration for all lanes or individual lanes.

        Usage:`UNIT_LANE_CALIBRATION UNIT=<unit>`
        Example: `UNIT_LANE_CALIBRATION UNIT=Turtle_1`

        Args:
            UNIT: Specifies the unit to be used in calibration

        Returns:
            None
        """
        prompt = AFCprompt(gcmd, self.logger)
        buttons = []
        group_buttons = []
        title = '{} Lane Calibration'.format(self.name)
        text  = ('Select a loaded lane from {} to calibrate length from extruder to hub. '
                 'Config option: dist_hub').format(self.name)

        # Create buttons for each lane and group every 4 lanes together
        for index, LANE in enumerate(self.lanes):
            CUR_LANE = self.lanes[LANE]
            if CUR_LANE.load_state:
                button_label = "{}".format(LANE)
                button_command = "CALIBRATE_AFC LANE={}".format(LANE)
                button_style = "primary" if index % 2 == 0 else "secondary"
                group_buttons.append((button_label, button_command, button_style))

                # Add group to buttons list after every 4 lanes
                if (index + 1) % 2 == 0 or index == len(self.lanes) - 1:
                    buttons.append(list(group_buttons))
                    group_buttons = []

        if group_buttons:
            buttons.append(list(group_buttons))

        total_buttons = sum(len(group) for group in buttons)
        if total_buttons > 1:
            all_lanes = [('All lanes', 'CALIBRATE_AFC LANE=all UNIT={}'.format(self.name), 'default')]
        else:
            all_lanes = None
        if total_buttons == 0:
            text = 'No lanes are loaded, please load before calibration'

        # 'Back' button
        back = [('Back', 'UNIT_CALIBRATION UNIT={}'.format(self.name), 'info')]

        prompt.create_custom_p(title, text, all_lanes,
                               True, buttons, back)

    cmd_UNIT_BOW_CALIBRATION_help = 'open prompt to calibrate the afc_bowden_length from a lane in the unit'
    def cmd_UNIT_BOW_CALIBRATION(self, gcmd):
        """
        Open a prompt to calibrate the Bowden length for a specific lane in the selected unit. Provides buttons
        for each lane, with a note to only calibrate one lane per unit.

        Usage:`UNIT_CALIBRATION UNIT=<unit>`
        Example: `UNIT_CALIBRATION UNIT=Turtle_1`

        Args:
            UNIT: Specifies the unit to be used in calibration

        Returns:
            None
        """
        prompt = AFCprompt(gcmd, self.logger)
        buttons = []
        group_buttons = []
        title = 'Bowden Calibration {}'.format(self.name)
        text = ('Select a loaded lane from {} to measure Bowden length. '
                'ONLY CALIBRATE BOWDEN USING 1 LANE PER UNIT. '
                'Config option: afc_bowden_length').format(self.name)

        for index, LANE in enumerate(self.lanes):
            CUR_LANE = self.lanes[LANE]
            if CUR_LANE.load_state:
                # Create a button for each lane
                button_label = "{}".format(LANE)
                button_command = "CALIBRATE_AFC BOWDEN={}".format(LANE)
                button_style = "primary" if index % 2 == 0 else "secondary"
                group_buttons.append((button_label, button_command, button_style))

                # Add group to buttons list after every 4 lanes
                if (index + 1) % 2 == 0 or index == len(self.lanes) - 1:
                    buttons.append(list(group_buttons))
                    group_buttons = []

        if group_buttons:
            buttons.append(list(group_buttons))

        total_buttons = sum(len(group) for group in buttons)
        if total_buttons == 0:
            text = 'No lanes are loaded, please load before calibration'

        back = [('Back', 'UNIT_CALIBRATION UNIT={}'.format(self.name), 'info')]

        prompt.create_custom_p(title, text, None,
                               True, buttons, back)

    # Functions are below are placeholders so the function exists for all units, override these function in your unit files
    def _print_function_not_defined(self, name):
        self.AFC.gcode("{} function not defined for {}".format(name, self.name))

    # Function that other units can create so that they are specific to the unit
    def system_Test(self, CUR_LANE, delay, assignTcmd, enable_movement):
        self._print_function_not_defined(self.system_test.__name__)

    def calibrate_bowden(self, CUR_LANE, dis, tol):
        self._print_function_not_defined(self.calibrate_bowden.__name__)

    def calibrate_hub(self, CUR_LANE, tol):
        self._print_function_not_defined(self.calibrate_hub.__name__)

    def move_until_state(self, CUR_LANE, state, move_dis, tolerance, short_move, pos=0):
        self._print_function_not_defined(self.move_until_state.__name__)

    def calc_position(self,CUR_LANE, state, pos, short_move, tolerance):
        self._print_function_not_defined(self.calc_position.__name__)

    def calibrate_lane(self, CUR_LANE, tol):
        self._print_function_not_defined(self.calibrate_lane.__name__)
