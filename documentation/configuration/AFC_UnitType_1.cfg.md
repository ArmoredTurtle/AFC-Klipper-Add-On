# AFC_UnitType_1.cfg Configuration Overview

The `AFC_UnitType_1.cfg` file is used to define the configuration for the AFC system when using a specific unit type.

This file will typically be named in the format of `AFC_Turtle_1.cfg` for example, when a BoxTurtle is installed. If 
multiple unit types are installed, the file will be named in the format of `AFC_Turtle_2.cfg`, `AFC_Turtle_3.cfg`, etc.

!!! note

    The actual naming convention may vary depending on your specific setup. The unit name can be renamed by using the 
    `install-afc.sh` script.

## [mcu mcu_name] Section

This section will define the MCU used for the specific unit.

!!! warning

    Either `canbus_uuid` or `serial` should be defined, not both. Please ensure that you are using the correct
    configuration for your setup. The `canbus_uuid` is used for CAN bus devices, while the `serial` is used for
    USB devices. Whichever option is **NOT** being used should be commented out.

``` cfg
[include mcu/<mcu_name>.cfg]
#    This will be used for any MCU aliases or definition files.
[mcu mcu_name]
canbus_uuid: 1234567890a
#    UUID of the CAN bus device. This is used to identify the device 
#    on the CAN bus.
serial: /dev/serial/by-id/<device-name>
#    Serial address of the device. This is usually in the format of
#    `/dev/serial/by-id/<device-name>` 
```

## [temperature_sensor sensor_name] Section

If your MCU has a temperature sensor built in, you can define it here. 

``` cfg
[temperature_sensor sensor_name]
sensor_type: temperature_mcu
#    Type of temperature sensor. This is usually `temperature_mcu`
sensor_mcu: mcu_name
#    Name of the MCU that the temperature sensor is connected to.
```

## [AFC_stepper <lane_name>] Section

The following options are available in the `[AFC_stepper <lane_name>]` section of the `AFC_UnitType_1.cfg` file. These
options control the configuration of the AFC system when interfacing with the stepper motor for the specific unit type.
You will typically have one of these sections for each lane in the unit.

