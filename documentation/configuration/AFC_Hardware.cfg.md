---
Title: AFC_Hardware.cfg Configuration Overview
---

# [AFC_Hardware.cfg] Configuration Overview

The `AFC_Hardware.cfg` file is used to typically define options such as the AFC extruder configuration, filament 
switch bypass sensors, and buffer configurations.

This file is typically located in the `~/printer_data/config/AFC` directory and is created during the installation 
of the AFC-Klipper-Add-On.

## [AFC_extruder extruder] Section

The following options are available in the `[AFC_extruder extruder]` section of the `AFC.cfg` file. These options 
control the configuration of the AFC system when interfacing with the extruder / toolhead.

!!! note

    These options will most likely require the most amount of configuration and tuning.

``` cfg
[AFC_extruder extruder]
pin_tool_start: mcu:pin
#    MCU defined pin for filament sensor located before (pre) the
#    extruder gears. This is used to detect the presence of filament
#    before the extruder gears. 
pin_tool_end: mcu:pin
#    MCU defined pin for filament sensor located after (post) the
#    extruder gears. This is used to detect the presence of filament
#    after the extruder gears.
tool_stn: 72                    
#    Distance in mm from the toolhead sensor (pin_tool_start)to the 
#    tip of the nozzle in mm, if `pin_tool_end` is defined then 
#    distance is from this sensor 
tool_stn_unload: 100            
#    Distance to move in mm while unloading toolhead
tool_sensor_after_extruder: 0   
#    Extra distance to move in mm once pre/post sensors are clear. 
#    Useful for when only using post sensor, so this distance can 
#    be the amout to move to clear extruder gears.
tool_unload_speed: 25           
#    Unload speed in mm/s when unloading toolhead. Default is 25mm/s.
tool_load_speed: 25             
#    Load speed in mm/s when unloading toolhead. Default is 25mm/s.
buffer: <buffer_name>
#    Buffer to use for extruder, this variable can be overridden 
#    per lane.
enable_sensors_in_gui: False
#    Set to True toolhead sensors switches as filament sensors in 
#    Mainsail/Fluidd gui, overrides value set in AFC.cfg.
``` 

## [AFC_buffer buffer_name] Section
The following options are available in the `[AFC_buffer buffer_name]` section of the `AFC.cfg` file. These options
control the configuration of the AFC system when interfacing with the filament buffer.

``` cfg
[AFC_buffer buffer_name]
advance_pin: mcu:pin
#    MCU defined pin for advance sensor.
trailing_pin: mcu:pin
#    MCU defined pin for trailing sensor.
multiplier_high: 1.05
#    Factor to move more filament through the secondary extruder.
multiplier_low: 0.95
#    Factor to move less filament through the secondary extruder.
led_index: Buffer_Indicator:1
#    LED index for the buffer, used to control the buffer LED
#    (if present).
velocity: 0
#    Velocity for the forward assist.
accel: 0
#    Error if the buffer is not configured properly.
```

## [AFC_led Buffer_Indicator] Section

The following options are available in the `[AFC_led Buffer_Indicator]` section of the `AFC.cfg` file. These options
control the configuration of the AFC system when interfacing with the buffer LED.

``` cfg
[AFC_led Buffer_Indicator]
pin: mcu:pin 
#    MCU defined pin for the LED.
chain_count: 1
#    Number of LEDs in the chain.
color_order: GRBW
#    Color order of the LED chain.
intial_RED: 0.0
#    Initial RED value of the LED.
intial_GREEN: 0.0
#    Initial GREEN value of the LED.
intial_BLUE: 0.0
#    Initial BLUE value of the LED.
intial_WHITE: 0.0
#    Initial WHITE value of the LED.
```