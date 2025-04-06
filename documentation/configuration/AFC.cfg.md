---
Title: AFC.cfg Configuration Overview
---

# [AFC.cfg] Configuration Overview

The `AFC.cfg` file is the main configuration file for the AFC-Klipper-Add-On. It contains the primary settings and 
options that control the overall behavior of the AFC system. This file is typically located in the `~/printer_data/config/AFC` 
directory and is created during the installation of the AFC-Klipper-Add-On.

## [AFC] Section

The following options are available in the `[AFC]` section of the `AFC.cfg` file. These options control various aspects 
of the AFC system, including speed settings, LED configurations, and macro settings.

!!! warning

    The `AFC.cfg` file is a critical component of the AFC-Klipper-Add-On. 
    Modifying this file incorrectly can lead to unexpected behavior or 
    malfunctions in the AFC system. Always make a backup of your configuration 
    files before making any changes.

``` cfg
[AFC]
VarFile: ../printer_data/config/AFC/AFC.var
#    Defines the location of the AFC.var file. This file is used to store 
#    variables and settings for the AFC system. 
long_moves_speed: 150      
#    Default: 150     
#    Speed in mm/s. This is the speed used for long moves, such as when 
#    loading or unloading filament.
long_moves_accel: 250
#    Default: 250           
#    Speed in mm/s². This is the acceleration used for long moves.
short_moves_speed: 50
#    Default: 50           
#    Speed in mm/s. This is the speed used for short moves, such as 
#    when moving the final distance to the toolhead or during calibration.
short_moves_accel: 300
#    Default: 300          
#    Speed in mm/s². This is the acceleration used for short moves.
short_move_dis: 10
#    Default: 10              
#    Move distance for failsafe moves.
global_print_current: 0.6
#    Default: 0.6
#    Uncomment to set stepper motors to a lower current while printing.
#    This value can also be set per stepper with print_current: 0.6
enable_sensors_in_gui: True
#    Default: False     
#    Boolean to show all sensor switches as filament sensors in 
#    the Mainsail/Fluidd gui.
default_material_temps: default: 235, PLA:210, ABS:235, ASA:235 
#    Default temperature to set extruder when loading/unloading lanes.
#    Material needs to be either manually set or uses material from spoolman 
#    if extruder temp is not set in spoolman. Follow current format to 
#    add more filament types.
default_material_type: PLA      
#    Default material type to assign to a spool once loaded into a lane.
load_to_hub: True
#    Default: True            
#    Fast loads filament to hub when inserted, set to False to disable. This 
#    is a global setting and can be overridden at AFC_stepper for individual 
#    lanes if needed.
moonraker_port: 7125
#    Default: <none>     
#    Port to connect to when interacting with moonraker. Used when there are 
#    multiple moonraker/klipper instances on a single host.
assisted_unload: True
#    Default: <none> 
#    If True, the unload retract is assisted to prevent loose windings, 
#    especially on full spools. This can prevent loops from slipping off the 
#    spool. This is a global setting and can be overridden at the unit and 
#    stepper level.
pause_when_bypass_active: True
#    Default: False
#    When True AFC pauses print when change tool is called and bypass is loaded
unload_on_runout: True
#    Default: False   
#    When True AFC will unload lane and then pause when runout is triggered and 
#    spool to swap to is not set(infinite spool)
debug: False
#    Default: False                    
#    Setting to True turns on more debugging to show on console.
trsync_update: False            
#    Default: False
#    When set to true, Klipper's trsync value will be automatically set to the
#    value in trsync_timeout. This can be useful if you are experiencing TTC
#    issues.
trsync_timeout: 0.05          
#    Default: 0.05
#    Value to set trsync to when trsync_update is set to true.
trsync_single_timeout: 0.250
#    Default: 0.250  
#    Value to set single_timeout to when it needs to be greater than the 
#    default of 0.250
z_hop: 5
#    Default: 0                
#    Height to move up before and after a tool change completes
resume_speed: 120               
#    Speed mm/s of resume move. Set to 0 to use gcode speed
resume_z_speed: 30              
#    Speed mm/s of resume move in Z. Set to 0 to use gcode speed
led_name: AFC_Indicator         
#    LED name from the [AFC_led] section in AFC_Hardware.cfg.
#    All LEDs use the (R,G,B,W) format. R = Red, G = Green, B = Blue, W = White.
#    0 = off, 1 = full brightness. 
led_fault: 1,0,0,0              
#    Fault color
led_ready: 0,0.8,0,0            
#    Ready color
led_not_ready: 1,0,0,0          
#    Not ready color
led_loading: 1,1,1,0            
#    Loading color
led_tool_loaded: 0,0,1,0        
#    Loaded color
led_buffer_advancing: 0,0,1,0   
#    Buffer advancing color
led_buffer_trailing: 0,1,0,0    
#    Buffer trailing color
led_buffer_disable: 0,0,0,0.25  
#    Buffer disable color
n20_break_delay_time: 0.200
#    Default: 0.200
#    Time to wait between breaking n20 motors(nSleep/FWD/RWD all 1) and then 
#    releasing the break to allow coasting.
tool_max_unload_attempts: 2
#    Default: 2
#    Max number of attempts to unload filament from toolhead when using 
#    buffer as ramming sensor.
tool_max_load_checks: 4
#    Default: 4
#    Max number of attempts to check to make sure filament is loaded into 
#    toolhead extruder when using buffer as ramming sensor.
resume_speed: 25
#    Default: 25
#    Speed in mm/s of the resume move. Set to 0 to use gcode speed.
resume_z_speed: 25
#    Default: 25
#    Speed in mm/s of the resume move in Z. Set to 0 to use gcode speed.
pause_when_bypass_active: False
#    Default: False
#    When true AFC pauses print when change tool is called and bypass is loaded
unload_on_runout: False
#    Default: False
#    When True AFC will unload lane and then pause when runout is triggered 
#    and spool to swap to is not set(infinite spool).

```

