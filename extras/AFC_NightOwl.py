class afcNightOwl:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

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

    def system_Test(self, UNIT, LANE, delay):
        msg = ''
        succeeded = True
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
        try: CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        except:
            error_string = 'Error: No config found for extruder: ' + CUR_LANE.extruder_name + ' in [AFC_stepper ' + CUR_LANE.name + ']. Please make sure [AFC_extruder ' + CUR_LANE.extruder_name + '] config exists in AFC_Hardware.cfg'
            self.AFC.AFC_error(error_string, False)
            return False

        # Run test reverse/forward on each lane
        CUR_LANE.extruder_stepper.sync_to_extruder(None)
        CUR_LANE.move( 5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
        self.AFC.reactor.pause(self.AFC.reactor.monotonic() + delay)
        CUR_LANE.move( -5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)

        if CUR_LANE.prep_state == False:
            if CUR_LANE.load_state == False:
                self.AFC.afc_led(self.AFC.led_not_ready, CUR_LANE.led_index)
                msg += 'EMPTY READY FOR SPOOL'
            else:
                self.AFC.afc_led(self.AFC.led_fault, CUR_LANE.led_index)
                CUR_LANE.status = None
                msg +="<span class=error--text> NOT READY</span>"
                CUR_LANE.do_enable(False)
                msg = '<span class=error--text>CHECK FILAMENT Prep: False - Load: True</span>'
                succeeded = False

        else:
            CUR_LANE.hub_load = self.AFC.lanes[UNIT][LANE]['hub_loaded'] # Setting hub load state so it can be retained between restarts
            self.AFC.afc_led(self.AFC.led_ready, CUR_LANE.led_index)
            msg +="<span class=success--text>LOCKED</span>"
            if CUR_LANE.load_state == False:
                msg +="<span class=error--text> NOT LOADED</span>"
                self.AFC.afc_led(self.AFC.led_not_ready, CUR_LANE.led_index)
                succeeded = False
            else:
                CUR_LANE.status = 'Loaded'
                msg +="<span class=success--text> AND LOADED</span>"

                if self.AFC.lanes[UNIT][CUR_LANE.name]['tool_loaded']:
                    if CUR_EXTRUDER.tool_start_state == True or CUR_EXTRUDER.tool_start == "buffer":
                        if self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded'] == CUR_LANE.name:
                            CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
                            msg +="<span class=primary--text> in ToolHead</span>"
                            if CUR_EXTRUDER.tool_start == "buffer":
                                msg += "<span class=warning--text>\n Ram sensor enabled, confirm tool is loaded</span>"
                            self.AFC.SPOOL.set_active_spool(self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'])
                            self.AFC.afc_led(self.AFC.led_tool_loaded, CUR_LANE.led_index)
                            if len(self.AFC.extruders) == 1:
                                self.AFC.current = CUR_LANE.name
                                CUR_EXTRUDER.enable_buffer()
                        else:
                            if CUR_EXTRUDER.tool_start_state == True:
                                msg +="<span class=error--text> error in ToolHead. \nLane identified as loaded in AFC.vars.unit file\n but not identified as loaded in AFC.var.tool file</span>"
                                succeeded = False
                    else:
                        lane_check=self.AFC.ERROR.fix('toolhead',CUR_LANE)  #send to error handling
                        if not lane_check:
                            return False

        self.AFC.TcmdAssign(CUR_LANE)
        CUR_LANE.do_enable(False)
        self.AFC.gcode.respond_info( '{lane_name} tool cmd: {tcmd:3} {msg}'.format(lane_name=CUR_LANE.name.upper(), tcmd=CUR_LANE.map, msg=msg))
        CUR_LANE.set_afc_prep_done()
        return succeeded

def load_config(config):
    return afcNightOwl(config)