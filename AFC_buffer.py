
# 8 Track Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.
 
import logging
import math
import stepper, chelper
import copy
import os 
import toolhead
from . import AFC

class AFCtrigger:

    def __init__(self, config):
      self.printer = config.get_printer()
      self.reactor = self.printer.get_reactor()
      self.name = config.get_name().split(' ')[-1]
      self.pin = config.get('pin')
      self.buffer_distance=config.getfloat('distance', 0)
      self.velocity=config.getfloat('velocity', 0)
      self.accel=config.getfloat('accel', 0)
      self.last_state = False
      self.current =''
      self.AFC = self.printer.lookup_object('AFC')

      buttons = self.printer.load_object(config, "buttons")
      buttons.register_buttons([self.pin], self.sensor_callback)

      self.gcode = self.printer.lookup_object('gcode')
      self.printer.register_event_handler("klippy:ready", self._handle_ready)
    
    def _handle_ready(self):
        self.min_event_systime = self.reactor.monotonic() + 2.
    
    def sensor_callback(self, eventtime, state):
        self.last_state = state
        if self.printer.state_message == 'Printer is ready':
            if "buffer" in self.name:
                if self.printer.lookup_object('filament_switch_sensor tool').runout_helper.filament_present == True:
                    tool_loaded=self.printer.lookup_object('AFC').current
                    if tool_loaded != 'lane0':
                        LANE=self.printer.lookup_object('AFC_stepper ' + tool_loaded)
                        if LANE.status != 'unloading':
                            #self.AFC.afc_move(self.name,self.AFC.buffer_distance,self.AFC.short_moves_speed,self.AFC.short_moves_accel)
                            self.gcode.run_script_from_command('FORCE_MOVE STEPPER="AFC_stepper '+ tool_loaded + '" DISTANCE=' + str(self.buffer_distance) + ' VELOCITY=' + str(self.velocity) + ' ACCEL=' + str(self.accel))
                    
def load_config_prefix(config):
    return AFCtrigger(config)

