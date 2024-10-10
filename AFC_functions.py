

class afc_tip_form:
    def __init__(self, config):
        self.config = config
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')
        
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

        self.AFC = self.printer.lookup_object('AFC')
        self.afc_extrude =self.AFC.afc_extrude

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

class afc_hub_cut:
    def __init__(self, config):
        self.config = config
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')

        self.hub_cut_active = config.getboolean("hub_cut_active", False)
        self.hub_cut_dist = config.getfloat("hub_cut_dist", 200)
        self.hub_cut_clear = config.getfloat("hub_cut_clear", 120)
        self.hub_cut_min_length = config.getfloat("hub_cut_min_length", 200)
        self.hub_cut_servo_pass_angle = config.getfloat("hub_cut_servo_pass_angle", 0)
        self.hub_cut_servo_clip_angle = config.getfloat("hub_cut_servo_clip_angle", 160)
        self.hub_cut_servo_prep_angle = config.getfloat("hub_cut_servo_prep_angle", 75)
        self.hub_cut_confirm = config.getfloat("hub_cut_confirm", 0)

    def hub_cut(self, CUR_LANE):
        # Prep the servo for cutting.
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_prep_angle))
        # Load the lane until the hub is triggered.
        while self.hub.filament_present == False:
            CUR_LANE.move( self.hub_move_dis, self.short_moves_speed, self.short_moves_accel)
        # Go back, to allow the `hub_cut_dist` to be accurate.
        CUR_LANE.move( -self.hub_move_dis*4, self.short_moves_speed, self.short_moves_accel)
        # Feed the `hub_cut_dist` amount.
        CUR_LANE.move( self.hub_cut_dist, self.short_moves_speed, self.short_moves_accel)
        # Have a snooze
        # Choppy Chop
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_clip_angle))
        if self.hub_cut_confirm == 1:
            # ReChop, To be doubly choppy sure.
            self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_prep_angle))
            self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_clip_angle))
        # Longer Snooze
        # Align bowden tube (reset)
        self.gcode.run_script_from_command('SET_SERVO SERVO=cut ANGLE=' + str(self.hub_cut_servo_pass_angle))
        # Retract lane by `hub_cut_clear`.
        CUR_LANE.move( -self.hub_cut_clear, self.short_moves_speed, self.short_moves_accel)

class afc_poop:
    def __init__(self, config):
        self.config = config
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')

        self.verbose = config.getboolean('verbose', False)
        self.purge_loc_xy = config.get('purge_loc_xy')
        self.purge_start = config.getfloat('purge_start', 0)
        self.purge_spd = config.getfloat('purge_spd', 6.5)
        self.fast_z = config.getfloat('fast_z', 200)
        self.z_lift = config.getfloat('z_lift', 20)
        self.restore_position = config.getboolean('restore_position', False)
        self.purge_start = config.getfloat('purge_start', 20)
        self.full_fan = config.getboolean('full_fan', False)
        self.purge_length = config.getfloat('purge_length', 70.111)
        self.purge_length_min = config.getfloat('purge_length_min', 60.999)
    
    def poop(self,CUR_LANE):
        toolhead = self.printer.lookup_object('toolhead')
        step = 0
        if self.verbose:
            self.gcode.respond_info('AFC_Poop: ' + str(step) + ' Move To Purge Location')
        pooppos = self.toolhead.get_position()
        pooppos[0] = float(self.purge_loc_xy.split(',')[0])
        pooppos[1] = float(self.purge_loc_xy.split(',')[1])
        self.toolhead.manual_move(pooppos, 100)
        self.toolhead.wait_moves()
        pooppos[2] = self.purge_start
        self.toolhead.manual_move(pooppos, 100)
        self.toolhead.wait_moves()
        step +=1
        if self.full_fan:
            if self.verbose:
                self.gcode.respond_info('AFC_Poop: ' + str(step) + ' Set Cooling Fan to Full Speed')
            # save fan current speed
            # apply full speed
            step += 1
        
        iteration=1
        while iteration < int(self.purge_length / self.max_iteration_length ):
            if self.verbose:
                self.gcode.respond_info('AFC_Poop: ' + str(step) + ' Purge Iteration '+ str(iteration))
            purge_amount_left = self.purge_length - (self.max_iteration_length * iteration)
            extrude_amount = purge_amount_left / self.max_iteration_length
            extrude_ratio = extrude_amount / self.max_iteration_length
            step_triangular = iteration * (iteration + 1) / 2
            z_raise_substract = self.purge_start if iteration == 0 else step_triangular * self.iteration_z_change
            raise_z = (self.iteration_z_raise - z_raise_substract) * extrude_ratio
            duration = extrude_amount / self.purge_spd
            speed = raise_z / duration
            pooppos = self.toolhead.get_position()
            pooppos[2] = raise_z
            pooppos[3] = extrude_amount
            self.toolhead.manual_move(pooppos, speed)
            self.toolhead.wait_moves()

        step +=1
        if self.verbose:
            self.gcode.respond_info('AFC_Poop: ' + str(step) + ' Fast Z Lift to keep poop from sticking')
        pooppos = self.toolhead.get_position()
        pooppos[2] = self.z_lift
        self.toolhead.manual_move(pooppos, self.fast_z)
        self.toolhead.wait_moves()
        step += 1

        if self.full_fan:
            if self.verbose:
                self.gcode.respond_info('AFC_Poop: ' + str(step) + ' Restore fan speed and feedrate')
            # restore fan current speed
















