# Armored Turtle Automated Filament Changer (AFC) Buffer

This file describes the `AFC_buffer` module, part of the Armored Turtle Automated Filament Changer (AFC) project.

## Overview

The `AFC_buffer` module is responsible for handling two types of buffers: [TurtleNeck](https://github.com/ArmoredTurtle/TurtleNeck), [TurtleNeck 2.0](https://github.com/ArmoredTurtle/TurtleNeck2.0) and [Annex Engineering Belay](https://github.com/Annex-Engineering/Belay). The Turtleneck buffer involves two sensors (advance and trailing), while the Belay buffer uses a single sensor to control filament movement.

The buffer adjusts the filament movement based on sensor inputs and can either compress or expand to manage filament feeding properly. Each buffer type has unique configuration options and behaviors.

## Configuration

### Required Configuration Options

In your printer configuration file, ensure you include the following options:

### TurtleNeck Style buffer

- **advance_pin**: Pin for the advance sensor (used in Turtleneck).
- **trailing_pin**: Pin for the trailing sensor (used in Turtleneck).

### Belay Style buffer

- **pin**: Pin for the buffer sensor (used in Belay).
- **distance**: Distance the filament should move when triggered.

### Example Config for Turtleneck 2.0 Buffer

```
[AFC_buffer TN2]
advance_pin: !TN:PB1
trailing_pin: !TN:PB2
multiplier_high: 1.15
multiplier_low: 0.95
```
