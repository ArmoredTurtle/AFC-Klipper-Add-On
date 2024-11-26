

class afcError:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')
        self.errorLog= {}

    def PauseUserIntervention(self,message):
        #pause for user intervention
        self.gcode.respond_info(message)

    def fix(self,problem, LANE=None):
        self.AFC = self.printer.lookup_object('AFC')
        if problem == None:
            return
        if problem=='toolhead':
            error_handled = self.ToolHeadFix(LANE)

        return error_handled

    def ToolHeadFix(self, CUR_LANE):
        CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
        if CUR_EXTRUDER.tool_start_state:   #toolhead has filament
            if self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded'] == CUR_LANE.name:   #var has right lane loaded
                if CUR_LANE.load_state == False: #Lane has filament
                    self.PauseUserIntervention('Filament not loaded in Lane')
                else:
                    self.PauseUserIntervention('no error detected')
            else:
                self.PauseUserIntervention('laneloaded does not match extruder')

        else: #toolhead empty
            if CUR_LANE.load_state == True: #Lane has filament
                while CUR_LANE.load_state == True:  # slowly back filament up to lane extruder
                    CUR_LANE.move(-5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                while CUR_LANE.load_state == False:  # reload lane extruder
                    CUR_LANE.move(5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = False
                self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded']= ''
                self.AFC.save_vars()
                return True

            else:
                self.PauseUserIntervention('Filament not loaded in Lane')

                
            
def load_config(config):
    return afcError(config)

