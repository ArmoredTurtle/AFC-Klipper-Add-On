

class afcError:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.gcode = self.printer.lookup_object('gcode')
        self.AFC = self.printer.lookup_object('AFC')

        self.errorLog= {}

    def PauseUserIntervention(self):
        #pause for user intervention
        self.gcode.respond_info('User intervention required')

    def fix(self,problem, LANE=None):
        if problem == None:
            return
        if problem=='toolhead':
            self.ToolHeadFix(LANE)

    def ToolHeadFix(self, CUR_LANE):
        CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        if CUR_EXTRUDER.tool_start_state:   #toolhead has filament
            if self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded'] == CUR_LANE.name:   #var has right lane loaded
                if CUR_LANE.load_state == False: #Lane has filament
                    self.gcode.respond_info('Filament not loaded in Lane')
                    #pause for user intervention
                else:
                    self.gcode.respond_info('no error detected')
            else:
                self.gcode.respond_info('laneloaded does not match extruder')
                    #pause for user intervention

        else: #toolhead empty
            if CUR_LANE.load_state == True: #Lane has filament
                while CUR_LANE.load_state == True:  # slowly back filament up to lane extruder
                    CUR_LANE.move(-5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                while CUR_LANE.load_state == False:  # reload lane extruder
                    CUR_LANE.move(5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = False
                self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded']= ''
                self.AFC.save_vars()
            else:
                self.gcode.respond_info('Filament not loaded in Lane')
                    #pause for user intervention

                
            
                












def load_config(config):
    return afcError(config)

