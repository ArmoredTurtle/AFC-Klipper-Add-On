# 8 Track Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

class AFCtrigger:
    def __init__(self, config):
      self.printer = config.get_printer()
      self.reactor = self.printer.get_reactor()
      self.name = config.get_name().split(' ')[-1]
      self.pin = config.get('pin')
      self.buffer_distance = config.getfloat('distance', 0)
      self.velocity = config.getfloat('velocity', 0)
      self.accel = config.getfloat('accel', 0)
      self.last_state = False
      self.current = ''
      self.AFC = self.printer.lookup_object('AFC')
      self.debug = config.getboolean("debug", False)
      buttons = self.printer.load_object(config, "buttons")
      buttons.register_buttons([self.pin], self.sensor_callback)
      self.gcode = self.printer.lookup_object('gcode')
      self.printer.register_event_handler("klippy:ready", self._handle_ready)
      self.gcode.register_mux_command("QUERY_BUFFER","BUFFER", self.name,self.cmd_QUERY_BUFFER,desc=self.cmd_QUERY_BUFFER_help)
    cmd_QUERY_BUFFER_help = "Report Buffer sensor state"

    def cmd_QUERY_BUFFER(self, gcmd):
        if self.last_state:
            state_info = "compressed"
        else:
            state_info = "expanded"
        self.gcode.respond_info("{} : {}".format(self.name, state_info))

    def _handle_ready(self):
        self.min_event_systime = self.reactor.monotonic() + 2.

    def sensor_callback(self, eventtime, state):
        self.last_state = state
        if self.printer.state_message == 'Printer is ready':
            if self.printer.lookup_object('filament_switch_sensor tool_start').runout_helper.filament_present == True:
                if self.printer.lookup_object('AFC').current != None:
                    tool_loaded=self.printer.lookup_object('AFC').current
                    LANE = self.printer.lookup_object('AFC_stepper ' + tool_loaded)
                    if LANE.status != 'unloading':
                        if self.debug == True: self.gcode.respond_info("Buffer Triggered, State: {}".format(state))
                        LANE.move(self.buffer_distance, self.velocity ,self.accel)

def load_config_prefix(config):
    return AFCtrigger(config)
