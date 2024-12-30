# Automated Filament Changer (AFC) Klipper Add-on

This Klipper plugin is for use on the Box Turtle Filament Changer. The Box Turtle is currently in an open beta.
More information can be found [here](https://github.com/ArmoredTurtle/BoxTurtle)

Further information to include command references can be found in the [docs](./docs) folder.

## Usage

Usage instructions for the `install-afc.sh` script can be shown by running:
```bash
./install-afc.sh -h
```

## Installation

To install this plugin, you should have the following pre-requisites installed:

  1) Klipper
  2) Moonraker
  3) WebUI (Mainsail or Fluidd) 

To install this plugin, you can use the following commands from the users home directory:

```bash
cd ~
git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
cd AFC-Klipper-Add-On
./install-afc.sh
```

## Updates

To update the AFC plugin software, you can simply run the following command:
```bash
cd AFC-Klipper-Add-On
./install-afc.sh
```
The update process should be non-destructive and will not overwrite any existing configuration files without your permission.
If you run into an issue due to a specific configuration, you may need to comment out the AFC plugin software and re-run the `install-afc.sh` script.

This can be accomplished by commenting out the following lines in your `printer.cfg` file:
```cfg
[include AFC/*.cfg]
```
Once the plugin is updated, please uncomment the lines in your `printer.cfg` file (if applicable).

## Configuration (Automated)

The `install-afc.sh` script will automatically install the majority of the plugin for you. 

Prior to starting Klipper, please review the configuration located at `~/printer_data/config/AFC/AFC_Hardware.cfg` and ensure all pins are correct for your specific hardware.

Additionally, review the following files for any changes that may be required:

  1) `~/printer_data/config/AFC/AFC.cfg`
  2) `~/printer_data/config/AFC/AFC_Macro_Vars.cfg`

Review information in [mandatory configuration changes](README.md#mandatory-configuration-changes-all) section

## Installation & Configuration (Manual)

To manually install and configure the plugin, you can use the following commands:

```bash
cd ~
git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
cd AFC-Klipper-Add-On
ln -sf ~/AFC-Klipper-Add-On/extras/*.py ~/klipper/klippy/extras/
mkdir -p ~/printer_data/config/AFC
cp -R ~/AFC-Klipper-Add-On/config/* ~/printer_data/config/AFC/
```

Next, please copy the appropriate `AFC_Hardware.cfg` template file from `~/AFC-Klipper-Add-On/templates` to `~/printer_data/config/AFC` 
and modify the file to match your hardware configuration. Ensure you rename the file properly based on the selected board type to `AFC_Hardware.cfg`.

Finally, review and update the following files as needed for your configuration.

  1) `~/printer_data/config/AFC/AFC.cfg`
  2) `~/printer_data/config/AFC/AFC_Macro_Vars.cfg`
  3) `~/printer_data/config/AFC/AFC_Hardware.cfg`

### Buffer configuration - Manual

If you are using a buffer such as the Turtleneck, Turtleneck v2 or Annex Belay, and you installed the software manually, you may need to make a couple of additional changes.

You should add the following block to your `AFC_Hardware.cfg` file based on the type of buffer you are using.

**NOTE** The `pin` value should be set to the pin that the buffer is connected to on your board.

#### Turtleneck
```cfg
[AFC_buffer TN]
advance_pin:     # set advance pin
trailing_pin:    # set trailing pin
multiplier_high: 1.05   # default 1.05, factor to feed more filament
multiplier_low:  0.95   # default 0.95, factor to feed less filament
velocity: 100
```

Turtleneck v2
```cfg
[AFC_buffer TN2]
advance_pin: !turtleneck:ADVANCE
trailing_pin: !turtleneck:TRAILING
multiplier_high: 1.05   # default 1.05, factor to feed more filament
multiplier_low:  0.95   # default 0.95, factor to feed less filament
led_index: Buffer_Indicator:1
velocity: 100

[AFC_led Buffer_Indicator]
pin: turtleneck:RGB
chain_count: 1
color_order: GRBW
initial_RED: 0.0
initial_GREEN: 0.0
initial_BLUE: 0.0
initial_WHITE: 0.0
```

Annex Belay
```cfg
[AFC_buffer Belay]
pin: mcu:BUFFER
distance: 12
velocity: 1000
accel: 1000
```

Finally, add `Buffer_Name: <TYPE>` to your `AFC.cfg` file.  For example, if you are using the Turtleneck v2, you would add the following line:

```cfg
Buffer_Name: TN2
```

Additional information about the buffer configuration and operation can be found in the [AFC_buffer.md](./docs/AFC_buffer.md) file.



## Mandatory Configuration Changes (All)

Prior to operation, the following checks / updates **MUST** be made to your system:

1) Update the following values in the `~/printer_data/config/AFC/AFC.cfg` file:

   - tool_stn: This value is the length from your toolhead sensor to nozzle
   - tool_stn_unload: This value is the amount to unload from extruder when doing a filament change.
   - afc_bowden_length: This value is the length from your hub to your toolhead sensor

