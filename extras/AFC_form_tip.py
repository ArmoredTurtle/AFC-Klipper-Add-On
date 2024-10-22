
class afc_tip_form:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.AFC = self.printer.lookup_object('AFC')
        self.gcode = self.printer.lookup_object('gcode')

         # TIP FORMING
        self.ramming_volume = config.getfloat("ramming_volume", 0)
        self.toolchange_temp  = config.getfloat("toolchange_temp", 0)
        self.unloading_speed_start  = config.getfloat("unloading_speed_start", 80)
        self.unloading_speed  = config.getfloat("unloading_speed", 18)
        self.cooling_tube_position  = config.getfloat("cooling_tube_position", 35)
        self.cooling_tube_length  = config.getfloat("cooling_tube_length", 10)
        self.initial_cooling_speed  = config.getfloat("initial_cooling_speed", 10)
        self.final_cooling_speed  = config.getfloat("final_cooling_speed", 50)
        self.cooling_moves  = config.getint("cooling_moves", 4)
        self.use_skinnydip  = config.getboolean("use_skinnydip", False)
        self.skinnydip_distance  = config.getfloat("skinnydip_distance", 4)
        self.dip_insertion_speed  = config.getfloat("dip_insertion_speed", 4)
        self.dip_extraction_speed  = config.getfloat("dip_extraction_speed", 4)
        self.melt_zone_pause  = config.getfloat("melt_zone_pause", 4)
        self.cooling_zone_pause  = config.getfloat("cooling_zone_pause", 4)
        

    def afc_extrude(self, distance, speed):
        pos = self.AFC.toolhead.get_position()
        pos[3] += distance
        self.AFC.toolhead.manual_move(pos, speed)
        self.AFC.toolhead.wait_moves()

       

    def tip_form(self):
        step = 1
        if self.ramming_volume > 0:
            self.gcode.respond_info('AFC-TIP-FORM: Step ' + str(step) + ': Ramming')
            ratio = self.ramming_volume / 23
            self.afc_extrude(0.5784 * ratio, 299)
            self.afc_extrude(0.5834 * ratio, 302)
            self.afc_extrude(0.5918 * ratio, 306)
            self.afc_extrude(0.6169 * ratio, 319)
            self.afc_extrude(0.3393 * ratio, 350)
            self.afc_extrude(0.3363 * ratio, 350)
            self.afc_extrude(0.7577 * ratio, 392)
            self.afc_extrude(0.8382 * ratio, 434)
            self.afc_extrude(0.7776 * ratio, 469)
            self.afc_extrude(0.1293 * ratio, 469)
            self.afc_extrude(0.9673 * ratio, 501)
            self.afc_extrude(1.0176 * ratio, 527)
            self.afc_extrude(0.5956 * ratio, 544)
            self.afc_extrude(1.0662 * ratio, 552)
            step +=1
        self.gcode.respond_info('AFC-TIP-FORM: Step ' + str(step) + ': Retraction & Nozzle Separation')
        total_retraction_distance = self.cooling_tube_position + self.cooling_tube_length - 15
        self.afc_extrude(-15, self.unloading_speed_start * 60)
        if total_retraction_distance > 0:
            self.afc_extrude(-.7 * total_retraction_distance, 1.0 * self.unloading_speed * 60)
            self.afc_extrude(-.2 * total_retraction_distance, 0.5 * self.unloading_speed * 60)
            self.afc_extrude(-.1 * total_retraction_distance, 0.3 * self.unloading_speed * 60)
        if self.toolchange_temp > 0:
            if self.use_skinnydip:
                wait = False
            else:
                wait =  True
            extruder = self.toolhead.get_extruder()
            pheaters = self.printer.lookup_object('heaters')
            pheaters.set_temperature(extruder.get_heater(), self.toolchange_temp, wait)
        step +=1
        self.gcode.respond_info('AFC-TIP-FORM: Step ' + str(step) + ': Cooling Moves')
        speed_inc = (self.final_cooling_speed - self.initial_cooling_speed) / (2 * self.cooling_moves - 1)
        for move in range(self.cooling_moves):
            speed = self.initial_cooling_speed + speed_inc * move * 2
            self.afc_extrude(self.cooling_tube_length, speed * 60)
            self.afc_extrude(self.cooling_tube_length * -1, (speed + speed_inc) * 60)
        step += 1
        if self.use_skinnydip:
            self.gcode.respond_info('AFC-TIP-FORM: Step ' + str(step) + ': Skinny Dipping')
            self.afc_extrude(self.skinnydip_distance, self.dip_insertion_speed * 60)
            self.reactor.pause(self.reactor.monotonic() + self.melt_zone_pause)
            self.afc_extrude(self.skinnydip_distance * -1, self.dip_extraction_speed * 60)
            self.reactor.pause(self.reactor.monotonic() + self.cooling_zone_pause)

def load_config(config):
    return afc_tip_form(config)