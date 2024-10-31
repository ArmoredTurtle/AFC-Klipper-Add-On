# Armored Turtle Automated Filament Changer (AFC) Buffer

This file describes the `AFC_buffer` module, part of the Armored Turtle Automated Filament Changer (AFC) project.

## Overview

The `AFC_buffer` module is responsible for handling two types of buffers: [TurtleNeck](https://github.com/ArmoredTurtle/TurtleNeck), [TurtleNeck 2.0](https://github.com/ArmoredTurtle/TurtleNeck2.0) and [Annex Engineering Belay](https://github.com/Annex-Engineering/Belay). The Turtleneck buffer involves two sensors (advance and trailing), while the Belay buffer uses a single sensor to control filament movement.

The buffer adjusts the filament movement based on sensor inputs and can either compress or expand to manage filament feeding properly. Each buffer type has unique configuration options and behaviors.

## Basic Functionality

The AFC is a two extruder filament changer. The primary extruder is at the print head(s) and the second is in the AFC unit. While the 2 extruders are synced they will never be perfect. This is where a buffer comes in. The buffer is used to make up for any inconsistencies in the sync between the 2 stepper motors.

### TurtleNeck Style buffer

Two sensor TurtleNeck style buffers are used to modulate the rotation distance of the secondary extruder. This is done by increasing or decreasing the rotation distance if the buffer is expanded or compressed. 

*If the `advance` sensor is triggered, this means that the buffer is compressed, then the AFC will decrease rotation distance in order to move filament quicker to the primary extruder. 

*If the `trailing` sensor is triggered, this means that the buffer is expanded, then the AFC will increase rotation distance in order to slow the filament moving to the primary extruder.

### Belay Style buffer

With the current implementation of `AFC_buffer` support for Belay is limited. Belay will still help to keep even tension on the primary extruder but in a different way. First the AFC rotation distance has to be greater than the rotation distance of the primary extruder. While printing, the AFC will be pushing slightly less filament than the primary extruder, this will cause the Belay to become compressed towards it's switch. When the switch is reached the AFC will push a configured amount of material to expand the Belay. This will continue for the duration of the print.

## Configuration

### Required AFC Configuration Options

In `AFC.cfg`, `Buffer_Name` must be defined. The buffer name must match the defined buffer name in the AFC hardware configuration file.

Example:
`Buffer_Name: TN`

### Required AFC Hardware Configuration Options

In your SFC hardware configuration file, ensure you include the following options:

### TurtleNeck Style buffer

- **advance_pin**: Pin for the advance sensor.
- **trailing_pin**: Pin for the trailing sensor.

### Belay Style buffer

- **pin**: Pin for the buffer sensor.
- **distance**: Distance the filament should move when triggered.

### Example Configs

```
[AFC_buffer TN]
advance_pin: mcu:PB1
trailing_pin: mcu:PB2
multiplier_high: 1.15
multiplier_low: 0.95
```

```
[AFC_buffer TN2]
advance_pin: !TN:PB1
trailing_pin: !TN:PB2
multiplier_high: 1.15
multiplier_low: 0.95
```

```
[AFC_buffer Belay]
pin: mcu:PB0
distance: 15.0
velocity: 1000
accel: 1000
```

## AFC buffer commands

### QUERY BUFFER

The `QUERY_BUFFER` command reports the current state of the buffer sensor and, if applicable, the rotation distance of the AFC stepper motor. 

Example usage:
`QUERY_BUFFER BUFFER=Turtleneck`

Example output:
`Turtleneck: Expanded`

### SET_ROTATION_FACTOR
_for TurtleNeck Style Buffers_

This command allows the adjustment of rotation distance of the current AFC stepper motor by applying a factor. Factors greater than 1 will increase the rate filament is fed to the primary extruder, factors less than 1 but greater than 0 will decrease the rate filament to the primary extruder.

Example Usage:
`SET_ROTATION_FACTOR FACTOR=1.1`
