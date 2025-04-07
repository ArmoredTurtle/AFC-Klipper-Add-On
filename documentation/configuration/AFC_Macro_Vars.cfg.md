# [AFC_Macro_Vars.cfg] Configuration Overview

The `AFC_Macro_Vars.cfg` file is used to define the macro variables for the AFC-Klipper-Add-On. This file contains a 
set of variables that are used throughout the AFC-Klipper-Add-On to control various aspects of its behavior.

This file is split up into multiple sections, each of which is used to define a specific set of variables. The sections are
defined in the standard `[gcode_macro <macro_name>]` format, where `<macro_name>` is the name of the macro. 
Each section contains a set of variables that are used to control the behavior of the macro.

!!! info

    As a reminder, when a macro is preceeded by a `_` (underscore), it is a `hidden` macro. This means that it will not be
    listed in the `Gcode Macro` menu in Fluidd or Mainsail. This is useful for macros that are used internally by the
    AFC-Klipper-Add-On and should not be called directly.

These macros are installed upon installation of the AFC-Klipper-Add-On and are located in the 
`~/printer_data/config/AFC/macros` directory. These macros are **NOT** updated when new software versions are released. 

We recommend that you follow the announcements in the [afc-updates](https://discord.com/channels/1229586267671629945/1318916339674644541) 
channel of the Armored Turtle Discord server for information on when software updates are available. The decision 
was made to not automatically override these macros to prevent any potential issues with user modifications to the 
macros and unexpected behavior.

!!! info
    Travel speeds in this file are defined in mm/s, however typically Klipper expects 
    this to be in mm/min. Our macros have been designed to convert this value to mm/min for you.

## [_AFC_GLOBAL_VARS]

The `_AFC_GLOBAL_VARS` section is used to define the global variables for the AFC-Klipper-Add-On. These variables are
used throughout the AFC provided macros to control various aspects of its behavior. 

``` cfg
[gcode_macro _AFC_GLOBAL_VARS]
description: Global variables used in multiple macros
gcode: # Leave empty

variable_stepper_name                    : 'lane'
variable_travel_speed                    : '120'
variable_z_travel_speed                  : '30'
variable_accel                           : '1000'
variable_verbose                         : '1'
```

-----
=== "variable_stepper_name"
    Default: `'lane'`  
    This is the value that is used to define the lane name for AFC. This should be 
    set to the same value in the `AFC_UnitType_1.cfg` file. 
    
=== "Example"
    When this is set to `'lane'`, all other macros would use the format of `lane1` or `lane2` 
    when interacting with macros. If this was set to, for example, `'leg'`, then the expected
    format would `'leg1'` or `'leg2'`. 

-----
=== "variable_travel_speed"
    Default: `'120'`  
    This is the value that is used to define the travel speed for movement speeds in `mm/s` for
    any AFC gcode macros. 

=== "Example"
    When this is set to `'120'`, all gcode macros would be executed for example with 
    a speed of `G0 X100 F7200` or `G1 X100 F7200`. Remember, we convert this to `mm/min` for you in the format
    of `variable_travel_speed * 60`.

-----
=== "variable_z_travel_speed"
    Default: `'30'`  
    This is the value that is used to define the Z travel speed for movement speeds in `mm/s` for
    any AFC gcode macros. 

=== "Example"
    When this is set to `'30'`, all gcode macros would be executed for example with
    a speed of `G0 Z10 F1800` or `G1 Z10 F1800`. Remember, we convert this to `mm/min` for you in the format
    of `variable_z_travel_speed * 60`.

-----
=== "variable_accel"
    Default: `'2000'`  
    This is the value that is used to define the acceleration for movement speeds in `mm/s` for
    any AFC gcode macros.

=== "Example"
    This value is typically lower than your acceleration that is used on your printer in order to ensure
    accuracy and prevent any issues. This value is usually set by defining a temporary acceleration limit
    such as `SET_VELOCITY_LIMIT ACCEL={variable_accel}`.

-----
=== "variable_verbose"
    Default: `'1'`  
    This is the value that is used to define the verbosity level for the AFC-Klipper-Add-On macros. 
    This value is used to control the amount of information that is printed to the console 
    during the execution of the macros.

=== "Levels"
    - `0`: No output
    - `1`: Limited output
    - `2`: All output

## [_AFC_CUT_TIP_VARS]

The `_AFC_CUT_TIP_VARS` section is used to define the variables for the AFC-Klipper-Add-On for the `CUT` macro. These 
variables help define items such as locations, speed, and other parameters that are used in the `CUT` macro. 

!!! warning
    These variables **MUST** be set correctly when `tool_cut` is set to `True` in your `AFC.cfg` file.

``` cfg
[gcode_macro _AFC_CUT_TIP_VARS]
description: Toolhead tip cutting macro configuration variables
gcode: # Leave empty
variable_pin_loc_xy               : -1, -1  
variable_cut_accel                : 0
variable_cut_direction            : "left"
variable_pin_park_dist            : 6.0       
variable_cut_move_dist            : 8.5 
variable_cut_fast_move_speed      : 32  
variable_cut_slow_move_speed      : 10  
variable_evacuate_speed           : 150  
variable_cut_dwell_time           : 50  
variable_cut_fast_move_fraction   : 0.85    
variable_extruder_move_speed      : 25   
variable_restore_position         : False
variable_retract_length           : 20
variable_quick_tip_forming        : False
variable_cut_count                : 2
variable_rip_length               : 1.0 
variable_rip_speed                : 3 
variable_pushback_length          : 15
variable_safe_margin_xy           : 30, 30 
variable_cut_current_stepper_x: 0
variable_cut_current_stepper_y: 0
variable_cut_current_stepper_z: 0
variable_conf_name_stepper_x: "tmc2209 stepper_x"
variable_conf_name_stepper_y: "tmc2209 stepper_y"
variable_conf_name_stepper_z: "tmc2209 stepper_z"
variable_awd: False
```

-----
=== "variable_pin_loc_xy"
    Default: `-1, -1`  
    This is the value that is used to define the location of the pin in the X and Y axis. 
    This should be the position of the toolhead where the cutter arm just lightly touches the 
    depressor pin.

-----
=== "variable_cut_accel"
    Default: `0`  
    Accel during cut. This will overwrite the global accel for this macro. Set to 0 to use global accel

-----
=== "variable_cut_direction"
    Default: `"left"`  
    This is the value that is used to define the direction of the cut move. This should be set to either 
    `left`, `right`, `front`, or `back`.

-----
=== "variable_pin_park_dist"
    Default: `6.0`  
    This is the value that is used to move the toolhead to cut the filament and to create a small safety distance 
    that aids in generating momentum. This distance is in mm.

-----
=== "variable_cut_move_dist"
    Default: `8.5`  
    Position of the toolhead when the cutter is fully compressed. Distance the toolhead needs to travel to compress the 
    cutter arm. To calculate this distance start at the pin_loc_xy position and move your toolhead till the cutter 
    arm is completely compressed. Take 0.5mm off this distance as a buffer. 

=== "Example"
    `pin_loc_x : 9, 310`  fully compressed at 0, 310 set `cut_move_dist` to 8.5

-----
The following variables are used to define the speed of the cutting action.  Note that if the cut speed is too fast, 
the steppers can lose steps. Therefore, for a cut:

- We first make a fast move to accumulate some momentum and get the cut blade to the initial contact with the filament.
- We then make a slow move for the actual cut to happen.
 
-----
=== "variable_cut_fast_move_speed"
    Default: `32`  
    This is the value that is used to define the fast move speed for the cutter. This speed is in `mm/s`.

-----
=== "variable_cut_slow_move_speed"
    Default: `10`  
    This is the value that is used to define the slow move speed for the cutter. This speed is in `mm/s`.

-----
=== "variable_evacuate_speed"
    Default: `150`  
    This is the value that is used to define the evacuation speed for the cutter. This speed is in `mm/s`.

-----
=== "variable_cut_dwell_time"
    Default: `50`  
    This is the value that is used to define the dwell time for the cutter at the cut point. This time is in `ms`.

-----
=== "variable_cut_fast_move_fraction"
    Default: `0.85`  
    This is the value that is used to define the fraction of the cut move that is done at the fast speed. 
    This value should be between `0` and `1`.

-----
=== "variable_extruder_move_speed"
    Default: `25`  
    This is the value that is used to define the speed of the extruder during the cut. This speed is in `mm/s`.

-----
=== "variable_restore_position"
    Default: `False`  
    This is the value that is used to define whether the toolhead returns to the initial position after the cut is 
    complete. 
    This value should be set to `True` or `False`.

-----
=== "variable_retract_length"
    Default: `20`  
    Distance to retract prior to making the cut, this reduces wasted filament but might cause clog if set too large 
    and/or if there are gaps in the hotend assembly. 

!!! note
    This must be less than the distance from the nozzle to the cutter

-----
=== "variable_quick_tip_forming"
    Default: `False`  
    This is the value that is used to define whether the quick tip forming is enabled. This can help prevent 
    clogging of some toolheads by doing a quick tip forming before the cut. 
    This value should be set to `True` or `False`.

-----
=== "variable_cut_count"
    Default: `2`  
    This is the value that is used to define the number of times to run the cut movement.

-----
=== "variable_rip_length"
    Default: `1.0`  
    Distance in mm to retract to aid level decompression. This must be >= 0.

-----
=== "variable_rip_speed"
    Default: `3`  
    Speed in mm/s to retract to aid level decompression. This must be >= 0.

-----
=== "variable_pushback_length"
    Default: `15`  
    Distance in mm to push back the remaining tip from the cold end into the hotend.

!!! note
    This must be less then the `retract_length`.

-----
=== "variable_pushback_dwell_time"
    Default: `20`  
    Time in ms to dwell at the end of the pushback. This is used to allow the filament to cool down before 
    retracting it back into the hotend.

-----
=== "variable_safe_margin_xy"
    Default: `30, 30`  
    Safety margin for fast vs slow travel. When traveling to the pin location we make a safer but longer move if we 
    are closer to the pin than this specified margin. Usually setting these to the size of the toolhead 
    (plus a small margin) should be good enough. 

=== "Example"
    For example, if your toolhead is 25mm wide, you can set this to `30, 30` to ensure that the toolhead 
    does not hit the pin when moving to the cut location.

-----
Some printers may need a boost of power to complete the cut without skipping steps.

One option is to increase the current for those steppers in printer.cfg. Another option is to use these variables to 
set a current that is only used during the cut motion. Different combinations of kinematics and cutter configurations 
engage different combinations of steppers for that motion. If enabled, the values in the 
`variable_conf_name_stepper_<stepper>` need to match the stepper names in your `printer.cfg` file.

!!! note
    The override is skipped if the current is 0. These are typically enabled if layer shifts occur when cutting.

-----
=== "variable_cut_current_stepper_x"
    Default: `0`  
    This is the value that is used to define the current for the X stepper during the cut. 
    This value should be set to `0` to disable the override.

-----
=== "variable_cut_current_stepper_y"
    Default: `0`  
    This is the value that is used to define the current for the Y stepper during the cut. 
    This value should be set to `0` to disable the override.

-----
=== "variable_cut_current_stepper_z"
    Default: `0`  
    This is the value that is used to define the current for the Z stepper during the cut. 
    This value should be set to `0` to disable the override.   

---
=== "variable_conf_name_stepper_x"
    Default: `"tmc2209 stepper_x"`  
    This is the value that is used to define the name of the X stepper in the printer.cfg file. 
    This value should be set to the name of the stepper in your printer.cfg file.

-----
=== "variable_conf_name_stepper_y"
    Default: `"tmc2209 stepper_y"`  
    This is the value that is used to define the name of the Y stepper in the printer.cfg file. 
    This value should be set to the name of the stepper in your printer.cfg file.

-----
=== "variable_conf_name_stepper_z"
    Default: `"tmc2209 stepper_z"`  
    This is the value that is used to define the name of the Z stepper in the printer.cfg file. 
    This value should be set to the name of the stepper in your printer.cfg file.

-----
=== "variable_awd"
    Default: `False`  
    This is the value that is used to define whether system is using 'AWD' to adjust these for multiple X or Y 
    steppers. 
    This value should be set to `True` or `False`.

## [_AFC_POOP_VARS]

The `_AFC_POOP_VARS` section is used to define the variables for the AFC-Klipper-Add-On for the `POOP` macro. These
variables help define items such as locations, speed, and other parameters that are used in the `POOP` macro.

!!! warning
    These variables **MUST** be set correctly when `poop` is set to `True` in your `AFC.cfg` file.

``` cfg
[gcode_macro _AFC_POOP_VARS]
description: Poop macro configuration variables
gcode: # Leave empty
variable_purge_loc_xy             : -1, -1    
variable_purge_spd                : 6.5      
variable_z_purge_move             : True 
variable_fast_z                   : 200
variable_z_lift                   : 20    
variable_restore_position         : False 
variable_purge_start              : 0.6
variable_part_cooling_fan         : True      
variable_part_cooling_fan_speed   : 1.0     
variable_purge_cool_time          : 2
variable_purge_length             : 72.111
variable_purge_length_minimum     : 60.999
variable_purge_length_modifier    : 1
variable_purge_length_addition    : 0
```

-----
=== "variable_purge_loc_xy"
    Default: `-1, -1`  
    This is the value that is used to define the location of the purge in the X and Y axis. 
    (x,y) Location of where to purge.

-----
=== "variable_purge_spd"
    Default: `6.5`  
    This is the value that is used to define the purge speed in `mm/s`.

-----
=== "variable_z_purge_move"
    Default: `True`  
    This is the value that is used to define whether the Z axis should be moved during the purge.
    Set to `False` to not move in Z during the `poop` macro.
    This value should be set to `True` or `False`.

-----
=== "variable_fast_z"
    Default: `200`  
    Speed, in mm/s to lift z after the purge is completed. It is a faster lift to keep it from 
    sticking to the toolhead.

-----
=== "variable_z_lift"
    Default: `20`  
    This is the value that is used to define the Z lift distance in mm. 
    This is the distance that the toolhead will be lifted after the purge is completed.

-----
=== "variable_restore_position"
    Default: `False`  
    This is the value that is used to define whether the toolhead returns to the initial position after the purge is 
    complete. 
    This value should be set to `True` or `False`.

-----
=== "variable_purge_start"
    Default: `0.6`  
    The height to raise the nozzle above the tray before purging. This allows any built up pressure to escape before 
    the purge.

-----
=== "variable_part_cooling_fan"
    Default: `True`  
    Set the part cooling fan speed. Disabling can help prevent the nozzle from cooling down and stimulate flow.
    Enabling it can prevent blobs from sticking together.
    This value should be set to `True` or `False`.

-----
=== "variable_part_cooling_fan_speed"
    Default: `1.0`  
    This is the value that is used to define the part cooling fan speed. 
    This value should be set to a value between `0` and `1`.

-----
=== "variable_purge_cool_time"
    Default: `2`  
    This is the value that is used to define the time to cool down the part cooling fan. 
    This value should be set to a value in seconds.

-----
=== "variable_purge_length"
    Default: `72.111`  
    Default purge length to fall back on when neither the tool map purge_volumes nor parameter PURGE_LENGTH is set. 
    This value should be set to a value in mm.

-----
=== "variable_purge_length_minimum"
    Default: `60.999`  
    The absolute minimum to purge, even if you didn't change tools. This is to prime the nozzle before printing.

-----
=== "variable_purge_length_modifier"
    Default: `1`  
    This is the value that is used to define the purge length modifier. The slicer values are a bit too wasteful. 
    This value can be tuned to get an optimal purge length. A good starting point is `0.6`. 
    This value should be set to a decimal value between `0` and `1`.

-----
=== "variable_purge_length_addition"
    Default: `0`  
    Length of filament to add after the purge volume. Purge volumes don't always take cutters into account and therefor 
    a swap from red to white might be long enough, but from white to red can be far too short. 
    When should you alter this value:

       INCREASE: When the dark to light swaps are good, but light to dark aren't.  
       DECREASE: When the light to dark swaps are good, but dark to light aren't.

    Don't forget to increase the `purge_length_modifier`.
    This value should be set to a decimal value between `0` and `1`.


## [_AFC_KICK_VARS]
The `_AFC_KICK_VARS` section is used to define the variables for the AFC-Klipper-Add-On for the `KICK` macro. These
variables help define items such as locations, speed, and other parameters that are used in the `KICK` macro.
!!! warning
    These variables **MUST** be set correctly when `kick` is set to `True` in your `AFC.cfg` file.

``` cfg
[gcode_macro _AFC_KICK_VARS]
description: Kick macro configuration variables
gcode: # Leave empty

variable_kick_start_loc           : -1,-1,10  
variable_kick_z                   : 1.5       
variable_kick_speed               : 150      
variable_kick_accel               : 0       
variable_kick_direction           : "right"   
variable_kick_move_dist           : 45        
variable_z_after_kick             : 10       
```

-----
=== "variable_kick_start_loc"
    Default: `-1,-1, 10`  
    This is the value that is used to define the location of the toolhead prior to the kick macro being executed. 
    This should be set to the location of the kick in the X,Y,Z axis.

-----
=== "variable_kick_z"
    Default: `1.5`  
    This is the value that is used to define the Z height to drop the toolhead for the kick macro.

-----
=== "variable_kick_speed"
    Default: `150`  
    This is the value that is used to define the speed of the kick in `mm/s`.

-----
=== "variable_kick_accel"
    Default: `0`  
    Accel of kick moves. This will overwrite the global accel for this macro. Set to 0 to use global acceleration 
    variable.

-----
=== "variable_kick_direction"
    Default: `"right"`  
    This is the value that is used to define the direction of the kick. This should be set to either 
    `left`, `right`, `front`, or `back`.

-----
=== "variable_kick_move_dist"
    Default: `45`  
    This is the value that is used to define the distance of the kick in mm. 
    This should be set to the distance of the kick in mm.

-----
=== "variable_z_after_kick"
    Default: `10`  
    This is the value that is used to define the Z height after the kick macro is executed. 
    This should be set to the height of the kick in mm.

## [_AFC_BRUSH_VARS]
The `_AFC_BRUSH_VARS` section is used to define the variables for the AFC-Klipper-Add-On for the `BRUSH` macro. These
variables help define items such as locations, speed, and other parameters that are used in the `BRUSH` macro.
!!! warning
    These variables **MUST** be set correctly when `brush` is set to `True` in your `AFC.cfg` file.

``` cfg
[gcode_macro _AFC_BRUSH_VARS]
description: Brush macro configuration variables
gcode: # Leave empty


variable_brush_loc                : -1,-1,-1  
variable_brush_clean_speed        : 150      
variable_brush_clean_accel        : 0 
variable_brush_width              : 30        
variable_brush_depth              : 10      
variable_y_brush                  : True     
variable_brush_count              : 4        
variable_z_move                   : -1
```

-----
=== "variable_brush_loc"
    Default: `-1,-1,-1`  
    Position of the center of the brush (Set Z to -1 if you don't want a z move)
    This should be set to the location of the brush in the X,Y,Z axis.

-----
=== "variable_brush_clean_speed"
    Default: `150`  
    This is the value that is used to define the speed of the cleaning moves in `mm/s`.

-----
=== "variable_brush_clean_accel"
    Default: `0`  
    Accel of brush moves. This will overwrite the global accel for this macro. Set to 0 to use global acceleration 
    variable.

-----   
=== "variable_brush_width"
    Default: `30`  
    This is the value that is used to define the width of the brush in mm. 
    This should be set to the total width in mm of the brush in the X direction.

-----
=== "variable_brush_depth"
    Default: `10`  
    This is the value that is used to define the depth of the brush in mm. 
    This should be set to the total depth in mm of the brush in the Y direction.

-----
=== "variable_y_brush"
    Default: `True`  
    True - Brush along Y axis first then X. False - Only brush along X.
    This value should be set to `True` or `False`.

-----
=== "variable_brush_count"
    Default: `4`  
    This is the value that is used to define the number of times to run the brush movement. 
    This should be set to the number of times to run the brush movement.

-----
=== "variable_z_move"
    Default: `-1`  
    Move in Z after brush to avoid bed if brush is at Z0 (Set z to -1 if you don't want a z move)

## [_AFC_PARK_VARS]
The `_AFC_PARK_VARS` section is used to define the variables for the AFC-Klipper-Add-On for the `PARK` macro. These
variables help define items such as locations, speed, and other parameters that are used in the `PARK` macro.
!!! warning
    These variables **MUST** be set correctly when `park` is set to `True` in your `AFC.cfg` file.

``` cfg
[gcode_macro _AFC_PARK_VARS]
description: Park macro configuration variables
gcode: # Leave empty

variable_park_loc_xy              : -1, -1    
variable_z_hop                    : 0 
```

-----
=== "variable_park_loc_xy"
    Default: `-1, -1`  
    This is the value that is used to define the location of the park in the X and Y axis. 
    This should be set to the location of the park in the X,Y axis.

-----
=== "variable_z_hop"
    Default: `0`  
    Height to raise Z when moving to park. Leave 0 to disable.
    If you want z_hop during toolchanges please set the value in the AFC.cfg.
```