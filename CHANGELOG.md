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

### Changed

 - Revamped `install-afc.sh` script to be interactive and provide more configuration options for the user.
 - Updated `ruff` GHA to only scan for changed files.
 - Updates to AFC.cfg file. Be sure to backup current file and replace with new version, then update values from backed up file.
 - Manually changes needed to AFC_hardware.cfg
    - `[filament_switch_sensor tool]` update to `[filament_switch_sensor tool_start]`
    - If using sensor after gears `[filament_switch_sensor extruder]` updaste to `[filament_switch_sensor tool_end]`

### Fixed
### Removed

## [2024-10-24]

### Added

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

  - Full functionality change for Turtleneck/ Turtleneck 2.0 style buffers
  - Changed buffer configuration examples, new configuration is required for full functionality!
    - `multiplier_high` controls the speed up of filament being fed
    - `multiplier_low` controls the slow down of filament being fed
  - `QUERY_BUFFER` will output rotation distance if applicable

### Fixed
  - minor adjustments to the use of single sensor buffers, retaining functionality for Belay
### Removed

