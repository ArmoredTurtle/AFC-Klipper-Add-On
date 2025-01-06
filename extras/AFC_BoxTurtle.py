
class afcBoxTurtle:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
                
        self.name = config.get_name().split()[-1]
        self.type = config.get('type', 'Box_Turtle')
        self.screen_mac = config.get('screen_mac', None)
        self.hub = config.get('hub', None)
        self.buffer = config.get('buffer', None)
        self.buffer_obj = None
        
        self.led_name =config.get('led_name', None)
        self.led_fault =config.get('led_fault', None)
        self.led_ready = config.get('led_ready', None)
        self.led_not_ready = config.get('led_not_ready', None)
        self.led_loading = config.get('led_loading', None)
        self.led_prep_loaded = config.get('led_loading', None)
        self.led_unloading = config.get('led_unloading', None)
        self.led_tool_loaded = config.get('led_tool_loaded', None)

        self.long_moves_speed = config.getfloat("long_moves_speed",  None)            # Speed in mm/s to move filament when doing long moves
        self.long_moves_accel = config.getfloat("long_moves_accel",  None)            # Acceleration in mm/s squared when doing long moves
        self.short_moves_speed = config.getfloat("short_moves_speed",  None)           # Speed in mm/s to move filament when doing short moves
        self.short_moves_accel = config.getfloat("short_moves_accel",  None)          # Acceleration in mm/s squared when doing short moves
        self.short_move_dis = config.getfloat("short_move_dis",  None)                 # Move distance in mm for failsafe moves.
    
    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')

    def _handle_ready(self):
        
        self.lanes = []
        if self.hub == None: self.hub = self.AFC.hub
        if self.buffer == None: self.buffer = self.AFC.buffer

        self.AFC.units[self.name] = self
        self.hub_obj = self.AFC.hubs[self.hub]
        
        if self.buffer is not None: self.buffer_obj = self.AFC.buffers[self.buffer]

        if self.led_name is None: self.led_name = self.AFC.led_name
        if self.led_fault is None: self.led_fault = self.AFC.led_fault
        if self.led_ready is None: self.led_ready = self.AFC.led_ready
        if self.led_not_ready is None: self.led_not_ready = self.AFC.led_not_ready
        if self.led_loading is None: self.led_loading = self.AFC.led_loading
        if self.led_prep_loaded is None: self.led_prep_loaded = self.AFC.led_prep_loaded
        if self.led_unloading is None: self.led_unloading = self.AFC.led_unloading
        if self.led_tool_loaded is None: self.led_tool_loaded = self.AFC.led_tool_loaded

        if self.long_moves_speed is None: self.long_moves_speed = self.AFC.long_moves_speed        # Speed in mm/s to move filament when doing long moves
        if self.long_moves_accel is None: self.long_moves_accel = self.AFC.long_moves_accel           # Acceleration in mm/s squared when doing long moves
        if self.short_moves_speed is None: self.short_moves_speed = self.AFC.short_moves_speed          # Speed in mm/s to move filament when doing short moves
        if self.short_moves_accel is None: self.short_moves_accel = self.AFC.short_moves_accel        # Acceleration in mm/s squared when doing short moves
        if self.short_move_dis is None: self.short_move_dis = self.AFC.short_move_dis                # Move distance in mm for failsafe moves.


        firstLeg = '<span class=warning--text>|</span><span class=error--text>_</span>'
        secondLeg = firstLeg + '<span class=warning--text>|</span>'
        self.logo ='<span class=success--text>R  _____     ____\n'
        self.logo+='E /      \  |  </span><span class=info--text>o</span><span class=success--text> | \n'
        self.logo+='A |       |/ ___/ \n'
        self.logo+='D |_________/     \n'
        self.logo+='Y {first}{second} {first}{second}\n'.format(first=firstLeg, second=secondLeg)
        self.logo+= '  ' + self.name + '\n'

        self.logo_error ='<span class=error--text>E  _ _   _ _\n'
        self.logo_error+='R |_|_|_|_|_|\n'
        self.logo_error+='R |         \____\n'
        self.logo_error+='O |              \ \n'
        self.logo_error+='R |          |\ <span class=secondary--text>X</span> |\n'
        self.logo_error+='! \_________/ |___|</span>\n'
        self.logo_error+= '  ' + self.name + '\n'

    def system_Test(self, LANE, delay, assignTcmd):
        msg = ''
        succeeded = True
        if LANE not in self.AFC.lanes:
            self.AFC.gcode.respond_info('{} Unknown'.format(LANE.upper()))
            return
        CUR_LANE = self.AFC.lanes[LANE]
        # Run test reverse/forward on each lane
        CUR_LANE.unsync_to_extruder(False)
        CUR_LANE.move( 5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + delay)
        CUR_LANE.move( -5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
        if CUR_LANE.prep_state == False:
            if CUR_LANE.load_state == False:
                self.AFC.afc_led(CUR_LANE.led_not_ready, CUR_LANE.led_index)
                msg += 'EMPTY READY FOR SPOOL'
            else:
                self.AFC.afc_led(CUR_LANE.led_fault, CUR_LANE.led_index)
                msg +="<span class=error--text> NOT READY</span>"
                CUR_LANE.do_enable(False)
                msg = '<span class=error--text>CHECK FILAMENT Prep: False - Load: True</span>'
                succeeded = False
        else:
            self.AFC.afc_led(CUR_LANE.led_ready, CUR_LANE.led_index)
            msg +="<span class=success--text>LOCKED</span>"
            if CUR_LANE.load_state == False:
                msg +="<span class=error--text> NOT LOADED</span>"
                self.AFC.afc_led(CUR_LANE.led_not_ready, CUR_LANE.led_index)
                succeeded = False
            else:
                CUR_LANE.status = 'Loaded'
                msg +="<span class=success--text> AND LOADED</span>"
                if CUR_LANE.tool_loaded:
                    if CUR_LANE.extruder_obj.tool_start_state == True or CUR_LANE.extruder_obj.tool_start == "buffer":
                        if CUR_LANE.extruder_obj.lane_loaded == CUR_LANE.name:
                            self.AFC.current = CUR_LANE.name
                            CUR_LANE.sync_to_extruder()
                            msg +="<span class=primary--text> in ToolHead</span>"
                            if CUR_LANE.extruder_obj.tool_start == "buffer":
                                msg += "<span class=warning--text>\n Ram sensor enabled, confirm tool is loaded</span>"
                            self.AFC.SPOOL.set_active_spool(CUR_LANE.spool_id)
                            self.AFC.afc_led(CUR_LANE.led_tool_loaded, CUR_LANE.led_index)
                            CUR_LANE.status = 'Tooled'
                            CUR_LANE.extruder_obj.enable_buffer()
                            CUR_LANE.extruder_obj.lane_loaded = CUR_LANE.name
                        else:
                            if CUR_LANE.extruder_obj.tool_start_state == True:
                                msg +="<span class=error--text> error in ToolHead. \nLane identified as loaded in AFC.vars.unit file\n but not identified as loaded in AFC.var.tool file</span>"
                                succeeded = False
                    else:
                        lane_check=self.AFC.ERROR.fix('toolhead',CUR_LANE)  #send to error handling
                        if not lane_check:
                            return False

        if assignTcmd: self.AFC.TcmdAssign(CUR_LANE)
        CUR_LANE.do_enable(False)
        self.AFC.gcode.respond_info( '{lane_name} tool cmd: {tcmd:3} {msg}'.format(lane_name=CUR_LANE.name.upper(), tcmd=CUR_LANE.map, msg=msg))
        CUR_LANE.set_afc_prep_done()
        return succeeded
    
    def get_status(self, eventtime=None):
        self.response = {}
        self.response['lanes'] = self.lanes

        return self.response
        
def load_config_prefix(config):
    return afcBoxTurtle(config)