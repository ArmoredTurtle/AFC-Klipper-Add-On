class afcNightOwl:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.AFC = self.printer.lookup_object('AFC')
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.name = config.get_name().split()[-1]
        self.type='Box_Turtle'
        self.screen_mac = config.get('screen_mac', None)
        self.lanes=[]
        self.AFC.units[self.name]=config.get_name().split()[0]
 
        self.led_name =config.get('led_name',self.AFC.led_name)
        self.led_fault =config.get('led_fault',self.AFC.led_fault)
        self.led_ready = config.get('led_ready',self.AFC.led_ready)
        self.led_not_ready = config.get('led_not_ready',self.AFC.led_not_ready)
        self.led_loading = config.get('led_loading',self.AFC.led_loading)
        self.led_prep_loaded = config.get('led_loading',self.AFC.led_prep_loaded)
        self.led_unloading = config.get('led_unloading',self.AFC.led_unloading)
        self.led_tool_loaded = config.get('led_tool_loaded',self.AFC.led_tool_loaded)

    def get_status(self, eventtime=None):
        self.response = {}
        self.response['name'] = self.name
        self.response['type'] = self.type
        self.response['screen'] = self.screen_mac
        self.response['lanes'] = self.lanes
        
        return self.response
    
    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')

        self.logo = '<span class=success--text>Night Owl Ready</span>'
        self.logo ='<span class=success--text>R  ,     ,\n'
        self.logo+='E  )\___/(\n'
        self.logo+='A {(@)v(@)}\n'
        self.logo+='D  {|~~~|}\n'
        self.logo+='Y  {/^^^\}\n'
        self.logo+='!   `m-m`</span>\n'

        self.logo_error = '<span class=error--text>Night Owl Not Ready</span>\n'

    def system_Test(self, UNIT, LANE, delay, assignTcmd):
        msg = ''
        succeeded = True
        if LANE not in self.AFC.stepper:
            self.AFC.gcode.respond_info('{} Unknown'.format(LANE.upper()))
            return
        CUR_LANE = self.AFC.stepper[LANE]
        try:
            CUR_LANE.extruder_obj = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        except:
            error_string = 'Error: No config found for extruder: ' + CUR_LANE.extruder_name + ' in [AFC_stepper ' + CUR_LANE.name + ']. Please make sure [AFC_extruder ' + CUR_LANE.extruder_name + '] config exists in AFC_Hardware.cfg'
            self.AFC.ERROR.AFC_error(error_string, False)
            return False

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

def load_config(config):
    return afcNightOwl(config)