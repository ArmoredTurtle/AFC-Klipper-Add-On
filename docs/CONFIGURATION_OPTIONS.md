# Configuration Options Documentation

## AFC
- `moonraker_port` (default: `None`): Port to connect to when interacting with moonraker. Used when there are multiple moonraker/klipper instances on a single host
- `VarFile` (default: `'../printer_data/config/AFC/'`): Path to the variables file for AFC configuration.
- `default_material_temps` (default: `None`): Default temperature to set extruder when loading/unloading lanes. Material needs to be either manually set or uses material from spoolman if extruder temp is not set in spoolman.
- `led_fault` (default: `'1,0,0,0'`): LED color to set when faults occur in lane        (R,G,B,W) 0 = off, 1 = full brightness.
- `led_ready` (default: `'1,1,1,1'`): LED color to set when lane is ready               (R,G,B,W) 0 = off, 1 = full brightness.
- `led_not_ready` (default: `'1,1,0,0'`): LED color to set when lane not ready              (R,G,B,W) 0 = off, 1 = full brightness.
- `led_loading` (default: `'1,0,0,0'`): LED color to set when lane is loading             (R,G,B,W) 0 = off, 1 = full brightness.
- `led_loading` (default: `'1,1,0,0'`): LED color to set when lane is loaded              (R,G,B,W) 0 = off, 1 = full brightness.
- `led_unloading` (default: `'1,1,.5,0'`): LED color to set when lane is unloading           (R,G,B,W) 0 = off, 1 = full brightness.
- `led_tool_loaded` (default: `'1,1,0,0'`): LED color to set when lane is loaded into tool    (R,G,B,W) 0 = off, 1 = full brightness.
- `led_buffer_advancing` (default: `'0,0,1,0'`): LED color to set when buffer is advancing         (R,G,B,W) 0 = off, 1 = full brightness.
- `led_buffer_trailing` (default: `'0,1,0,0'`): LED color to set when buffer is trailing          (R,G,B,W) 0 = off, 1 = full brightness.
- `led_buffer_disable` (default: `'0,0,0,0.25'`): LED color to set when buffer is disabled          (R,G,B,W) 0 = off, 1 = full brightness.
- `tool_cut` (default: `False`): Set to True to enable toolhead cutting
- `tool_cut_cmd` (default: `None`): Macro to use when doing toolhead cutting. Change macro name if you would like to use your own cutting macro
- `park` (default: `False`): Set to True to enable parking during unload
- `park_cmd` (default: `None`): Macro to use when parking. Change macro name if you would like to use your own park macro
- `kick` (default: `False`): Set to True to enable poop kicking after lane loads
- `kick_cmd` (default: `None`): Macro to use when kicking. Change macro name if you would like to use your own kick macro
- `wipe` (default: `False`): Set to True to enable nozzle wiping after lane loads
- `wipe_cmd` (default: `None`): Macro to use when nozzle wiping. Change macro name if you would like to use your own wipe macro
- `poop` (default: `False`): Set to True to enable pooping(purging color) after lane loads
- `poop_cmd` (default: `None`): Macro to use when pooping. Change macro name if you would like to use your own poop/purge macro
- `form_tip` (default: `False`): Set to True to tip forming when unloading lanes
- `form_tip_cmd` (default: `None`): Macro to use when tip forming. Change macro name if you would like to use your own tip forming macro
- `long_moves_speed` (default: `100`): Speed in mm/s to move filament when doing long moves
- `long_moves_accel` (default: `400`): Acceleration in mm/s squared when doing long moves
- `short_moves_speed` (default: `25`): Speed in mm/s to move filament when doing short moves
- `short_moves_accel` (default: `400`): Acceleration in mm/s squared when doing short moves
- `short_move_dis` (default: `10`): Move distance in mm for failsafe moves.
- `max_move_dis` (default: `999999`): Maximum distance to move filament. AFC breaks filament moves over this number into multiple moves. Useful to lower this number if running into timer too close errors when doing long filament moves.
- `tool_max_unload_attempts` (default: `2`): Max number of attempts to unload filament from toolhead when using buffer as ramming sensor
- `tool_max_load_checks` (default: `4`): Max number of attempts to check to make sure filament is loaded into toolhead extruder when using buffer as ramming sensor
- `z_hop` (default: `0`): Height to move up before and after a tool change completes
- `xy_resume` (default: `False`): Need description or remove as this is currently an unused variable
- `resume_speed` (default: `0`): Speed mm/s of resume move. Set to 0 to use gcode speed
- `resume_z_speed` (default: `0`): Speed mm/s of resume move in Z. Set to 0 to use gcode speed
- `global_print_current` (default: `None`): Global variable to set steppers current to a specified current when printing. Going lower than 0.6 may result in TurtleNeck buffer's not working correctly
- `enable_sensors_in_gui` (default: `False`): Set to True to show all sensor switches as filament sensors in mainsail/fluidd gui
- `load_to_hub` (default: `True`): Fast loads filament to hub when inserted, set to False to disable. This is a global setting and can be overridden at AFC_stepper
- `trsync_update` (default: `False`): Set to true to enable updating trsync value in klipper mcu. Enabling this and updating the timeouts can help with Timer Too Close(TTC) errors
- `trsync_timeout` (default: `0.05`): Timeout value to update in klipper mcu. Klippers default value is 0.025
- `trsync_single_timeout` (default: `0.5`): Single timeout value to update in klipper mcu. Klippers default value is 0.250