2) Verify that `pin_tool_start` is set to the correct pin for your toolhead sensor. If you are using an existing filament sensor as your toolhead sensor make sure you comment out the filament sensor section in your `printer.cfg` file.

3) If you are using any of the built-in macros, the variables in the `~/printer_data/config/AFC/AFC_Macro_Vars.cfg` file
must also be modified to match your configuration for your system.

    Required variables to verify and update if necessary for the following default macros
    - tool_cut:
      - variable_retract_length
      - variable_cut_direction
      - variable_pin_loc_xy
      - variable_pin_park_dist
      - variable_cut_move_dist
    - park:
      - variable_park_loc_xy
    - poop: 
      - variable_purge_loc_xy
    - kick:
      - variable_kick_start_loc
      - variable_kick_direction
    - wipe
      - variable_brush_loc
      - variable_y_brush
    - form_tip
      Variables to update for tip forming are in `~/printer_data/config/AFC/AFC.cfg`
      - cooling_tube_position
      - cooling_tube_length

4) If you would like to use your own macro instead of the provided macros, make sure to update the command with your custom macro in `~/printer_data/config/AFC/AFC.cfg`  
	  ex. If using custom park macro, change `park_cmd` from `AFC_PARK` to your macro name

**Failure to update these values can result in damage to your system**

## Optional Configuration Changes

If you use a Turtleneck v2, you can enable the buffer indicator LED by adding the following lines to your `AFC.cfg` file:

```cfg
led_buffer_advancing: 0,0,1,0
led_buffer_trailing: 0,1,0,0
led_buffer_disable: 0,0,0,0.25
```

If using a hub that is not located in the box turtle the following value needs to be updated for each stepper  
  - dist_hub: This value the the length between the lanes extruder and the hub, this does not have to be exact and is better to figure the length and then minus about 40mm
  
If using snappy hub cutter update the following values:
  - cut: change to True
  - cut_dist: update to the value that you would like to cut off the end, this may take some tuning to get right

## Automatic Calibration

The function `CALIBRATE_AFC` can be called in the console to calibrate distances.  
_distances will be calibrated to have ~1 short move after the move distance_

### Definitions

- `dist_hub` for each lane is the distance from the load switch at the extruder to the hub
- `afc_bowden_length` is the distance from the hub to the toolhead sensor

### Usage

`CALIBRATE_AFC LANE=<lane> DISTANCE=<distance> TOLERANCE=<tolerance> BOWDEN=<lane>`  
_`DISTANCE` and `TOLERANCE` are optional. default distance 25mm, default tolerance 5mm_

- To calibrate all lanes and the bowden length all at once:
  - `CALIBRATE_AFC LANE=all BOWDEN=<lane>` input which lane to be used to check `afc_bowden_length`
- To calibrate individual lanes
  - `CALIBRATE_AFC LANE=<lane>` input the lane you would like to calibrate
- To calibrate just the bowden length:
  - `CALIBRATE_AFC BOWDEN=<lane>` input which lane to be used to check `afc_bowden_length`

If using a hub different from the stock set up `hub_clear_move_dis` under AFC unit may need to be increased/decreased to match your setup, default `50mm`.  
**All values must be updated in AFC_Hardware.cfg after calibration**

## Troubleshooting

Debug information about the respooler system can be found by visiting the following URL in your browser:

`{ip address}/printer/objects/query?AFC`

## LEDs not displaying correct color
If your leds are not displaying the correct color update the following value under your `AFC_led` section in `~/printer_data/config/AFC/AFC_hardware.cfg` file.
  - color_order: change to match the color order for you leds. Different color orders are: RGB, RGBW, GRB, GRBW


## Filament pulling past extruder during unloads
During unloads if your filament retracts too much and goes past the lanes extruder then decrease your `afc_bowden_length` value in `~/printer_data/config/AFC/AFC.cfg` file


## Timer too close (TTC) error
If you keep getting TTC errors start by adding the following to `AFC/AFC.cfg` file under `[AFC]` section  
- `trsync_update: True`


## Layer shift when using cut macro
If you notice a layer shift occurs while using the cut macro, setting a higher stepper current while cutting has shown to help with this.
Update and uncomment the following values in `AFC/AFC_Macr_Vars.cfg` file
- variable_cut_current_stepper_x - start with ~1.7-1.8A
- variable_cut_current_stepper_y - start with ~1.7-1.8A
- Only needed if cutting action is along the z - variable_cut_current_stepper_z

Make sure your stepper names are updated for variables: `variable_cut_current_stepper_x, variable_cut_current_stepper_y, variable_cut_current_stepper_z`


## Removing Plugin

To remove the plugin, you can use the following commands:

```bash
cd ~/AFC-Klipper-Add-On
./install-afc.sh -u
```

## Support

[![Join me on Discord](https://discord.com/api/guilds/1229586267671629945/widget.png?style=banner2)](https://discord.gg/eT8zc3bvPR)

Armored Turtle Configuration / Build Manuals [here](https://armoredturtle.xyz/)

