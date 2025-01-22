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

class AFCextruder:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        buttons = self.printer.load_object(config, "buttons")
        self.AFC = self.printer.lookup_object('AFC')

        self.toolhead_extruder = None

        self.name = config.get_name().split(' ')[-1]
        self.tool_stn = config.getfloat("tool_stn", 72)
        self.tool_stn_unload = config.getfloat("tool_stn_unload", 100)
        self.tool_sensor_after_extruder = config.getfloat("tool_sensor_after_extruder", 0)
        self.tool_unload_speed = config.getfloat("tool_unload_speed", 25)
        self.tool_load_speed = config.getfloat("tool_load_speed", 25)
        self.tool_start = config.get('pin_tool_start', None)
        self.tool_end = config.get('pin_tool_end', None)
        self.lane_loaded = None
        self.lanes = {}
        self.buffer_name = config.get('buffer', None)

        self.gcode = self.printer.lookup_object('gcode')
        self.enable_sensors_in_gui = config.getboolean("enable_sensors_in_gui", self.AFC.enable_sensors_in_gui) # Set to True toolhead sensors switches as filament sensors in mainsail/fluidd gui, overrides value set in AFC.cfg

        self.tool_start_state = False
        if self.tool_start is not None:
            if self.tool_start == "buffer":
                self.gcode.respond_info("Setting up as buffer")
            else:
                self.tool_start_state = False
                buttons.register_buttons([self.tool_start], self.tool_start_callback)
                if self.enable_sensors_in_gui:
                    self.tool_start_filament_switch_name = "filament_switch_sensor {}".format("tool_start")
                    self.fila_tool_start = add_filament_switch(self.tool_start_filament_switch_name, self.tool_start, self.printer )

        self.tool_end_state = False
        if self.tool_end is not None:
            buttons.register_buttons([self.tool_end], self.tool_end_callback)
            if self.enable_sensors_in_gui:
                self.tool_end_state_filament_switch_name = "filament_switch_sensor {}".format("tool_end")
                self.fila_avd = add_filament_switch(self.tool_end_state_filament_switch_name, self.tool_end, self.printer )

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.reactor = self.AFC.reactor
        self.AFC.tools[self.name] = self

        try:
            self.toolhead_extruder = self.printer.lookup_object(self.name)
        except:
            raise error("[{}] not found in config file".format(self.name))

    def tool_start_callback(self, eventtime, state):
        self.tool_start_state = state

    def buffer_trailing_callback(self, eventtime, state):
        self.buffer_trailing = state

    def tool_end_callback(self, eventtime, state):
        self.tool_end_state = state

    def get_status(self, eventtime=None):
        self.response = {}
        self.response['tool_stn'] = self.tool_stn
        self.response['tool_stn_unload'] = self.tool_stn_unload
        self.response['tool_sensor_after_extruder'] = self.tool_sensor_after_extruder
        self.response['tool_unload_speed'] = self.tool_unload_speed
        self.response['tool_load_speed'] = self.tool_load_speed
        self.response['buffer'] = self.buffer_name
        self.response['lane_loaded'] = self.lane_loaded
        self.response['tool_start'] = self.tool_start
        self.response['tool_start_status'] = bool(self.tool_start_state)
        self.response['tool_end'] = self.tool_end
        self.response['tool_end_status'] = bool(self.tool_end_state)
        self.response['lanes'] = [lane.name for lane in self.lanes.values()]
        return self.response

def load_config_prefix(config):
    return AFCextruder(config)
