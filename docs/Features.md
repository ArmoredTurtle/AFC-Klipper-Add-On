# Overview of features 

This file goes over the features that can be found in Armored Turtle Automated Filament Control (AFC) Software

## TurtleNeck Buffer Ram Sensor
AFC allows the use of using the TurtleNeck Buffers as a ram sensor for detecting when filament is loaded to the toolhead extruder. This can be used inplace of a toolhead filament sensor. To learn more about this feature please see [Buffer Ram Sensor](Buffer_Ram_Sensor.md) document

## Bypass
By default if a hardware sensor is not setup for a bypass AFC will create a virtual bypass filament sensor. Enabling the virtual filament sensor disables AFC functionality and enabled state persists across reboots.

You can also enable AFC bypass with a hardware sensor by printing out [bypass](https://github.com/ArmoredTurtle/AFC-Accessories/tree/main/AFC_Bypass) accessory, connecting inline after your buffer and adding a bypass filament sensor to klipper config like below. Once filament is inserted into the bypass side, the switch disables AFC functionality so you can print like normal.

```
[filament_switch_sensor bypass]
switch_pin: <replace with MCU pin that switch is connected to>
pause_on_runout: False
```

When either bypass is enabled/filament detect all AFC functionality with loading to the toolhead is disabled. Calling the `TOOL_UNLOAD` macro will call the `UNLOAD_FILAMENT` macro if it exists so that filament can still be manually unload from the toolhead.

## Lower stepper current when printing
For longer prints you may want to have the ability to lower BoxTurtles steppers current as they can get hot when engaged for a long period of time.

Enabling lower current during printing can be enabled two ways:
1. Set `global_print_current` in AFC.cfg file
2. Set `print_current` for each AFC_stepper, this will override `global_print_current` in AFC.cfg

During testing it was found that 0.6A worked well during printing and kept the steppers warms to the touch. Would not suggest going lower than this or the TurtleNeck buffers may not work as intended.


## Enabling switches to show up in mainsail/fluidd guis
AFC has the ability to add sensors as filament switches so they show up in mainsail/fluidd web gui. This can either be enabled globally by adding/uncommenting `enable_sensors_in_gui: True` in AFC.cfg file or enabled/disabled in individual sections in your config file. Enabling this globally us usefull for debugging purposes, but setting in individual sections will override the global setting

AFC_buffer, AFC_extruder, AFC_hub, and AFC_stepper sections in your AFC_hardware.cfg or AFC_Turtle(n).cfg have the ability to enable sensor by adding `enable_sensors_in_gui: True`. There is an extra config value for AFC_stepper to allow you to either show both sensors or just prep/load sensors by using `sensor_to_show: prep` or `sensor_to_show: load`, leaving out sensor_to_show will show both sensors.

## Tool change count
AFC has the ability to keep track of number of tool changes when doing multicolor prints. The macro can be used to set total number of toolchanges from slicer. AFC will keep track of tool changes and print out
current tool change number when a T(n) command is called from gcode.

This call can be added to the slicer by adding the following lines to Change filament G-code section in your slicer.
You may already have `T[next_extruder]`, just make sure the toolchange call is after your T(n) call
```cfg
T[next_extruder]
{ if toolchange_count == 1 }SET_AFC_TOOLCHANGES TOOLCHANGES=[total_toolchanges]{endif }
```

The following can also be added to your `PRINT_END` section in your slicer to set number of toolchanges back to zero
`SET_AFC_TOOLCHANGES TOOLCHANGES=0`

## Setting extruder temp
AFC has the ability to automatically set extruder temperature based off filament material type loaded or spoolman extruder temperature if its set.

If not using spoolman make sure the material is set for your lanes and the temperature values will be pulled from `default_material_temps` variable in `AFC.cfg` file. This list can also be updated/added to, just make sure new entries have a comma inbetween and follow current format when adding new variable.

If spoolman extruder temperature or material type is not defined AFC default's to `min_extrude_temp` variable defined in `[extruder]` section in `printer.cfg`

```cfg
default_material_temps: PLA:210, ABS:235, ASA:235 # Default temperature to set extruder when loading/unloading lanes.
```

## Loading filament to hub
For users that have a hub not located in their Box Turtle, AFC has the ability to load filament to their hub once its inserted. This is turned on by default and this will happen even if your hub is located in your Box Turtle. This can be disabled by setting `load_to_hub: False` in your `AFC.cfg` file. Also individual lanes can be turn on/off by setting `load_to_hub: True/False` under `[AFC_stepper <lane_name>]` section in your config.

## Variable purge length on filament change
AFC has the ability to purge different lengths with orcas flush volumes when doing filament changes with T(n) macros. To use this feature update your Change Filament G-Code section in your orca slicer to the following:

`T[next_extruder] PURGE_LENGTH=[flush_length]`

Could also be added to your PRINT_START macro with a specific length, this would be ideal for if your first filament is not currently loaded as the PURGE_LENGTH from Orca for the first change would be zero

`T{initial_tool} PURGE_LENGTH=100`

**NOTE: If your first filament is not currently loaded and needs to change, `PURGE_LENGTH` will be zero and the poop macro will then use `variable_purge_length_minimum` from AFC_Macro_Vars.cfg file, so make sure this is set correctly for your printer**