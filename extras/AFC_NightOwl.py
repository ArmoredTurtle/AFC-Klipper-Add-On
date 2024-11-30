class afcNightOwl:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')
        self.printer.register_event_handler("klippy:connect", self.handle_connect)

        self.logo = 'Night Owl Ready'
        self.logo ='R  ,     ,\n'
        self.logo+='E  )\___/(\n'
        self.logo+='A {(@)v(@)}\n'
        self.logo+='D  {|~~~|}\n'
        self.logo+='Y  {/^^^\}\n'
        self.logo+='!   `m-m`\n'

        self.logo_error = 'Night Owl Not Ready\n'
    def handle_connect(self):
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        self.AFC = self.printer.lookup_object('AFC')

    def system_Test(self, UNIT, LANE, delay):
        msg = ''
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
        try: CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        except:
            error_string = 'Error: No config found for extruder: ' + CUR_LANE.extruder_name + ' in [AFC_stepper ' + CUR_LANE.name + ']. Please make sure [AFC_extruder ' + CUR_LANE.extruder_name + '] config exists in AFC_Hardware.cfg'
            self.AFC.AFC_error(error_string, False)
            return False

        # Run test reverse/forward on each lane
        CUR_LANE.extruder_stepper.sync_to_extruder(None)
        CUR_LANE.move( 5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
        self.reactor.pause(self.reactor.monotonic() + delay)
        CUR_LANE.move( -5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)

        if CUR_LANE.prep_state == False:
            if CUR_LANE.load_state == False:
                self.AFC.afc_led(self.AFC.led_not_ready, CUR_LANE.led_index)
                msg += 'EMPTY READY FOR SPOOL'
            else:
                CUR_LANE.status = None
                msg +="<span class=error--text> NOT READY</span>"
                CUR_LANE.do_enable(False)
                msg = '<span class=secondary--text>CHECK FILAMENT Prep: False - Load: True</span>'

        else:
            CUR_LANE.hub_load = self.AFC.lanes[UNIT][LANE]['hub_loaded'] # Setting hub load state so it can be retained between restarts
            self.AFC.afc_led(self.AFC.led_ready, CUR_LANE.led_index)
            msg +="<span class=success--text>LOCKED</span>"
            if CUR_LANE.load_state == False:
                msg +="<span class=error--text> NOT LOADED</span>"
            else:
                CUR_LANE.status = 'Loaded'
                msg +="<span class=success--text> AND LOADED</span>"

                if self.AFC.lanes[UNIT][CUR_LANE.name]['tool_loaded']:
                    if CUR_EXTRUDER.tool_start_state == True:
                        if self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded'] == CUR_LANE.name:
                            CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
                            msg +="\n in ToolHead"
                            self.AFC.spool.set_active_spool(self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'])
                            self.AFC.afc_led(self.AFC.led_tool_loaded, CUR_LANE.led_index)
                            if len(self.AFC.extruders) == 1:
                                self.AFC.current = CUR_LANE.name
                                CUR_EXTRUDER.enable_buffer()
                        else:
                            lane_check=self.ERROR.fix('toolhead',CUR_LANE)  #send to error handling
                            if not lane_check:
                                return False
                    else:
                        if CUR_EXTRUDER.tool_start_state == True:
                            if self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded'] == CUR_LANE.name:
                                msg +="\n<span class=error--text> error in ToolHead. Extruder loaded with no lane identified</span>"

        CUR_LANE.do_enable(False)
        self.gcode.respond_info(CUR_LANE.name.upper() + ' ' + msg)
        CUR_LANE.set_afc_prep_done()

        if self.AFC.lanes[UNIT][LANE]['map'] not in self.AFC.tool_cmds:
            self.AFC.tool_cmds[self.AFC.lanes[UNIT][LANE]['map']]=LANE
            self.gcode.register_command(self.AFC.lanes[UNIT][LANE]['map'], self.AFC.cmd_CHANGE_TOOL, desc=self.AFC.cmd_CHANGE_TOOL_help)
        else:
            self.AFC.ERROR.fix('Command {} ALready Taken please re-map {}/{}'.format(self.AFC.lanes[UNIT][LANE]['map'], UNIT,LANE))
        return True

def load_config(config):
    return afcNightOwl(config)