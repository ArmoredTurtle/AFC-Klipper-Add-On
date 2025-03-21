# Armored Turtle Automated Filament Control (AFC) Calibration

## Guided Calibration

`AFC_CALIBRATION` starts the process of a guided calibration process. Prompts will show in the gui that will walk through calibration steps.

## Manual Calibration

The function `CALIBRATE_AFC` can be called in the console to calibrate distances.  
_distances will be calibrated to have ~1 short move after the move distance_

**NOTE: If using Turtleneck buffer please hold hold shut until filament reaches toolhead, once buffer start expanding slowly release. Doing this will keep the calibration from falsely triggering before fully reaching toolhead. Also pay attention and make sure the neck is not fully extended and triggering the advance sensor.**

### Definitions

- `dist_hub` for each lane is the distance from the load switch at the extruder to the hub
- `afc_bowden_length` is the distance from the hub to the toolhead sensor

### Usage

`CALIBRATE_AFC LANE=<lane> DISTANCE=<distance> TOLERANCE=<tolerance> BOWDEN=<lane> UNIT=<unit>`  
_`DISTANCE` and `TOLERANCE` are optional. default distance 25mm, default tolerance 5mm. `UNIT` can be used to calibrate all lanes in one unit_

- To calibrate all lanes and the bowden length all at once:
  - `CALIBRATE_AFC LANE=all BOWDEN=<lane>` input which lane to be used to check `afc_bowden_length`
- To calibrate individual lanes
  - `CALIBRATE_AFC LANE=<lane>` input the lane you would like to calibrate
- To calibrate just the bowden length:
  - `CALIBRATE_AFC BOWDEN=<lane>` input which lane to be used to check `afc_bowden_length`