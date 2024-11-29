# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2024-08-28]

### Added

- Addition of two helper macros for the AFC system. 
  - `BT_LANE_EJECT` - This macro will eject a specified box turtle lane.
  - `BT_TOOL_UNLOAD` - This macro will unload a specified box turtle tool.

- Sample configuration files for the most popular boards are located in the `Klipper_cfg_example/AFC` directory.

## [2024-10-24]

### Added

 - Added `loaded_to_hub` parameter to get_status so users can see if filament is loaded to  their hub
 - Added `SET_BOWDEN_LENGTH LENGTH={}` to change `afc_bowden_length`
      - Length can be changed in 3 ways:
          - An exact value can be set. `SET_BOWDEN_LENGTH LENGTH=955` will set the Bowden length to 955mm
          - Current value can be incremented positive or negative.
             - `SET_BOWDEN_LENGTH LENGTH=+100` if the original length was `955` it will be changed to `1055`
             - `SET_BOWDEN_LENGTH LENGTH=-100` if the original length was `955` it will be changed to `855`
       - `SET_BOWDEN_LENGTH` is called without a `LENGTH` specified then the value will be reset back to the configured length
       - Changed distance will have to be manually updated in `AFC.cfg`  

  - Added `Buffer_Name` to `AFC.cfg`
    - this allows the code base to have a name for the buffer to reference.
    - The name must match how buffer is defined in `[AFC_buffer *Buffer_Name*]`
    - ^^^This has to be manually updated and must be uncommented/added to AFC.cfg file^^^
  -  Additions to `AFC.py`
    - establish Buffer name
    - With buffer set up
      - Enable during `PREP`
      - Enable during `tool_load`
      - Disable during `tool_unload`
  - Added `SET_ROTATION_FACTOR` that uses variable `FACTOR`
    - if a turtleneck style buffer is enabled it will change the current rotation distance of the AFC stepper,
    - Values greater than 0
    - Values greater than 1 will cause more filament to be fed
    - Values Less than 1 greater than 0 will cause less filament to be fed
    
### Changed

 - Revamped `install-afc.sh` script to be interactive and provide more configuration options for the user.
 - Updated `ruff` GHA to only scan for changed files.
 - Updates to AFC.cfg file. Be sure to back up current file and replace with new version, then update values from backed up file.
 - Manually changes needed to AFC_hardware.cfg
    - `[filament_switch_sensor tool]` update to `[filament_switch_sensor tool_start]`
    - If using sensor after gears `[filament_switch_sensor extruder]` update to `[filament_switch_sensor tool_end]`

  - Full functionality change for Turtleneck/ Turtleneck 2.0 style buffers
  - Changed buffer configuration examples, new configuration is required for full functionality!
    - `multiplier_high` controls the speed-up of filament being fed
    - `multiplier_low` controls the slow-down of filament being fed
  - `QUERY_BUFFER` will output rotation distance if applicable

### Fixed

  - Minor adjustments to the use of single sensor buffers, retaining functionality for Belay

## [2024-10-27]

### Added

- Updated the `install-afc.sh` script to include setup of the buffer configuration.
- Added `part_cooling_fan_speed` to poop macro
- Add `variable_part_cooling_fan_speed   : 1.0         # Speed to run fan when enabled above. 0 - 1.0` to your `_AFC_POOP_VARS` to change the value.

### Changed

- Broke the `install-afc.sh` script out into multiple files that are sourced by the main script for maintainability.

### Fixed
  - Fixed bug when `part_cooling_fan` was set to False

## [2024-10-31]

### Added

- Added LED buffer_indicator
  - allows for state change indication through color change
- Added AFC_buffer.md to layout the integration of a buffer into the AFC system

### Changed

- Changed buffer code to reflect buffer functionality and pin names
- Moved stepper commands from AFC_buffer to AFC_stepper
- Abstracted buffer status to be used in IP query and query buffer

## [2024-11-03]

### Added

- Manually add the following section to your `AFC.cfg`
```
#--=================================================================================--#
######### Pause/Resume ################################################################
#--=================================================================================--#
xy_resume: False               # Enable to have position return to previous x,y coords after tool change
resume_speed: 0                # Speed of resume move. Leave 0 to use current printer speed
resume_z_speed: 0              # Speed of resume move in Z. Leave 0 to use current printer speed
```
- Manually add the following to your `AFC_macros.cfg`
```
[gcode_macro BT_RESUME]
description: Resume the print after an error
gcode:
    {% if not printer.pause_resume.is_paused %}
        RESPOND MSG="Print is not paused. Resume ignored"
    {% else %}
        AFC_RESUME
    {% endif %}
```
- If you encounter an error use the *BT_RESUME* macro to resume to the proper z height after the error is fixed.

### Changed

- Save/Restore position to use proper gcode location
- It will restore the z position first before making an x,y move

## [2024-11-16]

### Added
- New variable `cut_servo_name` for AFC_hub configuration to specify which servo to use
- AFC_STATUS macro call, will print out what the current status is for each lane
  
  ex. 
  ```
  Turtle_1 Status
  LANE | Prep | Load | Hub | Tool |
  LEG1 |  xx  |  xx  |  x  |  xx  |
  LEG2 |  xx  |  xx  |  x  |  xx  |
  LEG3 |  xx  |  xx  |  x  |  xx  |
  LEG4 |  xx  |  xx  |  x  |  xx  |
  
  Turtle_2 Status
  LANE | Prep | Load | Hub | Tool |
  LEG5 |  xx  |  xx  |  x  |  xx  |
  LEG6 |  xx  |  xx  |  x  |  xx  |
  LEG7 |  xx  |  xx  |  x  |  xx  |
  LEG8 | <--> | <--> | <-> | <--> |
  ```

### Fixed
- Fixed hub_cut function to work with new structure
- Added sleeps back to hub_cut with reactor class

## [2024-11-22]

### Changed

*Full update, this needs more details*

## [2024-11-23]

### Added
- New buffer function `SET_BUFFER_MULTIPLIER` used to live adjust the high and low multipliers for the buffer
    - To change `multiplier_high`: `SET_BUFFER_MULTIPLIER MULTIPLIER=HIGH FACTOR=1.2`
    - To change `multiplier_low`: `SET_BUFFER_MULTIPLIER MULTIPLIER=HIGH FACTOR=0.8`
    - `MULTIPLIER` and `FACTOR` must be defined
    - Buffer config section must be updated for values to be saved

### Fixed
-Corrected buffer to only trigger when tube comes onto switch/sensor and not off

## [2024-11-25]

### Changed
- Simplified buffer status to Trailing and Advancing
  - Buffer tube moving from Trailing to Advance it is in the Advancing state
  - Buffer tube moving from Advance to Trialing it is in the Trialing state

## [2024-11-27]

### Added

- `generate_docs.py` utility in the `utilities` folder to auto-generate some basic documentation in the `docs/command_reference.md` file.

## [2024-11-27]]

### Fixed
- Klipper erroring out when renaming `RESUME` macro when a user call's `BT_PREP` within the same reboot of klipper

## [2024-11-27]

### Added
- `self.delay` to AFC_Prep to control delay time during Prep
  - Config option under `[AFC Prep]`, `delay_time: 1  # default .1`
  - This can be increased if TTC occurs during prep caused by H-bridge command queue

### Changed
- Simplified enabling and disabling of the buffer
- `AFC_extruder.py` now holds the functions and controls of the buffer
  - These common functions all called throughout

### Fixed
- Fixed erroring out if a buffer in not configured
