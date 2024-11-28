# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

class AFCextruder:
    def __init__(self, config):
      self.printer = config.get_printer()
      self.reactor = self.printer.get_reactor()
      self.name = config.get_name().split(' ')[-1]
      self.tool_stn = config.getfloat("tool_stn", 72)
      self.tool_stn_unload = config.getfloat("tool_stn_unload", 100)
      self.tool_sensor_after_extruder = config.getfloat("tool_sensor_after_extruder", 0)
      self.tool_unload_speed = config.getfloat("tool_unload_speed", 25)
      self.tool_load_speed = config.getfloat("tool_load_speed", 25)
      # BUFFER
      self.buffer_name = config.get('buffer', None)
      self.buffer = None
      self.printer.register_event_handler("klippy:connect", self._handle_ready)

      buttons = self.printer.load_object(config, "buttons")
      self.tool_start = config.get('pin_tool_start', None)
      self.tool_end = config.get('pin_tool_end', None)
      if self.tool_start is not None:
        self.tool_start_state = False
        buttons.register_buttons([self.tool_start], self.tool_start_callback)
      if self.tool_end is not None:
        self.tool_end_state = False
        buttons.register_buttons([self.tool_end], self.tool_end_callback)

    def tool_start_callback(self, eventtime, state):
        self.tool_start_state = state
    def tool_end_callback(self, eventtime, state):
        self.tool_end_state = state

    def get_buffer(self):
      """
      Retrieve the buffer object associated with the current buffer name.
      If `buffer_name` is set, this method assigns the buffer object to `self.buffer`
      by looking it up using the printer's AFC buffer system.
      """
      if self.buffer_name != None:
          self.buffer = self.printer.lookup_object('AFC_buffer ' + self.buffer_name)

    def _handle_ready(self):
       self.get_buffer()

    def enable_buffer(self):
      """
      Enable the buffer if `buffer_name` is set. 
      Retrieves the buffer object and calls its `enable_buffer()` method to activate it.
      """
      self.get_buffer()
      if self.buffer_name != None:
         self.buffer.enable_buffer()
    
    def disable_buffer(self):
       """
       Disable the buffer if `buffer_name` is set.
       Calls the buffer's `disable_buffer()` method to deactivate it.
       """
       if self.buffer_name != None:
          self.buffer.disable_buffer()

    def buffer_status(self):
       """
       Retrieve the current status of the buffer.
       If `buffer_name` is set, returns the buffer's status using `buffer_status()`. 
       Otherwise, returns None.
       """
       if self.buffer_name != None:
          return self.buffer.buffer_status()

       else: return None

def load_config_prefix(config):
    return AFCextruder(config)
