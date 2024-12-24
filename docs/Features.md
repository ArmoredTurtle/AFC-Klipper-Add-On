# Overview of features 

This file goes over the features that can be found in Armored Turtle Automated Filament Changer (AFC) Software

## TurtleNeck Buffer Ram Sensor
AFC allows the use of using the TurtleNeck Buffers as a ram sensor for detecting when filament is loaded to the toolhead extruder. This can be used inplace of a toolhead filament sensor. To learn more about this feature please see [Buffer Ram Sensor](Buffer_Ram_Sensor.md) document

## Bypass
You can enable AFC bypass by printing out [bypass](https://github.com/ArmoredTurtle/AFC-Accessories/tree/main/AFC_Bypass) accessory, connecting inline after your buffer and adding a bypass filament sensor to klipper config like below. Once filament is inserted into the bypass side, the switch disables AFC functionality so you can print like normal.

```
[filament_switch_sensor bypass]
switch_pin: <replace with MCU pin that switch is connected to>
pause_on_runout: False
```

## Lower stepper current when printing
For longer prints you may want to have the ability to lower BoxTurtles steppers current as they can get hot when engaged for a long period of time.

Enabling lower current during printing can be enabled two ways:
1. Set `global_print_current` in AFC.cfg file
2. Set `print_current` for each AFC_stepper, this will override `global_print_current` in AFC.cfg

During testing it was found that 0.6A worked well during printing and kept the steppers warms to the touch. Would not suggest going lower than this or the TurtleNeck buffers may not work as intended.