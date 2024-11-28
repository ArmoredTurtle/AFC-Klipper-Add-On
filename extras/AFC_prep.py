# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import os
import json
try:
    from urllib.request import urlopen
except:
    # Python 2.7 support
    from urllib2 import urlopen

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

        # Renaming users Resume macro so that RESUME calls AFC_Resume function instead
        base_resume_name = "RESUME"
        prev_cmd = self.gcode.register_command(base_resume_name, None)
        if prev_cmd is not None:
            pdesc = "Renamed builtin of '%s'" % (base_resume_name,)
            self.gcode.register_command(self.AFC.AFC_RENAME_RESUME_NAME, prev_cmd, desc=pdesc)
        else:
            self.gcode.respond_info("{}Existing command {} not found in gcode_macros{}".format("<span class=warning--text>", base_resume_name, "</span>",))

        self.gcode.register_command(base_resume_name, self.AFC.cmd_AFC_RESUME, desc=self.AFC.cmd_AFC_RESUME_help)

        ## load Unit variables
        if os.path.exists(self.AFC.VarFile + '.unit') and os.stat(self.AFC.VarFile + '.unit').st_size > 0:
            self.AFC.lanes=json.load(open(self.AFC.VarFile + '.unit'))
        else:
            self.AFC.lanes={}
        ## load Toolhead variables
        if os.path.exists(self.AFC.VarFile + '.tool') and os.stat(self.AFC.VarFile + '.tool').st_size > 0:
            self.AFC.extruders=json.load(open(self.AFC.VarFile + '.tool'))
        else:
            self.AFC.extruders={}
        temp=[]
        for PO in self.printer.objects:
            if 'AFC_stepper' in PO and 'tmc' not in PO:
                LANE=self.printer.lookup_object(PO)
                temp.append(LANE.name)
                if LANE.unit not in self.AFC.lanes: self.AFC.lanes[LANE.unit]={}
                if LANE.name not in self.AFC.lanes[LANE.unit]: self.AFC.lanes[LANE.unit][LANE.name]={}
                if LANE.extruder_name not in self.AFC.extruders: self.AFC.extruders[LANE.extruder_name]={}
                if 'lane_loaded' not in self.AFC.extruders[LANE.extruder_name]: self.AFC.extruders[LANE.extruder_name]['lane_loaded']=''

                if 'spool_id' not in self.AFC.lanes[LANE.unit][LANE.name]:
                    self.AFC.lanes[LANE.unit][LANE.name]['spool_id']=''
                else:
                    if self.AFC.spoolman_ip !=None and self.AFC.lanes[LANE.unit][LANE.name]['spool_id'] != '':
                        url = 'http://' + self.AFC.spoolman_ip + ':'+ self.AFC.spoolman_port +"/api/v1/spool/" + self.AFC.lanes[LANE.unit][LANE.name]['spool_id']
                        result = json.load(urlopen(url))
                        self.AFC.lanes[LANE.unit][LANE.name]['material'] = result['filament']['material']
                        self.AFC.lanes[LANE.unit][LANE.name]['color'] = '#' + result['filament']['color_hex']
                        if 'remaining_weight' in result: self.AFC.lanes[LANE.unit][LANE.name]['weight'] =  result['remaining_weight']

                if 'material' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['material']=''
                if 'color' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['color']='#000000'
                if 'weight' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['weight'] = 0

                if 'command' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['command'] = LANE.gcode_cmd
                if 'index' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['index'] = LANE.index
                if 'tool_loaded' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['tool_loaded'] = False
                if 'hub_loaded' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['hub_loaded'] = False
                if 'tool_loaded' not in self.AFC.lanes[LANE.unit][LANE.name]: self.AFC.lanes[LANE.unit][LANE.name]['tool_loaded'] = False

        tmp=[]
        for UNIT in self.AFC.lanes.keys():
            if UNIT !='system':
                for LANE in self.AFC.lanes[UNIT].keys():
                    if LANE !='system':
                        if LANE not in temp: tmp.append(LANE)
        for erase in tmp:
            del self.AFC.lanes[UNIT][erase]

        self.AFC.save_vars()
        if len(self.AFC.lanes) >0:
            for UNIT in self.AFC.lanes.keys():
                logo=''
                logo_error = ''
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

                for LANE in self.AFC.lanes[UNIT].keys():
                    check_success = True
                    CUR_LANE = self.printer.lookup_object('AFC_stepper ' + LANE)
                    # Check each lane is assigned to a valid extruder
                    try: CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + CUR_LANE.extruder_name)
                    except:
                        error_string = 'Error: No config found for extruder: ' + CUR_LANE.extruder_name + ' in [AFC_stepper ' + CUR_LANE.name + ']. Please make sure [AFC_extruder ' + CUR_LANE.extruder_name + '] config exists in AFC_Hardware.cfg'
                        self.AFC.AFC_error(error_string, False)
                        check_success = False
                        break

                        # Run test reverse/forward on each lane
                    if check_success == True:
                        CUR_LANE.extruder_stepper.sync_to_extruder(None)
                        CUR_LANE.move( 5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                        self.reactor.pause(self.reactor.monotonic() + .1)
                        CUR_LANE.move( -5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
                    msg = ''
                    if CUR_LANE.prep_state == False:
                        if CUR_LANE.load_state == False:
                            self.AFC.afc_led(self.AFC.led_not_ready, CUR_LANE.led_index)
                            msg += 'EMPTY READY FOR SPOOL'
                        else:
                            CUR_LANE.status = None
                            msg +="<span class=error--text> NOT READY</span>"
                            CUR_LANE.do_enable(False)
                            msg = '<span class=secondary--text>CHECK FILAMENT Prep: False - Load: True</span>'

                    elif CUR_LANE.prep_state == True:
                        CUR_LANE.hub_load = self.AFC.lanes[UNIT][LANE]['hub_loaded'] # Setting hub load state so it can be retained between restarts
                        self.AFC.afc_led(self.AFC.led_ready, CUR_LANE.led_index)
                        msg +="<span class=success--text>LOCKED</span>"
                        if CUR_LANE.load_state == True:
                            CUR_LANE.status = 'Loaded'
                            msg +="<span class=success--text> AND LOADED</span>"
                        else:
                            msg +="<span class=error--text> NOT LOADED</span>"
                        if self.AFC.lanes[UNIT][CUR_LANE.name]['tool_loaded']:
                            if CUR_EXTRUDER.tool_start_state == True:
                                if CUR_LANE.prep_state == True and CUR_LANE.load_state == True:
                                    CUR_LANE.extruder_stepper.sync_to_extruder(CUR_LANE.extruder_name)
                                    msg +="\n in ToolHead"
                                    self.AFC.set_active_spool(self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['spool_id'])
                                    self.AFC.afc_led(self.AFC.led_tool_loaded, CUR_LANE.led_index)
                                    if len(self.AFC.extruders) == 1:
                                        self.AFC.current = CUR_LANE.name
                                        CUR_EXTRUDER.enable_buffer()
                            else:
                                lane_check=self.error_tool_unload(CUR_LANE)
                                if lane_check != True:
                                    check_success = False
                        else:
                            if CUR_EXTRUDER.tool_start_state == True:
                                if self.AFC.extruders[CUR_LANE.extruder_name]['lane_loaded'] == CUR_LANE.name:
                                    msg +="\n<span class=error--text> error in ToolHead. Extruder loaded with no lane identified</span>"
                                    check_success = False

                    CUR_LANE.do_enable(False)
                    self.gcode.respond_info(CUR_LANE.name.upper() + ' ' + msg)
                    CUR_LANE.set_afc_prep_done()

                for EXTRUDE in self.AFC.extruders.keys():
                    CUR_EXTRUDER = self.printer.lookup_object('AFC_extruder ' + EXTRUDE)
                    if CUR_EXTRUDER.tool_start_state == True:
                        if not self.AFC.extruders[EXTRUDE]['lane_loaded']:
                            self.gcode.respond_info('Extruder loaded with out knowing Lane')
                            check_success = False

            if check_success == True:
                self.gcode.respond_raw(logo)
            else:
                self.gcode.respond_raw(logo_error)
    def error_tool_unload(self, CUR_LANE):
        self.gcode.respond_info('Error on filament trying to correct')
        while CUR_LANE.load_state == True:
            CUR_LANE.move(-5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
        while CUR_LANE.load_state == False:
            CUR_LANE.move(5, self.AFC.short_moves_speed, self.AFC.short_moves_accel, True)
        self.AFC.lanes[CUR_LANE.unit][CUR_LANE.name]['tool_loaded'] = False
        return True

def load_config(config):
    return afcPrep(config)

