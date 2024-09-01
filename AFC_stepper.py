# 8 Track Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import math, logging
import stepper, chelper
import time
from . import output_pin
from kinematics import extruder


#respooler
PIN_MIN_TIME = 0.100
RESEND_HOST_TIME = 0.300 + PIN_MIN_TIME
MAX_SCHEDULE_TIME = 5.0

#LED
BACKGROUND_PRIORITY_CLOCK = 0x7fffffff00000000
BIT_MAX_TIME=.000004
RESET_MIN_TIME=.000050
MAX_MCU_SIZE = 500  # Sanity check on LED chain length

class AFCExtruderStepper:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.extruder_stepper = extruder.ExtruderStepper(config)
        self.extruder_name = config.get('extruder')
        self.name = config.get_name().split()[-1]
        self.motion_queue = None
        self.status = ''
        self.gcode = self.printer.lookup_object('gcode')
        
        self.hub_dist = config.getfloat('hub_dist')
        
        #
        self.dist_hub = config.getfloat('dist_hub', 60)
        # LEDS
        self.led_index = config.get('led_index')

        # lane triggers
        buttons = self.printer.load_object(config, "buttons")

        self.prep = config.get('prep', None)
        if self.prep is not None:
            self.prep_state = False
            buttons.register_buttons([self.prep], self.prep_callback)

        self.load = config.get('load', None)
        if self.load is not None:
            self.load_state = False
            buttons.register_buttons([self.load], self.load_callback)
            
        # Respoolers
        self.respooler = config.get('respooler', None)
        if self.respooler is not None:
            pin=config.get('respooler')
            self.respooler_pin=pin
            respoolconfig=config
            respoolconfig.fileconfig.set('AFC_stepper '+ self.name,'pin',str(pin))
            self.respooler=output_pin.PrinterOutputPin(respoolconfig)
        self.AFC = self.printer.lookup_object('AFC')
        self.gcode = self.printer.lookup_object('gcode')   

        # Defaulting to false so that extruder motors to not move until PREP has been called
        self._afc_prep_done = False
    
    def set_afc_prep_done(self):
        """
        set_afc_prep_done function should only be called once AFC PREP function is done. Once this
            function is called it sets afc_prep_done to True. Once this is done the prep_callback function will
            now load once filament is inserted. 
        """
        self._afc_prep_done = True
       
    def resend_current_val(self, eventtime):
        if self.respool_last_value == self.respool_shutdown_value:
            self.reactor.unregister_timer(self.respool_resend_timer)
            self.respool_resend_timer = None
            return self.reactor.NEVER

        systime = self.reactor.monotonic()
        print_time = self.respool_mcu_pin.get_mcu().estimated_print_time(systime)
        time_diff = (self.respool_last_print_time + self.respool_resend_interval) - print_time
        if time_diff > 0.:
            # Reschedule for resend time
            return systime + time_diff
        self.rewind(print_time + PIN_MIN_TIME, self.respool_last_value, True)
        return systime + self.respool_resend_interval

    def load_callback(self, eventtime, state):
        self.load_state = state

    def prep_callback(self, eventtime, state):
        self.prep_state = state

        # Checking to make sure printer is ready and making sure PREP has been called before trying to load anything
        if self.printer.state_message == 'Printer is ready' and True == self._afc_prep_done:
            led=self.led_index
            if self.prep_state == True:
                while self.load_state == False and self.prep_state == True and self.status == '' :
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+self.name +'" ENABLE=1')
                    self.AFC.afc_move(self.name,10,500,400)
                    self.gcode.run_script_from_command('SET_STEPPER_ENABLE STEPPER="AFC_stepper '+self.name +'" ENABLE=0')
                if self.load_state == True and self.prep_state == True:
                    self.AFC.afc_led(self.AFC.led_ready, led)
            else:
                self.status = ''
                self.AFC.afc_led(self.AFC.led_not_ready, led)

def load_config_prefix(config):
    return AFCExtruderStepper(config)