The next part of the `[AFC]` section contains the configuration for the AFC macros. These macros are used to control the
operation of the AFC system, including loading and unloading filament, cutting, and waste management.

``` cfg
# Macro order of operation
# - Load               |   - Unload
#   - Load Filament    |    - Cut
#   - Poop             |    - Park
#   - Wipe             |    or
#   - Kick             |    - Park
#   - Wipe             |    - Tip Form
#   - Print            |

# TOOL Cutting Settings
tool_cut: True                  
#    Boolean, when set to true a toolhead cutter will be utilized.
tool_cut_cmd: AFC_CUT
#    Default: AFC_CUT           
#    Macro name to call when cutting filament. Using the default AFC_CUT macro
#    will call the macro defined in `Cut.cfg`. You can replace this with a 
#    custom macro name if you have a different cutting method or tool.

# Park Settings
park: True                      
#    Boolean, when set to true, the the park functionality will be enabled.
park_cmd: AFC_PARK              
#    Default: AFC_PARK
#    Macro name to call when parking the toolhead. Using the default AFC_PARK
#    macro will call the macro defined in `Park.cfg`. You can replace this with
#    a custom macro name if you have a different parking method or tool.

# Poop Settings
poop: True                      
#    Boolean, when set to true, the system will use the `poop` method for 
#    purging filament after a color change.
poop_cmd: AFC_POOP              
#    Default: AFC_POOP
#    Macro name to call when pooping filament. Using the default AFC_POOP macro
#    will call the macro defined in `Poop.cfg`. You can replace this with a 
#    custom macro name if you have a different pooping method or tool.

# Kick Settings
kick: True                      
#    Boolean, when set to true, the system will use enable the `kick` 
#    functionality to clear purged filament from the bed.
kick_cmd: AFC_KICK              
#    Default: AFC_Kick
#    Macro name to call when wiping filament. Using the default AFC_KICK macro
#    will call the macro defined in `Brush.cfg`. You can replace this with a 
#    custom macro name if you have a different wiping method or tool.

# Wipe Settings
wipe: True                      
#    Boolean, when set to true, the system will use a wiper to help clean the 
#    toolhead.
wipe_cmd: AFC_BRUSH
#    Default: AFC_BRUSH
#    Macro name to call when wiping filament. Using the default AFC_BRUSH macro
#    will call the macro defined in `Brush.cfg`. You can replace this with a 
#    custom macro name if you have a different wiping method or tool.

# Form Tip Settings
form_tip: False                 
#    Boolean, when set to true, the system will use a form tip macro to help 
#    shape the filament tip for better loading / unloading.
form_tip_cmd: AFC               
#    Default: AFC
#    Macro name to call when using tip-forming. Using the default AFC macro will
#    call the built-in macro. You can replace this with a custom macro name if 
#    you have a different tip-forming method or tool. Configuration for the AFC 
#    macro is defined in the `AFC.cfg` file.
```