``` cfg
[AFC_stepper <lane_name>]

unit: MCU:<lane>
#    This is the unit name of the stepper motor. This would typically be 
#    formatted as `MCU:<lane>` where `<lane>` is the lane number. The
#    MCU being being referenced is relative to the `[mcu <mcu_name>]`
#    in this file. For example: `unit: Turtle_1:1` would set this as
#    the first lane for the hardware connected to the `Turtle_1` MCU.
step_pin: mcu:pin
#    Step GPIO pin (triggered high). This parameter must be provided.
dir_pin: mcu:pin
#    Direction GPIO pin (high indicates positive direction). This
#    parameter must be provided.
enable_pin: mcu:pin
#    Enable pin (default is enable high; use ! to indicate enable
#    low). If this parameter is not provided then the stepper motor
#    driver must always be enabled.
microsteps: 16
#    The number of microsteps the stepper motor driver uses. This
#    parameter must be provided.
rotation_distance: 4.65
#    Default: 4.65
#    Distance (in mm) that the axis travels with one full rotation of
#    the stepper motor (or final gear if gear_ratio is specified).
#    This parameter must be provided. With a standard BoxTurtle based
#    on BOM components, this parameter should not need to be adjusted.
gear_ratio:
#    Default: <none>
#    For a standard BoxTurtle, this parameter should not need to be
#    set. This parameter is only used if a different gear set it used.
#    The gear ratio if the stepper motor is connected to the axis via a
#    gearbox. For example, one may specify "5:1" if a 5 to 1 gearbox is
#    in use. If the axis has multiple gearboxes one may specify a comma
#    separated list of gear ratios (for example, "57:11, 2:1"). If a
#    gear_ratio is specified then rotation_distance specifies the
#    distance the axis travels for one full rotation of the final gear.
#    The default is to not use a gear ratio.
dist_hub: 60
#    Default: 60
#    Bowden distance between Box Turtle extruder and hub.
park_dist: 10
#    Default: 10
#    Currently unused.
led_index: AFC_Indicator:1
#    Default: None
#    LED index of lane in chain of lane LEDs. This should reference
#    a defined LED in the `[AFC_Indicator]` section. 
afc_motor_rwd: Turtle_1:MOT1_RWD
#    Reverse pin on MCU for spoolers (N20 motors).
afc_motor_fwd: Turtle_1:MOT1_FWD
#    Forward pin on MCU for spoolers (N20 motors).
afc_motor_enb: Turtle_1:MOT1_EN
#    Enable pin on MCU for spoolers (N20 motors).
rwd_speed_multiplier: 0.5
#    Default: 0.5
#    Multiplier to apply to rpm.
fwd_speed_multiplier: 0.5
#    Default: 0.5
#    Multiplier to apply to rpm.
pwm: True
#    Default: True
#    If True, the n20 motor will be controlled using PWM. 
prep: ^!Turtle_1:TRG1
#    MCU pin for prep trigger. This is the sensor attached to the
#    trigger that is used when filament is loaded.
load: ^!Turtle_1:EXT1
#    MCU pin for load trigger. This is the sensor attached to the
#    extruder body located AFTER the extruder motor.
led_fault: 1,0,0,0
#    Default: 1,0,0,0
#    LED color to set when faults occur in lane.
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here 
#    overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section.
led_ready: 0,0.8,0,0
#    Default: 0,0.8,0,0
#    LED color to set when lane is ready.
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here 
#    overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section.
led_not_ready: 1,0,0,0
#    Default: 1,0,0,0
#    LED color to set when lane is not ready.
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here 
#    overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section.
led_loading:
#    Default: <none>
#    LED color to set when lane is loading.
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here 
#    overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section.
led_unloading: 1,1,1,0
#    Default: 1,1,1,0
#    LED color to set when lane is unloading.
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here 
#    overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section.
led_tool_loaded: 0,0,1,0
#    Default: 0,0,1,0
#    LED color to set when lane is loaded in toolhead.
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here 
#    overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) section.
long_moves_speed: 150
#    Default: 150
#    Speed in mm/s to move filament when doing long moves. 
#    Setting value here overrides values set in 
#    unit(AFC_BoxTurtle/NightOwl/etc) section
long_moves_accel: 250
#    Default: 250
#    Acceleration in mm/s squared when doing long moves. 
#    Setting value here overrides values set in 
#    unit(AFC_BoxTurtle/NightOwl/etc) section
short_moves_speed: 50
#    Default: 50
#    Speed in mm/s to move filament when doing short moves. 
#    Setting value here overrides values set in 
#    unit(AFC_BoxTurtle/NightOwl/etc) section
short_moves_accel: 300
#    Default: 300
#    Acceleration in mm/s squared when doing short moves. 
#    Setting value here overrides values set in 
#    unit(AFC_BoxTurtle/NightOwl/etc) section
short_move_dis: 10
#    Default: 10
#    Move distance in mm for failsafe moves. Setting value 
#    here overrides values set in unit(AFC_BoxTurtle/NightOwl/etc) 
#    section
max_move_dis: 99999
#    Default: 99999
#    Maximum distance to move filament. AFC breaks filament moves over 
#    this number into multiple moves. Useful to lower this number if 
#    running into timer too close errors when doing long filament moves. 
#    Setting value here overrides values set in 
#    unit(AFC_BoxTurtle/NightOwl/etc) section
n20_break_delay_time: 0.200
#    Default: 0.200
#    Time to wait between breaking n20 motors(nSleep/FWD/RWD all 1) 
#    and then releasing the break to allow coasting. Setting value 
#    here overrides values set in unit (AFC_BoxTurtle/NightOwl/etc) section.
load_to_hub: True
#    Default: True
#    Fast loads filament to hub when inserted, set to False to disable. 
#    Setting here overrides global setting in AFC.cfg.
enable_sensors_in_gui: False
#    Default: False
#    Set to True to show prep and load sensors switches as filament sensors 
#    in Mainsail/Fluidd gui, overrides value set in AFC.cfg.
sensor_to_show:
#    Default: <none>
#    Set to prep to only show prep sensor, set to load to only show load 
#    sensor. Do not add if you want both prep and load sensors to show in 
#    web gui.
assisted_unload: False
#    Default: False
#    If True, the unload retract is assisted to prevent loose windings, 
#    especially on full spools. This can prevent loops from slipping off the 
#    spool. Setting value here overrides values set in 
#    unit(AFC_BoxTurtle/NightOwl/etc) section.
print_current: 0.6
#    Default: 0.6
#    Current to use while printing, set to a lower current to reduce stepper 
#    heat when printing. Defaults to global_print_current, if not specified 
#    current is not changed.
filament_diameter: 1.75
#    Default: 1.75
#    Diameter of the filament in mm.
filament_density: 1.24
#    Default: 1.24
#    Density of the filament in g/cm^3.
spool_inner_diameter: 100
#    Default: 100
#    Inner diameter of the spool in mm.
spool_outer_diameter: 200
#    Default: 200 
#    Outer diameter of the spool in mm.
empty_spool_weight: 190
#    Default: 190
#    Weight of the empty spool in grams.
spool_weight: 1000
#    Default: 1000
#    Remaining spool weight in grams.
assist_max_motor_rpm: 500
#    Default: 500
#    Maximum motor RPM for the assist motor (N20).
hub: 
#    Default: <none>
#    Hub name(AFC_hub) that belongs to this stepper, overrides hub 
#    that is set in unit(AFC_BoxTurtle/NightOwl/etc) section.
buffer:
#    Default: <none>
#    Buffer name(AFC_buffer) that belongs to this stepper, overrides 
#    buffer that is set in extruder(AFC_extruder) or 
#    unit(AFC_BoxTurtle/NightOwl/etc) sections.
extruder:
#    Default: <none>
#    Extruder name(AFC_extruder) that belongs to this stepper, 
#    overrides extruder that is set in unit(AFC_BoxTurtle/NightOwl/etc) 
#    section.
```

