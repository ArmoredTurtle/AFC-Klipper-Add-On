# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2025-02-04]

### Changed
- Changed default `hub_clear_move_dis` to 25 to avoid too much retraction during filament changes

### Fixed
- Fixed error out during calibration when not calibrating bowden length
- Fixed issue where AFC could crash klipper in some scenarios when tool unloads fail to clear hub


## [2025-02-03]

### Changed
- Added expanded and compressed to buffer query for easier troubleshooting

### Fixed
- Corrected readme to point to the correct files
- Added check for key on bowden length calibration to not crash klipper if the wrong value is provided

## [2025-01-28]

### Changed
- Added `velocity` default setting back into buffer configuration when using the `install-afc.sh` script. This value was previously set to `0` by default,
but the configuration did not display this value. For future installations, this value will be explicitly set in the buffer configuration.

### Fixed
- Added minor documentation changes regarding `velocity` changes in the buffer configuration.

## [2025-01-26]
### Added
- Added ability to specify moonraker port, needed for when user has multiple moonraker/klipper instances on a single machine

### Fixed
- Fixed issue where software was updated to no long detected movement outside of printing, this fixes crashing klipper when inserting filament while printer is moving
- Fixed issue where remaining weight was not being pulled correctly from spoolman

## [2025-01-23]
### Fixed
- Fixed not being able to unload filament with UNLOAD_FILAMENT macro when using bypass

## [2025-01-17]
### Added
- Added ability to break up long bowden moves into shorter moves with `max_move_dis` variable to help with users that are facing timer too close issues when doing long moves. This variable can be set in `AFC.cfg` as a global setting or in the stepper/config sections.

### Changed
- Function `isPrinting` is determined by `print_stats` instead of `idle_timeout`
- Check extruder temp function only sets temperature if hotend can't extrude(temp below min value) and if printer is not printing, so that hotend temperature is not changed while printing

## [2025-01-12]
### Added

- Added Guided calibration using `AFC_CALIBRATION`
  - With the call of `AFC_CALIBRATION` the user will be guided through calibrating the lanes in their AFC unit.
- Added `UNIT` as an option to the `CALIBRATE_AFC` macro that is leveraged to calibrate lanes in a specific unit.

## [2025-01-12]
### Added
- Remapping stock `UNLOAD_FILAMENT` to call `TOOL_UNLOAD` function. Stock `UNLOAD_FILAMENT` will be renamed to `_AFC_RENAMED_UNLOAD_FILAMENT_` and can still be called from the command line. If trying to do a `TOOL_UNLOAD` and filament is loaded into bypass, AFC will unload with `_AFC_RENAMED_UNLOAD_FILAMENT_` macro. Remapping `UNLOAD_FILAMENT` macro can be disabled by setting `disable_unload_filament_remapping: True` in AFC_prep config section. 
- Added `docs/CONFIGURATION_OPTIONS.md` file that describes the different config parameters, still a work in progress

### Changed
- AFC-Klipper-Add-On now pulls spoolman ip/port from moonracker.conf file, please remove `spoolman_ip` and `spoolman_port` from `AFC/AFC.cfg` file


## [2025-01-11]
### Added
- Added clearing spool info and `load_to_hub` when lane retracts too far past Box Turtle extruder, reset once prep goes low
- Added logic so that buffer/extruder/hubs don't need to be entered per stepper as long as they are defined in their Unit(AFC_BoxTurtle/AFC_NightOwl) section 

For the following please see [Features doc](docs/Features.md) for more information on how to setup
- Added ability to set and track number of toolchanges when doing multicolor prints
- Added ability to set extruder temperature based off spoolman values or filament materials type if manually entered
- Added ability to show sensors as filament sensors in gui's
- Added ability to use multiple buffers
- Added automatically loading filament to hub for users that have moved their hubs closer to their toolhead

## [2025-01-10]

### Changed
- Due to a too long retraction, hub cuts had the risk of ejecting filament from the extruder,
  requiring manual intervention. The hub cut sequence was changed to avoid this situation.

  **NOTE**: due to the new way hub cuts are performed, the configuration has to be updated!
        The value `cut_dist` in `[AFC_Hub]` has to be reduced by about 150. Please recalibrate
        this before the next print.

### Added
- [AFC_Hub] has a new config option: `assisted_retract`. If set to true, retracts are assisted so
  that filament can't get loose on the spool.

### Changed

- `http://<ip_address>/printer/objects/query?AFC` has moved to `http://<ip_address>/printer/afc/status`endpoint. If tools have been designed around original endpoint please review results returned as new items have been added

## [2025-01-08]
### Added
- If using `tool_end` variable(sensor after extruder gears) `tool_stn` distance will now be based off this sensor
- When running `CALIBRATE_AFC` command values will be automatically updated and saved to config file

### Fixed
- Fixed infinite spool logic

## [2025-01-05]

### Updated
- This update will require the re-installation of an user's configuration  files due to changes in the config file structure.
- Re-designed the `install-afc.sh` script to be more user-friendly, interactive, and more indicative of what is happening 
during the installation process.

## [2024-12-29]

### Added
- **New Command: `GET_TIP_FORMING`**
  Shows the current tip forming configuration. Mostly interesting together with
  SET_TIP_FORMING.

- **New Command: `SET_TIP_FORMING`**
  Allows to update tip forming configuration at runtime.

  See command_reference doc for more info