## [AFC_prep] Section

``` cfg
[AFC_prep]
enable: True                    
#    Boolean, setting this true will run a test sequence when Klipper starts 
#    or when the Klipper firmware is reloaded. 
delay_time: 0.1
#    Default: 0.1, minval=0.0
#    Time to delay when moving extruders and spoolers during the PREP routine.
disable_unload_filament_remapping: False
#    Default: False
#    Set to true to disable remapping UNLOAD_FILAMENT macro to TOOL_UNLOAD 
#    macro.
```

## [delayed_gcode welcome] Section

!!! warning

    This section is used to define a delayed G-code macro that runs when the AFC system is
    initialized. It typically should not be modified unless you are familiar with the
    AFC-Klipper-Add-On and its operation.

``` cfg
[delayed_gcode welcome]
initial_duration: 0.5
#    Duration in seconds to wait before executing the gcode macro defined below.
gcode:
 PREP
#    The macro name to call when the [AFC_prep] section is enabled. This macro 
#    is used to run a test sequence when Klipper starts or when the Klipper 
#    firmware is reloaded.
```

## [AFC_form_tip] Section

The `[AFC_form_tip]` section contains the configuration options for the tip-forming process. This process is used to shape
the filament tip for better loading and unloading. The options in this section control the speed, distance, and other parameters
of the tip-forming process.

``` cfg
[AFC_form_tip]
# This is the initial press of the filament into the tip before any cooling 
# moves.
ramming_volume: 0               
#    Volume of filament to press into the nozzle during tip formation in mm³.
toolchange_temp: 0
# Set this if you would like a temperature reduction during the tip formation.
# If using skinny_dip, this change will happen before.
# This step is split into two different movements. First, a fast move to 
# separate the filament from the hot zone. Next, a slower movement over 
# the remaining distance of the cooling tube.
unloading_speed_start: 40       
#    Speed in mm/s (fast pull).
unloading_speed: 15             
#    Speed in mm/s (cooling tube move).
# This stage moves the filament back and forth in the cooling tube section 
# of the hotend.It helps keep the tip shape uniform with the filament path 
# to prevent clogs.
cooling_tube_position: 35       
#    Start of the cooling tube in mm.
cooling_tube_length: 10         
#    Length of the move in mm.
initial_cooling_speed: 10       
#    Initial movement speed to start solidifying the tip in mm/s.
final_cooling_speed: 50         
#    Fast movement speed in mm/s.
cooling_moves: 4               
#    Number of back and forth moves in the cooling tube.
# This is a final move to burn off any hairs possibly on the end of 
# stringy materials like PLA. If you use this, it should be the last 
# thing you tune after achieving a solid tip shape.
use_skinnydip: False            
#    Enable skinny dip moves (for burning off filament hairs).
skinnydip_distance: 30          
#    Distance to reinsert the filament, starting at the end of the 
#    cooling tube in mm.
dip_insertion_speed: 30         
#    Insertion speed for burning off filament hairs in mm/s.
dip_extraction_speed: 70        
#    Extraction speed (set to around 2x the insertion speed) in mm/s.
melt_zone_pause: 0              
#    Pause time in the melt zone in seconds.
cooling_zone_pause: 0           
#    Pause time in the cooling zone after the dip in seconds.
```