--- 
Title: Using the Buffer as a Ram Sensor
---

# Armored Turtle Automated Filament Control (AFC) Buffer Ram Sensor

This file describes using a filament buffer as a ram sensor. This is part of the Armored Turtle Automated Filament
Control (AFC) project.

## Overview

Ram sensor is compatible with two types of buffers: [TurtleNeck](https://github.com/ArmoredTurtle/TurtleNeck), 
[TurtleNeck 2.0](https://github.com/ArmoredTurtle/TurtleNeck2.0).

The filament loading and unloading process can use the two sensor design of these buffers in order to evaluate the 
position of the filament.

### Basic Functionality

During `TOOL_LOAD` filament will travel to buffer sensor and then execute the `afc_bowden_length` to the tool head

- If the buffer is expanded after the `afc_bowden_length` is complete then it will move forward with the tool load.
- If the buffer is not expanded after the `afc_bowden_length` then AFC will perform short moves until the buffer
  expands and the tool load will continue.
- After the `tool_stn` is complete the AFC will then pull back off the advance sensor, checking that it was loaded
  successfully and resetting the buffer.

During `TOOL_UNLOAD` AFC will perform the user specified macros (cut/tip shaping etc.).

- Once these macros are finished AFC will pull back to the trailing sensor to insure consistent position of the
  buffer.
- The rest of the unload will follow.

## Configuration

### Required Configuration

Under `[AFC_extruder extruder]` section:

`pin_tool_start: buffer`

- By setting the `pin_tool_start` to `buffer` the ram sensor will be enabled.

Under `[AFC_Buffer TN2]`

!!! note
    `advance_pin` and `trailing_pin` must be defined

- `advance_pin`: Pin for the advance sensor.
- `trailing_pin`: Pin for the trailing sensor.

Under `[AFC_extruder <extruder_name>]`, `[AFC_<unit_name> <name>]` or `[AFC_stepper lane(n)]`; the buffer name must be
defined. This allows having a buffer per extruder, unit or lane. Defining buffer in `AFC_stepper` config overrides
buffer variable being set in other places, and defining buffer in `AFC_<unit_name>` overrides buffer being set in
`AFC_extruder`.

Examples:

```
[AFC_extruder <extruder_name>]
buffer: TN
pin_tool_start: buffer
<reset_of_config>
```

```
[AFC_BoxTurtle <unit_name>]
buffer: TN
<reset_of_config>
```

```
[AFC_Stepper <stepper_name>]
buffer: TN
<reset_of_config>
```

### Optional Configuration

Under `[AFC_extruder extruder]` section:

`tool_max_load_checks: 4` can be set for the amount of times the AFC pulls back after load to come off the advance
 sensor. See [here](../configuration/AFC_Hardware.cfg.md#afc_buffer-buffer_name-section) for more information.

- Default 4

`tool_max_unload_attempts: 2` can be set for the amount of repetitions AFC pulls back to trailing sensor on unload.
See [here](../configuration/AFC_Hardware.cfg.md#afc_buffer-buffer_name-section) for more information.

- Default 2

## Tuning

- `afc_bowden_length` should be set so that on unload the filament comes just short of the hub sensor.
- `tool_unload_stn` should be set so that on unload the filament clears the extruder.