## [2024-12-23]
### Added
- Added ability to set lower stepper current when printing to help reduce how hot steppers can get.
  To enable this feature set `global_print_current` in AFC.cfg or `print_current` for each AFC_stepper
  During testing it was found that 0.6 was optimal, going lower than this may result in buffer not working as intended

- Added check to make sure printer is not printing or homing when trying to load a spool. Doing so before would
  result in klipper crashing.

## [2024-12-22]

### Added
- **New Command: `SET_BUFFER_VELOCITY`**
    Allows users to tweak buffer velocity setting while printing. This setting is not
    saved in configuration.

    See command_reference doc for more info

- **New Command: `TEST_AFC_TIP_FORMING`**
    Gives ability to test AFC tip forming without doing a tool change

- **New Command: `RESET_AFC_MAPPING`**
    Resets all tool lane mapping to the order that is setup in configuration

### Fixed
- Fixed error in tip forming when `toolchange_temp` value is not zero

## [2024-12-20]

### Added
- More error printouts to aid users

### Fixes
- Misc error fixes

## [2024-12-13]

### Updated
- Updated Cut.cfg macro to have the ability to up stepper current when doing filament cutting, 
  see layer shift troubleshooting section on what values need to be set

## [2024-12-09]

### Added
- **New Command: `CALIBRATE_AFC`**  
    Allows calibration of the hub position and Bowden length in the Automated Filament Changer (AFC) system.  
    Supports calibration for a specific lane or all lanes (`LANE` parameter).  
    Provides options for distance and tolerance during calibration:
    - `DISTANCE=<distance>`: Optional distance parameter for lane movement during calibration (default is 25mm).
    - `TOLERANCE=<tolerance>`: Optional tolerance for fine-tuning adjustments during calibration (default is 5mm).  
    - Bowden Calibration: Added functionality to calibrate Bowden length for individual lanes using the `BOWDEN` parameter.

## [2024-12-08]

### Added
- When updating the AFC software, the `install-afc.sh` script will now remove any instances of `[gcode_macro T#]` found in the `AFC_Macros.cfg`
file as the code now generates them automatically.
- Added logic to pause print when filament goes past prep sensor. Verify that PAUSE macro move's toolhead off print when it's called.

## [2024-12-07]

### Updated
- When BT_TOOL_UNLOAD is used, spoolman active spool is set to None
- When spool is ejected from Box Turtle spoolman spool is removed from variables
- Activated espooler when user calls LANE_MOVE

### Fixed
- Fixed places where gcode was not referencing AFC and would cause crashes

## [2024-12-04]

### Fixed
- Fixed issue with Turtleneck buffer pins not being assigned correctly when prompted during install
- Fixed issue with LEDs not showing the right color when error happened during PREP
- Changed error message when AFC.vars.unit lane showed loaded but AFC.vars.tool file didn't match
- Added logic so that user could change trsync value. To set value add the following into `[AFC]` section in AFC.cfg file:  
`trsync_update: True`  
Optional:  
`trsync_timeout: 0.05`  
`TRSYNC_SINGLE_MCU_TIMEOUT: 0.5` 

## [2024-12-03]

### Added

- The `install-afc.sh` script will now query the printer upon exit to see if it is actively printing. If it is not
  printing, it will restart the `klipper` service.

## [2024-12-02]

### Added

- Buffer_Ram_Sensor
  - Enabling the buffer to be used as a ram sensor for loading and unloading filament
  - see Buffer_Ram_Sensor doc for more information

### Changed

- Adjusted load and unload to account for ram sensor
- Adjusted Prep to account for ram sensor

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

## [2024-11-23]

### Added
- New buffer function `SET_BUFFER_MULTIPLIER` used to live adjust the high and low multipliers for the buffer
    - To change `multiplier_high`: `SET_BUFFER_MULTIPLIER MULTIPLIER=HIGH FACTOR=1.2`
    - To change `multiplier_low`: `SET_BUFFER_MULTIPLIER MULTIPLIER=HIGH FACTOR=0.8`
    - `MULTIPLIER` and `FACTOR` must be defined
    - Buffer config section must be updated for values to be saved

### Fixed
-Corrected buffer to only trigger when tube comes onto switch/sensor and not off

## [2024-11-22]

### Changed

*Full update, this needs more details*

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

## [2024-10-31]

### Added

- Added LED buffer_indicator
  - allows for state change indication through color change
- Added AFC_buffer.md to layout the integration of a buffer into the AFC system

### Changed

- Changed buffer code to reflect buffer functionality and pin names
- Moved stepper commands from AFC_buffer to AFC_stepper
- Abstracted buffer status to be used in IP query and query buffer

## [2024-10-27]

### Added

- Updated the `install-afc.sh` script to include setup of the buffer configuration.
- Added `part_cooling_fan_speed` to poop macro
- Add `variable_part_cooling_fan_speed   : 1.0         # Speed to run fan when enabled above. 0 - 1.0` to your `_AFC_POOP_VARS` to change the value.

### Changed

- Broke the `install-afc.sh` script out into multiple files that are sourced by the main script for maintainability.

### Fixed
  - Fixed bug when `part_cooling_fan` was set to False

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

## [2024-08-28]

### Added

- Addition of two helper macros for the AFC system. 
  - `BT_LANE_EJECT` - This macro will eject a specified box turtle lane.
  - `BT_TOOL_UNLOAD` - This macro will unload a specified box turtle tool.

- Sample configuration files for the most popular boards are located in the `Klipper_cfg_example/AFC` directory.