## [tmc2209 AFC_stepper <lane_name>] Section

The following options are available in the `[tmc2209 AFC_stepper <lane_name>]` section of the `AFC_UnitType_1.cfg` file. These
options control the configuration of the AFC system when interfacing with the TMC2209 stepper motor driver for the specific unit type.

!!! note

    There should be a matching `[tmc2209 AFC_stepper <lane_name>]` section for each `[AFC_stepper <lane_name>]` 
    section in the configuration file.

``` cfg
[tmc2209 AFC_stepper <lane_name>]
uart_pin: mcu:pin
#    Example: Turtle_1:M1_UART
#    The UART pin for the TMC2209 stepper motor driver. 
uart_address: 0
#    Address of the TMC2209 driver on the UART bus.
run_current: 0.8
#    The amount of current (in amps RMS) to configure the driver to use
#    during stepper movement. This parameter must be provided.
sense_resistor: 0.110
#    The resistance (in ohms) of the driver sense resistor. This parameter
#    must be provided. Common values are 0.110 ohms for most TMC2209 drivers
#    and 0.075 ohms for TMC5160 drivers. Check your stepper driver documentation
#    or board schematic to confirm the correct value.
```
!!! warning

    Ensure that the `sense_resistor` is set appropriately. Failure to set this appropriately may result in
    overheating of the stepper motor driver and/or stepper motor. This value is typically set to 0.110 for the TMC2209
    stepper motor driver present on the AFC-Lite board for the BoxTurtle. You *MUST* change this based on your
    board if using another system / configuration.

## [AFC_hub hub_name] Section

The following options are available in the `[AFC_hub hub_name]` section of the `AFC_UnitType_1.cfg` file. These 
options control the configuration of the AFC system when interfacing with the hub for the specific unit type. Multiple
hubs may be defined in the configuration file.

