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

def load_config_prefix(config):
    return AFCextruder(config)
