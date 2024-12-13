# Armored Turtle Automated Filament Changer (AFC) Buffer Ram Sensor

This file describes using a filament buffer as a ram sensor. This is part of the Armored Turtle Automated Filament Changer (AFC) project.

## Overview

Ram sensor is compatible with two types of buffers: [TurtleNeck](https://github.com/ArmoredTurtle/TurtleNeck), [TurtleNeck 2.0](https://github.com/ArmoredTurtle/TurtleNeck2.0).

The filament loading and unloading use the two sensor design to evaluate the position of the filament.

### Basic Functionality

- During `TOOL_LOAD` filament will travel to buffer sensor and then execute the `afc_bowden_length` to the tool head
  - If the buffer is expanded after the `afc_bowden_length` is complete then it will move forward with the tool load.
  - If the buffer is not expanded after the `afc_bowden_length` then AFC will perform short moves until the buffer expands and the tool load will continue.
  - After the `tool_stn` is complete the AFC will then pull back off the advance sensor, checking that it was loaded successfully and resetting the buffer.

- During `TOOL_UNLOAD` AFC will perform the user specified macros (cut/tip shaping etc.).
  - Once these macros are finished AFC will pull back to the trailing sensor to insure consistent position of the buffer.
  - The rest of the unload will follow.

## Configuration

### Required Configuration

Under `[AFC_extruder extruder]` section:

- `pin_tool_start: buffer`
  - By setting the `pin_tool_start` to `buffer` the ram sensor will be enabled.

Under `[AFC_Buffer TN2]`
__advance_pin and trailing_pin must be defined__

- __advance_pin__: Pin for the advance sensor.
- __trailing_pin__: Pin for the trailing sensor.

### Optional Configuration

Under `[AFC_extruder extruder]` section:

- `tool_max_load_checks: 4` can be set for the amount of times the AFC pulls back after load to come off the advance sensor.
  - Default 4
- `tool_max_unload_attempts: 2` can be set for the amount of repetitions AFC pulss back to trailing sensor on unload.
  - Default 2

## Tuning

- `afc_bowden_length` should be set so that on unload the filament comes just short of the hub sensor
- `tool_unload_stn` should be set so that on unload the filament clears the extruder