``` cfg
[AFC_hub hub_name]
switch_pin: mcu:pin
#    Default: <none>
#    MCU pin for the hub switch.
hub_clear_move_dis: 25
#    Default: 25
#    How far to move filament so that it doesn't block the hub exit.
afc_bowden_length:  900
#    Default: 900
#    Length of the bowden tube in mm from the hub to the toolhead 
#    sensor.
afc_unload_bowden_length: 900
#    Default: <afc_bowden_length>
#    Length to unload when retracting back from toolhead to hub in 
#    mm. This defaults to the value of `afc_bowden_length` if not
#    specified. With normal installations, this value should not
#    need to be changed or specified explicitly.
assisted_retract: False
#    Default: False
#    If true, retracts are assisted to prevent loose windings on the
#    spool.
move_dis: 50
#    Default: 50
#    Distance to move the filament within the hub in mm.
cut: False
#    Default: False
#    Set to true if using a hub cutter. An example of this would
#    be the `Snappy` hub cutter. 
cut_cmd: AFC
#    Default: AFC
#    Macro command to run when the cut command is sent. This should
#    be set to `AFC` if using the built in functionality. This is 
#    only required when `cut: True` is set.
cut_servo_name: cut
#    Default: cut
#    Name of servo to use for the hub cutter. This is only required
#    when `cut: True` is set. This requires a `[servo cut]` section
#    to be defined in a configuration file.
cut_dist: 50
#    Default: 50
#    How much filament (in mm) to cut when the cut command is sent.
#    This is only required when `cut: True` is set.
cut_clear: 120
#    Default: 120
#    How far the filament should retract (in mm) back from the hub.
#    This is only required when `cut: True` is set.
cut_min_length: 200
#    Default: 200
#    Minimum length of filament (in mm) to cut. This is only
#    required when `cut: True` is set.
cut_servo_pass_angle: 0 
#    Default: 0
#    Servo angle to align the bowden tube with the hole for loading
#    the toolhead. This is only required when `cut: True` is set.
cut_servo_clip_angle: 160
#    Default: 160
#    Servo angle for a completed cut movement. This is only required
#    when `cut: True` is set.
cut_servo_prep_angle: 75
#    Default: 75
#    Servo angle to prepare the filament for cutting. This should be 
#    set so that the bowden tube is NOT aligned with the hub exit. 
#    It should be clear so that filament can be pushed out of the hub
#    and the cutting mechanism can be engaged. This is only required
#    when `cut: True` is set.
cut_confirm: False
#    Default: False
#    If true, the cut command will execute twice. This is only
#    required when `cut: True` is set.
enable_sensors_in_gui: False
#    Default: False
#    Set to True to show hub sensor switch as a filament sensor in 
#    Mainsail/Fluidd gui, overrides value set in AFC.cfg.
```

## [AFC_led led_name] Section

The following options are available in the `[AFC_led led_name]` section of the `AFC_UnitType_1.cfg` file. These
options control the configuration of the AFC system when interfacing with the LED for the specific unit type. Multiple
LEDs may be defined in the configuration file.

``` cfg
[AFC_led AFC_Indicator]
pin: mcu:pin
#    MCU pin definition for LED indicator.
chain_count: 1
#    Number of LEDs in the chain.
color_order: GRB
#    Default: GRB
#    Color order of the LEDs in the chain. This is typically set to
#    a value like `GRB` or `GRBW` depending on the LED type. However,
#    if you are experiencing LED issues, ensure you validate that the 
#    proper color order is set. An incorrect value may result in 
#    sporadic behavior of the LEDs.
```

## [AFC_BoxTurtle unit_name] Section

The following options are available in the `[AFC_BoxTurtle unit_name]` section of the `AFC_UnitType_1.cfg` file. These
options control the configuration of the AFC system when interfacing with the BoxTurtle unit type. This section is
typically used to define the unit name and other options that are specific to the BoxTurtle unit type.

``` cfg
[AFC_BoxTurtle Turtle_1]
type: 'Box Turtle'
#    The type of the unit. This should be set to `Box Turtle` for all
#    BoxTurtle units.
hub:
#    Default: <none>
#    Hub name(AFC_hub) that belongs to this unit. can be overriden in 
#    the [AFC_stepper] section.
extruder:
#    Default: <none>
#    Extruder name(AFC_extruder) that belongs to this unit. can be
#    overriden in the [AFC_stepper] section.
buffer: 
#    Default: <none>
#    Buffer name(AFC_buffer) that belongs to this unit. can be
#    overriden in the [AFC_stepper] section.
led_fault: 1,0,0,0
#    Default: 1,0,0,0
#    LED color to set when faults occur in lane        
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here 
#    overrides values set in AFC.cfg file.
led_ready: 1,1,0,0
#    Default: 1,1,0,0
#    LED color to set when lane is ready
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
led_not_ready: 1,1,0,0
#    Default: 1,1,0,0
#    LED color to set when lane is not ready
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
led_loading: 1,0,0,0
#    Default: 1,0,0,0
#    LED color to set when lane is loading
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
led_unloading: 1,1,.5,0
#    Default: 1,1,.5,0
#    LED color to set when lane is unloading
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
led_tool_loaded: 1,1,0,0
#    Default: 1,1,0,0
#    LED color to set when lane is loaded in toolhead
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
long_moves_speed: 100
#    Default: 100
#    Speed in mm/s to move filament when doing long moves.
#    Setting value here overrides values set in AFC.cfg file.
long_moves_accel: 400
#    Default: 400
#    Acceleration in mm/s squared when doing long moves.
#    Setting value here overrides values set in AFC.cfg file.
short_moves_speed: 25
#    Default: 25
#    Speed in mm/s to move filament when doing short moves.
#    Setting value here overrides values set in AFC.cfg file.
short_moves_accel: 400
#    Default: 400
#    Acceleration in mm/s squared when doing short moves.
#    Setting value here overrides values set in AFC.cfg file.
short_move_dis: 400
#    Default: 400
#    Move distance in mm for failsafe moves. Setting value
#    here overrides values set in AFC.cfg file.
max_move_dis: 99999
#    Default: 99999
#    Maximum distance to move filament. AFC breaks filament moves over
#    this number into multiple moves. Useful to lower this number if
#    running into timer too close errors when doing long filament moves.
#    Setting value here overrides values set in AFC.cfg file.
n20_break_delay_time: 0.200
#    Default: 0.200
#    Time to wait between breaking n20 motors(nSleep/FWD/RWD all 1)
#    and then releasing the break to allow coasting. Setting value
#    here overrides values set in AFC.cfg file.
assisted_unload: False
#    Default: False
#    If True, the unload retract is assisted to prevent loose windings,
#    especially on full spools. This can prevent loops from slipping off the
#    spool. Setting value here overrides values set in AFC.cfg file.
unload_on_runout: False
#    Default: False
#    When True, AFC will unload lane and then pause when runout is 
#    triggered and spool to swap is not set (infinite spool). Setting
#    value here overrides values set in AFC.cfg file.
```

