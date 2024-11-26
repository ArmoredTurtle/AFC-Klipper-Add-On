# Armored Turtle Automated Filament Changer (AFC) Buffer

This file describes the `AFC_buffer` module, part of the Armored Turtle Automated Filament Changer (AFC) project.

## Overview

The `AFC_buffer` module is responsible for handling two types of buffers: [TurtleNeck](https://github.com/ArmoredTurtle/TurtleNeck), [TurtleNeck 2.0](https://github.com/ArmoredTurtle/TurtleNeck2.0) and [Annex Engineering Belay](https://github.com/Annex-Engineering/Belay). The Turtleneck buffer involves two sensors (advance and trailing), while the Belay buffer uses a single sensor to control filament movement.

The buffer adjusts the filament movement based on sensor inputs and can either compress or expand to manage filament feeding properly. Each buffer type has unique configuration options and behaviors.

### Basic Functionality

The AFC is a two extruder filament changer. The primary extruder is at the print head(s) and the second is in the AFC unit. While the 2 extruders are synced they will never be perfect. This is where a buffer comes in. The buffer is used to make up for any inconsistencies in the sync between the 2 stepper motors.

## TurtleNeck Style buffer

Two sensor TurtleNeck-style buffers are used to modulate the rotation distance of the secondary extruder. The buffer's expansion or compression increases or decreases the rotation distance. 

* If the `trailing` sensor is triggered, this means that the buffer is compressed, the AFC will decrease rotation distance in order to move the filament quicker to the primary extruder. 

* If the `advance` sensor is triggered, this means that the buffer is expanded, the AFC will increase rotation distance in order to slow the filament moving to the primary extruder.

### Turtleneck 1.0

![Heading](https://github.com/user-attachments/assets/c5b6faa9-e110-4e4d-a5d5-b909daad857a)


### TurtleNeck 2.0

[__Flashing TurtleNeck 2.0__](https://github.com/ArmoredTurtle/TurtleNeck2.0/blob/main/Flashing/README.md)

![image](https://github.com/user-attachments/assets/3feba749-e228-4dd4-b6bc-bc3089d14dce)

## Belay Style buffer

With the current implementation of `AFC_buffer` support for Belay is limited. Belay will still help to keep even tension on the primary extruder but in a different way. First, the AFC rotation distance has to be greater than the rotation distance of the primary extruder. While printing, the AFC will be pushing slightly less filament than the primary extruder, this will cause the Belay to become compressed toward the switch. When the switch is reached the AFC will make a configured amount of material to expand the Belay. This will continue for the duration of the print.

## Configuration

### Required AFC Configuration Options

In `AFC_Hardware.cfg`, `buffer` must be defined. 

Example under `AFC_extruder`:
`buffer: TN`

### Required AFC Hardware Configuration Options

In your AFC hardware configuration file, ensure you include the following options:

### TurtleNeck Style buffer

- **advance_pin**: Pin for the advance sensor.
- **trailing_pin**: Pin for the trailing sensor.

_Optional for more fine tuning_
- **multiplier_high**: Factor to move more filament through the secondary extruder.
- **multiplier_low**: Factor to move less filament through the secondary extruder.

__TurtleNeck 2.0 LED Indicator Configuration__

_add to AFC_hardware file_

```
[AFC_led Buffer_Indicator]
pin: TN:PD3
chain_count: 1
color_order: GRBW
initial_RED: 0.0
initial_GREEN: 0.0
initial_BLUE: 0.0
initial_WHITE: 0.0
```

_Optional AFC.cfg LED settings_

```
led_buffer_advancing: 0,0,1,0
led_buffer_trailing: 0,1,0,0
led_buffer_disable: 0,0,0,0.25
```

### Belay Style buffer

- **pin**: Pin for the buffer sensor.
- **distance**: Distance the filament should move when triggered.

_Optional_
- **velocity**: The speed the lane will move the filament.
- **accel**: Lane acceleration.

### Example Configs

```
[AFC_buffer TN]
advance_pin:     # set advance pin
trailing_pin:    # set trailing pin
multiplier_high: 1.05   # default 1.05, factor to feed more filament
multiplier_low:  0.95   # default 0.95, factor to feed less filament
velocity: 100

[AFC_buffer TN2]
advance_pin: !turtleneck:ADVANCE
trailing_pin: !turtleneck:TRAILING
multiplier_high: 1.05   # default 1.05, factor to feed more filament
multiplier_low:  0.95   # default 0.95, factor to feed less filament
led_index: Buffer_Indicator:1
velocity: 100

[AFC_buffer Belay]
pin: mcu:BUFFER
distance: 12
velocity: 1000
accel: 1000
```

## AFC buffer commands

### QUERY BUFFER

The `QUERY_BUFFER` command reports the current state of the buffer and, if applicable, the rotation distance of the AFC stepper motor. 

Example usage:
`QUERY_BUFFER BUFFER=Turtleneck`

Example outputs:
`Turtleneck: Trailing` _buffer is moving from the Advance trigger to the Trailing_
`Turtleneck: Advancing` _buffer is moving from the Trailing trigger to the Advance_ 

### SET_ROTATION_FACTOR
_for TurtleNeck Style Buffers_

This command allows the adjustment of rotation distance of the current AFC stepper motor by applying a factor. Factors greater than 1 will increase the rate filament is fed to the primary extruder, factors less than 1 but greater than 0 will decrease the rate filament to the primary extruder.

Example Usage:
`SET_ROTATION_FACTOR FACTOR=1.1`

### SET_BUFFER_MULTIPLIER
_for TurtleNeck Style Buffers_

`SET_BUFFER_MULTIPLIER` used to live adjust the high and low multipliers for the buffer
- To change `multiplier_high`: `SET_BUFFER_MULTIPLIER MULTIPLIER=HIGH FACTOR=1.2`
- To change `multiplier_low`: `SET_BUFFER_MULTIPLIER MULTIPLIER=HIGH FACTOR=0.8`
    
__Buffer config section must be updated for values to be saved__
