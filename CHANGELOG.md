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

## [Unreleased]

### Added

 - Added `loaded_to_hub` parameter to get_status so users can see if filament is loaded to  their hub

### Changed

 - Revamped `install-afc.sh` script to be interactive and provide more configuration options for the user.
 - Updated `ruff` GHA to only scan for changed files.
 - Updates to AFC.cfg file. Be sure to backup current file and replace with new version, then update values from backed up file.
 - Manually changes needed to AFC_hardware.cfg
    - `[filament_switch_sensor tool]` update to `[filament_switch_sensor tool_start]`
    - If using sensor after gears `[filament_switch_sensor extruder]` updaste to `[filament_switch_sensor tool_end]`

### Fixed

### Removed

