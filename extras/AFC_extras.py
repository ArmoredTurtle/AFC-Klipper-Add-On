# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2025 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.


class AFCExtras:
    """
    This class is used for extra functionality that doesn't fit into the main AFC logic.
    """
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.reactor = self.printer.get_reactor()

        self.print_stats = self.printer.lookup_object('print_stats')
        self.afc = self.printer.lookup_object('AFC')
        self.lane_id = config.get_name().split()[-1]
        self.lane_number = config.getint('lane_number')
        self.long_press_duration = config.getfloat('long_press_duration', 1.2)
        pin_name = config.get('pin')

        # Internal state for press timing
        self._press_time = None

        # Register the button callback
        buttons = self.printer.load_object(config, 'buttons')
        buttons.register_buttons([pin_name], self._button_callback)

        self.afc.logger.info(f"AFC_extras for {self.lane_id} initialized on pin: {pin_name}")

    def _button_callback(self, eventtime, state):
        """
        Callback function for button press events.

        Args:
            eventtime: The time of the event.
            state: The state of the button (True for press, False for release).

        Behavior:
            - Tracks press duration.
            - Executes short or long press actions based on the duration.
        """
        if state:
            self._press_time = eventtime
            return
        if self._press_time is None:
            return

        if self.afc.function.is_printing(check_movement=True):
            self.afc.error.AFC_error("Cannot use buttons while printer is actively moving or homing", False)
            return

        held_time = eventtime - self._press_time
        self._press_time = None

        if held_time < 0.05:
            return

        cur_lane = self.afc.function.get_current_lane()

        # Long Press
        if held_time >= self.long_press_duration:
            self.afc.logger.info(f"{self.lane_id}: Long press detected.")
            if cur_lane == self.lane_id:
                self.afc.logger.info(f"Unloading {self.lane_id} before ejecting.")
                if self.afc.TOOL_UNLOAD(self):
                    self.afc.LANE_UNLOAD(self, cur_lane)
            else:
                # If another lane is active, just eject this one
                self.afc.logger.info(f"Ejecting {self.lane_number}.")
                self.afc.LANE_UNLOAD(self, self.lane_number)
        # Short Press
        else:
            self.afc.logger.info(f"{self.lane_id}: Short press detected.")
            if cur_lane == self.lane_id:
                self.afc.logger.info(f"Unloading tool from {self.lane_id}.")
                self.afc.TOOL_UNLOAD(self)
            else:
                self.afc.logger.info(f"Loading tool to {self.lane_id}.")
                self.gcode.run_script_from_command(f"BT_CHANGE_TOOL LANE={self.lane_number}")


def load_config_prefix(config):
    return AFCExtras(config)