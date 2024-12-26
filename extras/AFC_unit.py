class AFCunit:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.AFC = self.printer.lookup_object('AFC')
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.name = config.get_name().split()[-1]
        self.type = config.get('type', None)
        self.screen_mac = config.get('screen_mac', None)
        self.lanes=[]

        try:
            UnitType = self.type
            if self.type == 'Night_Owl': UnitType='Box_Turtle'
            self.unit = self.printer.load_object(config, "AFC_{}".format(UnitType.replace("_", "")))
        except:
            raise error("{} not supported, please remove or fix correct type for AFC_hub in your configuration".format(self.type))
 
        self.led_name =config.get('led_name',self.AFC.led_name)
        self.led_fault =config.get('led_fault',self.AFC.led_fault)
        self.led_ready = config.get('led_ready',self.AFC.led_ready)
        self.led_not_ready = config.get('led_not_ready',self.AFC.led_not_ready)
        self.led_loading = config.get('led_loading',self.AFC.led_loading)
        self.led_prep_loaded = config.get('led_loading',self.AFC.led_prep_loaded)
        self.led_unloading = config.get('led_unloading',self.AFC.led_unloading)
        self.led_tool_loaded = config.get('led_tool_loaded',self.AFC.led_tool_loaded)

    def handle_connect(self):
        """2
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        
        self.gcode = self.AFC.gcode
        self.reactor = self.AFC.reactor

    def get_status(self, eventtime=None):
        self.response = {}
        self.response['name'] = self.name
        self.response['type'] = self.type
        self.response['screen'] = self.screen_mac
        self.response['lanes'] = self.lanes
        
        return self.response

def load_config_prefix(config):
    return AFCunit(config)