## AFC_buffer
- `enable_sensors_in_gui` (default: `False`): Set to True toolhead sensors switches as filament sensors in mainsail/fluidd gui, overrides value set in AFC.cfg
- `accel` (default: `0`): Error if buffer is not configured correctly
- `velocity` (default: `0`): Set buffer velocity for forward assist.

## AFC_extruder
- `enable_sensors_in_gui` (default: `False`): Set to True toolhead sensors switches as filament sensors in mainsail/fluidd gui, overrides value set in AFC.cfg

## AFC_hub
- `assisted_retract` (default: `False`): if True, retracts are assisted to prevent loose windings on the spool

## AFC_prep
- `delay_time` (default: `0.1, minval=0.0`): Time to delay when moving extruders and spoolers during PREP routine
- `enable` (default: `False`): Set True to disable PREP checks
- `disable_unload_filament_remapping` (default: `False`): Set to True to disable remapping UNLOAD_FILAMENT macro to TOOL_UNLOAD macro

## AFC_stepper
- `hub` (default: `None`): Hub name(AFC_hub) that belongs to this stepper, overrides hub that is set in unit(AFC_BoxTurtle/NightOwl/etc) section.
- `buffer` (default: `None`): Buffer name(AFC_buffer) that belongs to this stepper, overrides buffer that is set in extruder(AFC_extruder) or unit(AFC_BoxTurtle/NightOwl/etc) sections.
- `extruder` (default: `None`): Extruder name(AFC_extruder) that belongs to this stepper, overrides extruder that is set in unit(AFC_BoxTurtle/NightOwl/etc) section.
- `led_index` (default: `None`): LED index of lane in chain of lane LEDs
- `led_fault` (default: `None`): LED color to set when faults occur in lane        (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `led_ready` (default: `None`): LED color to set when lane is ready               (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `led_not_ready` (default: `None`): LED color to set when lane not ready              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `led_loading` (default: `None`): LED color to set when lane is loading             (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `led_loading` (default: `None`): LED color to set when lane is loaded              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `led_unloading` (default: `None`): LED color to set when lane is unloading           (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `led_tool_loaded` (default: `None`): LED color to set when lane is loaded into tool    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `long_moves_speed` (default: `None`): Speed in mm/s to move filament when doing long moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `long_moves_accel` (default: `None`): Acceleration in mm/s squared when doing long moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `short_moves_speed` (default: `None`): Speed in mm/s to move filament when doing short moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `short_moves_accel` (default: `None`): Acceleration in mm/s squared when doing short moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `short_move_dis` (default: `None`): Move distance in mm for failsafe moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `max_move_dis` (default: `999999`): Maximum distance to move filament. AFC breaks filament moves over this number into multiple moves. Useful to lower this number if running into timer too close errors when doing long filament moves. Setting value here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section
- `dist_hub` (default: `60`): Bowden distance between Box Turtle extruder and hub
- `park_dist` (default: `10`): Currently unused
- `load_to_hub` (default: `True`): Fast loads filament to hub when inserted, set to False to disable. Setting here overrides global setting in AFC.cfg
- `enable_sensors_in_gui` (default: `False`): Set to True to show prep and load sensors switches as filament sensors in mainsail/fluidd gui, overrides value set in AFC.cfg
- `sensor_to_show` (default: `None`): Set to prep to only show prep sensor, set to load to only show load sensor. Do not add if you want both prep and load sensors to show in web gui
- `prep` (default: `None`): MCU pin for prep trigger
- `load` (default: `None`): MCU pin load trigger
- `afc_motor_rwd` (default: `None`): Reverse pin on MCU for spoolers
- `afc_motor_fwd` (default: `None`): Forwards pin on MCU for spoolers
- `afc_motor_enb` (default: `None`): Enable pin on MCU for spoolers
- `print_current` (default: `None`): Current to use while printing, set to a lower current to reduce stepper heat when printing. Defaults to global_print_current, if not specified current is not changed.
- `filament_diameter` (default: `1.75`): Diameter of filament being used
- `filament_density` (default: `1.24`): Density of filament being used
- `spool_inner_diameter` (default: `100`): Inner diameter in mm
- `spool_outer_diameter` (default: `200`): Outer diameter in mm
- `empty_spool_weight` (default: `190`): Empty spool weight in g
- `spool_weight` (default: `1000`): Remaining spool weight in g
- `assist_max_motor_rpm` (default: `500`): Max motor RPM
- `rwd_speed_multiplier` (default: `0.5`): Multiplier to apply to rpm
- `fwd_speed_multiplier` (default: `0.5`): Multiplier to apply to rpm

## AFC_BoxTurtle
- `hub` (default: `None`): Hub name(AFC_hub) that belongs to this unit, can be overridden in AFC_stepper section
- `extruder` (default: `None`): Extruder name(AFC_extruder) that belongs to this unit, can be overridden in AFC_stepper section
- `buffer` (default: `None`): Buffer name(AFC_buffer) that belongs to this unit, can be overridden in AFC_stepper section
- `led_fault` (default: `'1,0,0,0'`): LED color to set when faults occur in lane        (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_ready` (default: `'1,1,0,0'`): LED color to set when lane is ready               (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_not_ready` (default: `'1,1,0,0'`): LED color to set when lane not ready              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_loading` (default: `'1,0,0,0'`): LED color to set when lane is loading             (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_loading` (default: `'1,1,0,0'`): LED color to set when lane is loaded              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_unloading` (default: `'1,1,.5,0'`): LED color to set when lane is unloading           (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_tool_loaded` (default: `'1,1,0,0'`): LED color to set when lane is loaded into tool    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `long_moves_speed` (default: `100`): Speed in mm/s to move filament when doing long moves. Setting value here overrides values set in AFC.cfg file
- `long_moves_accel` (default: `400`): Acceleration in mm/s squared when doing long moves. Setting value here overrides values set in AFC.cfg file
- `short_moves_speed` (default: `25`): Speed in mm/s to move filament when doing short moves. Setting value here overrides values set in AFC.cfg file
- `short_moves_accel` (default: `400`): Acceleration in mm/s squared when doing short moves. Setting value here overrides values set in AFC.cfg file
- `short_move_dis` (default: `400`): Move distance in mm for failsafe moves. Setting value here overrides values set in AFC.cfg file
- `max_move_dis` (default: `999999`): Maximum distance to move filament. AFC breaks filament moves over this number into multiple moves. Useful to lower this number if running into timer too close errors when doing long filament moves. Setting value here overrides values set in AFC.cfg file

## AFC_NightOwl
- `hub` (default: `None`): Hub name(AFC_hub) that belongs to this unit, can be overridden in AFC_stepper section
- `extruder` (default: `None`): Extruder name(AFC_extruder) that belongs to this unit, can be overridden in AFC_stepper section
- `buffer` (default: `None`): Buffer name(AFC_buffer) that belongs to this unit, can be overridden in AFC_stepper section
- `led_fault` (default: `'1,0,0,0'`): LED color to set when faults occur in lane        (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_ready` (default: `'1,1,0,0'`): LED color to set when lane is ready               (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_not_ready` (default: `'1,1,0,0'`): LED color to set when lane not ready              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_loading` (default: `'1,0,0,0'`): LED color to set when lane is loading             (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_loading` (default: `'1,1,0,0'`): LED color to set when lane is loaded              (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_unloading` (default: `'1,1,.5,0'`): LED color to set when lane is unloading           (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `led_tool_loaded` (default: `'1,1,0,0'`): LED color to set when lane is loaded into tool    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here overrides values set in AFC.cfg file
- `long_moves_speed` (default: `100`): Speed in mm/s to move filament when doing long moves. Setting value here overrides values set in AFC.cfg file
- `long_moves_accel` (default: `400`): Acceleration in mm/s squared when doing long moves. Setting value here overrides values set in AFC.cfg file
- `short_moves_speed` (default: `25`): Speed in mm/s to move filament when doing short moves. Setting value here overrides values set in AFC.cfg file
- `short_moves_accel` (default: `400`): Acceleration in mm/s squared when doing short moves. Setting value here overrides values set in AFC.cfg file
- `short_move_dis` (default: `400`): Move distance in mm for failsafe moves. Setting value here overrides values set in AFC.cfg file
