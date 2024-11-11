# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import os
import json
class afcPrep:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('PREP', self.PREP, desc=None)
        self.enable = config.getboolean("enable", False)

    def PREP(self, gcmd):
        self.AFC = self.printer.lookup_object('AFC')
        while self.printer.state_message != 'Printer is ready':
            self.reactor.pause(self.reactor.monotonic() + 1)
        if os.path.exists(self.AFC.VarFile) and os.stat(self.AFC.VarFile).st_size > 0:
            try: self.lanes=json.load(open(self.AFC.VarFile))
            except IOError: self.AFC.lanes={}
            except ValueError: self.AFC.lanes={}
        else:
            self.AFC.lanes={}
        temp=[]
        for PO in self.printer.objects:
            if 'AFC_stepper' in PO and 'tmc' not in PO:
                LANE=self.printer.lookup_object(PO)
                temp.append(LANE.name)
                if LANE.unit not in self.AFC.lanes: self.AFC.lanes[LANE.unit]={}
                if LANE.name not in self.AFC.lanes[LANE.unit]: self.AFC.lanes[LANE.unit][LANE.name]={}
                if LANE.extruder_name not in self.AFC.extrude: self.AFC.extrude.append(LANE.extruder_name)
                if 'index' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['index'] = LANE.index
                if 'material' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['material']=''
                if 'spool_id' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['spool_id']=''
                if 'color' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['color']='#000000'
                if 'tool_loaded' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['tool_loaded'] = False
                if 'hub_loaded' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['hub_loaded'] = False
                if self.AFC.lanes[LANE.unit][LANE.name]['tool_loaded'] == True: self.AFC.current = LANE.name
        tmp=[]
        for UNIT in self.AFC.lanes.keys():
            for lanecheck in self.AFC.lanes[UNIT].keys():
                if lanecheck not in temp: tmp.append(lanecheck)
            for erase in tmp:
                del self.AFC.lanes[UNIT][erase]
        self.AFC.save_vars()
        if len(self.AFC.lanes) >0:
            for UNIT in self.AFC.lanes.keys():
                logo=''
                logo_error = ''
                
                # Check each unit has a buffer
                try: CUR_HUB = self.printer.lookup_object('AFC_hub '+ UNIT)
                except:
                    error_string = 'Error: Hub for ' + UNIT + ' not found in AFC_Hardware.cfg. Please add the [AFC_Hub ' + UNIT + '] config section.'
                    self.AFC.AFC_error(error_string, False)
                    return
                self.gcode.respond_info(CUR_HUB.type + ' ' + UNIT +' Prepping lanes')
                if CUR_HUB.type == 'Box_Turtle':
                    firstLeg = '<span class=warning--text>|</span><span class=error--text>_</span>'
                    secondLeg = firstLeg + '<span class=warning--text>|</span>'
                    logo ='<span class=success--text>R  _____     ____\n'
                    logo+='E /      \  |  </span><span class=info--text>o</span><span class=success--text> | \n'
                    logo+='A |       |/ ___/ \n'
                    logo+='D |_________/     \n'
                    logo+='Y {first}{second} {first}{second}\n'.format(first=firstLeg, second=secondLeg)
                    logo+='  ' + UNIT + '\n'

                    logo_error ='<span class=error--text>E  _ _   _ _\n'
                    logo_error+='R |_|_|_|_|_|\n'
                    logo_error+='R |         \____\n'
                    logo_error+='O |              \ \n'
                    logo_error+='R |          |\ <span class=secondary--text>X</span> |\n'
                    logo_error+='! \_________/ |___|</error>\n'
                    logo_error+='  ' + UNIT + '\n'

                if CUR_HUB.type == 'Night_Owl':
                    logo = 'Night Owl Ready'
                    logo_error = 'Night Owl Not Ready'
                    logo ='R  ,     ,\n'
                    logo+='E  )\___/(\n'
                    logo+='A {(@)v(@)}\n'
                    logo+='D  {|~~~|}\n'
                    logo+='Y  {/^^^\}\n'
                    logo+='!   `m-m`\n'
                    logo+='  ' + UNIT + '\n'
                # Check for valid buffer deffinition
                buffer_warning = "Warning: Buffer {} not found in hardware config file"
                if self.AFC.buffer_name is not None:
                    try: self.AFC.buffer = self.printer.lookup_object('AFC_buffer {}'.format(self.buffer_name))
                    except:
                        self.AFC.AFC_error(buffer_warning.format(self.buffer_name))
                else:
                    self.gcode.respond_info("Warning: No buffer defined in config file")

                if self.AFC.current != None:
                    CUR_LANE = self.printer.lookup_object('AFC_stepper ' + self.current)
                    CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
                    if CUR_HUB.state == True and CUR_LANE.load_state == True and CUR_EXTRUDER.tool_start_state == True:
                        self.gcode.respond_info(self.current + " Currently Loaded")
                    else:
                        if CUR_LANE.load_state == True and CUR_EXTRUDER.tool_start_state == False:
                            self.gcode.respond_info(self.current + " Not in Tool Head")
                            return
                for LANE in self.AFC.lanes[UNIT].keys():
                    if self.AFC.current != LANE:
                        check_success = True
                        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
                        # Check each lane is assigned to a valid extruder
                        try: CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
                        except:
                            error_string = 'Error: No config found for extruder: ' + CUR_LANE.extruder_name + ' in [AFC_stepper ' + CUR_LANE.name + ']. Please make sure [AFC_extruder ' + CUR_LANE.extruder_name + '] config exists in AFC_Hardware.cfg'
                            self.AFC.AFC_error(error_string, False)
                            check_success = False
                        # Run test reverse/forward on each lane
                        if check_success == True:
                            CUR_LANE.extruder_stepper.sync_to_extruder(None)
                            CUR_LANE.move( 5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                            self.reactor.pause(self.reactor.monotonic() + 1)
                            CUR_LANE.move( -5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                    
                            if CUR_LANE.prep_state == False:
                                self.AFC.afc_led(self.AFC.led_not_ready, CUR_LANE.led_index)
                            elif CUR_HUB.state == True:
                                CUR_LANE.hub_load = self.AFC.lanes[UNIT][LANE]['hub_loaded'] # Setting hub load state so it can be retained between restarts
                                self.AFC.afc_led(self.AFC.led_ready, CUR_LANE.led_index)
                            msg = ''
                            if CUR_LANE.prep_state == True:
                                msg +="LOCKED"
                                if CUR_LANE.load_state == True:
                                    CUR_LANE.status = 'Loaded'
                                    msg +=" AND LOADED"
                                else:
                                    msg +=" NOT LOADED"
                            else:
                                if CUR_LANE.load_state == True:
                                    CUR_LANE.status = None
                                    msg +=" NOT READY"
                                    CUR_LANE.do_enable(False)
                                    msg = 'CHECK FILAMENT Prep: False - Load: True'
                                else:
                                    msg += 'EMPTY READY FOR SPOOL'
                            CUR_LANE.do_enable(False)
                            self.gcode.respond_info(CUR_LANE.name.upper() + ' ' + msg)
                            CUR_LANE.set_afc_prep_done()
                if check_success == True:
                    self.gcode.respond_raw(logo)
                    if self.AFC.buffer != None:
                        if self.AFC.current != None:
                            self.AFC.buffer.enable_buffer()
                else:
                    self.gcode.respond_raw(logo_error)

def load_config(config):
    return afcPrep(config)

