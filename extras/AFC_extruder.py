# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

class AFCextruder:
    def __init__(self, config):
      self.printer = config.get_printer()
      self.printer.register_event_handler("klippy:connect", self.handle_connect)

      self.name = config.get_name().split(' ')[-1]
      self.tool_stn = config.getfloat("tool_stn", 72)
      self.tool_stn_unload = config.getfloat("tool_stn_unload", 100)
      self.tool_sensor_after_extruder = config.getfloat("tool_sensor_after_extruder", 0)
      self.tool_unload_speed = config.getfloat("tool_unload_speed", 25)
      self.tool_load_speed = config.getfloat("tool_load_speed", 25)
      ppins = self.printer.lookup_object('pins')
      self.gcode = self.printer.lookup_object('gcode')

      # BUFFER
      self.buffer_name = config.get('buffer', None)
      self.buffer = None

      buttons = self.printer.load_object(config, "buttons")
      self.tool_start = config.get('pin_tool_start', None)
      self.tool_end = config.get('pin_tool_end', None)

      # RAMMING
      # Use buffer sensors for loading and unloading filament
      if self.tool_start == "buffer":
         self.r_enabled = False
         b = config.getsection("AFC_buffer {}".format(self.buffer_name))
         ap = b.get('advance_pin', None)
         tp = b.get('trailing_pin', None)
         if ap is not None and tp is not None:
            self.r_enabled = True
            self.advance_pin = ap
            self.trailing_pin = tp
            pins = ap.strip("!^"), tp.strip("!^")
            for pin_desc in pins:
                  ppins.allow_multi_use_pin(pin_desc)
         else:
            self.gcode.respond_info("advance_pin and trailing_pin must be defined to enable ram sensor")

      if self.tool_start is not None:
        if self.tool_start == "buffer" and self.r_enabled == True:
           self.tool_start_state = False
           self.buffer_trailing = False
           buttons.register_buttons([self.advance_pin], self.tool_start_callback)
           buttons.register_buttons([self.trailing_pin], self.buffer_trailing_callback)
        else:
          self.tool_start_state = False
          buttons.register_buttons([self.tool_start], self.tool_start_callback)
      if self.tool_end is not None:
        self.tool_end_state = False
        buttons.register_buttons([self.tool_end], self.tool_end_callback)

    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')
        self.reactor = self.AFC.reactor

        self.get_buffer()

    def get_buffer(self):
      """
      Retrieve the buffer object associated with the current buffer name.
      If `buffer_name` is set, this method assigns the buffer object to `self.buffer`
      by looking it up using the printer's AFC buffer system.
      """
      if self.buffer_name is not None:
          self.buffer = self.printer.lookup_object('AFC_buffer ' + self.buffer_name)

    def tool_start_callback(self, eventtime, state):
        self.tool_start_state = state
    def buffer_trailing_callback(self, eventtime, state):
        self.buffer_trailing = state
    def tool_end_callback(self, eventtime, state):
        self.tool_end_state = state

    def enable_buffer(self):
      """
      Enable the buffer if `buffer_name` is set.
      Retrieves the buffer object and calls its `enable_buffer()` method to activate it.
      """
      if self.buffer_name is not None:
         self.buffer.enable_buffer()

    def disable_buffer(self):
       """
       Disable the buffer if `buffer_name` is set.
       Calls the buffer's `disable_buffer()` method to deactivate it.
       """
       if self.buffer_name is not None:
          self.buffer.disable_buffer()

    def buffer_status(self):
       """
       Retrieve the current status of the buffer.
       If `buffer_name` is set, returns the buffer's status using `buffer_status()`.
       Otherwise, returns None.
       """
       if self.buffer_name is not None:
          return self.buffer.buffer_status()

       else: return None

def load_config_prefix(config):
    return AFCextruder(config)