## [AFC_NightOwl unit_name] Section

The following options are available in the `[AFC_NightOwl unit_name]` section of the `AFC_UnitType_1.cfg` file. These
options control the configuration of the AFC system when interfacing with the NightOwl unit type. This section is
typically used to define the unit name and other options that are specific to the NightOwl unit type.

``` cfg
[AFC_NightOwl NightOwl_1]
type: 'NightOwl'
#    The type of the unit. This should be set to `NightOwl` for all
#    NightOwl units.
hub:
#    Default: <none>
#    Hub name(AFC_hub) that belongs to this unit. can be overriden in 
#    the [AFC_stepper] section.
extruder:
#    Default: <none>
#    Extruder name(AFC_extruder) that belongs to this unit. can be
#    overriden in the [AFC_stepper] section.
buffer: 
#    Default: <none>
#    Buffer name(AFC_buffer) that belongs to this unit. can be
#    overriden in the [AFC_stepper] section.
led_fault: 1,0,0,0
#    Default: 1,0,0,0
#    LED color to set when faults occur in lane        
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here 
#    overrides values set in AFC.cfg file.
led_ready: 1,1,0,0
#    Default: 1,1,0,0
#    LED color to set when lane is ready
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
led_not_ready: 1,1,0,0
#    Default: 1,1,0,0
#    LED color to set when lane is not ready
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
led_loading: 1,0,0,0
#    Default: 1,0,0,0
#    LED color to set when lane is loading
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
led_unloading: 1,1,.5,0
#    Default: 1,1,.5,0
#    LED color to set when lane is unloading
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
led_tool_loaded: 1,1,0,0
#    Default: 1,1,0,0
#    LED color to set when lane is loaded in toolhead
#    (R,G,B,W) 0 = off, 1 = full brightness. Setting value here
#    overrides values set in AFC.cfg file.
long_moves_speed: 100
#    Default: 100
#    Speed in mm/s to move filament when doing long moves.
#    Setting value here overrides values set in AFC.cfg file.
long_moves_accel: 400
#    Default: 400
#    Acceleration in mm/s squared when doing long moves.
#    Setting value here overrides values set in AFC.cfg file.
short_moves_speed: 25
#    Default: 25
#    Speed in mm/s to move filament when doing short moves.
#    Setting value here overrides values set in AFC.cfg file.
short_moves_accel: 400
#    Default: 400
#    Acceleration in mm/s squared when doing short moves.
#    Setting value here overrides values set in AFC.cfg file.
short_move_dis: 400
#    Default: 400
#    Move distance in mm for failsafe moves. Setting value
#    here overrides values set in AFC.cfg file.
assisted_unload: False
#    Default: False
#    If True, the unload retract is assisted to prevent loose windings,
#    especially on full spools. This can prevent loops from slipping off the
#    spool. Setting value here overrides values set in AFC.cfg file.
unload_on_runout: False
#    Default: False
#    When True, AFC will unload lane and then pause when runout is 
#    triggered and spool to swap is not set (infinite spool). Setting
#    value here overrides values set in AFC.cfg file.
```