# Automated Filament Changer (AFC) Klipper Add-on

This Klipper plugin is for use on the Box Turtle Filament Changer. The Box Turtle is currently in an open beta.
More information can be found [here](https://github.com/ArmoredTurtle/BoxTurtle)

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

## Configuration (Automated)

The `install-afc.sh` script will automatically install the majority of the plugin for you. 

Prior to starting Klipper, please review the configuration located at `~/printer_data/config/AFC/AFC_Hardware.cfg` and ensure all pins are correct for your specific hardware.

Additionally, review the following files for any changes that may be required:

  1) `~/printer_data/config/AFC/AFC.cfg`
  2) `~/printer_data/config/AFC/AFC_Macro_Vars.cfg`

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
multiplier_high: 1.1   # default 1.1, factor to feed more filament
multiplier_low:  0.9   # default 0.9, factor to feed less filament
```

Turtleneck v2
```cfg
[AFC_buffer TN2]
advance_pin: !turtleneck:ADVANCE
trailing_pin: !turtleneck:TRAILING
multiplier_high: 1.1   # default 1.1, factor to feed more filament
multiplier_low:  0.9   # default 0.9, factor to feed less filament
led_index: Buffer_Indicator:1

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

## Usage

Usage instructions for the `install-afc.sh` script can be shown by running:
```bash
~/AFC-Klipper-Add-On/install-afc.sh -h
```

## Mandatory Configuration Changes (All)

Prior to operation, the following checks / updates **MUST** be made to your system:

1) Update the following values in the `~/printer_data/config/AFC/AFC.cfg` file:

   - tool_stn
   - tool_stn_unload
   - afc_bowden_length

2) If you are using any of the built-in macros, the variables in the `~/printer_data/config/AFC/AFC_Macro_Vars.cfg` file
must also be modified to match your configuration for your system. 

**Failure to update these values can result in damage to your system**

## Optional Configuration Changes

If you use a Turtleneck v2, you can enable the buffer indicator LED by adding the following lines to your `AFC.cfg` file:

```cfg
led_buffer_advancing: 0,0,1,0
led_buffer_trailing: 0,1,0,0
led_buffer_disable: 0,0,0,0.25
```

## Troubleshooting

Debug information about the respooler system can be found by visiting the following URL in your browser:

`{ip address}/printer/objects/query?AFC`


## Removing Plugin

To remove the plugin, you can use the following commands:

```bash
cd ~/AFC-Klipper-Add-On
./install-afc.sh -u
```

## Support

[![Join me on Discord](https://discord.com/api/guilds/1229586267671629945/widget.png?style=banner2)](https://discord.gg/eT8zc3bvPR)

Armored Turtle Configuration / Build Manuals [here](https://armoredturtle.xyz/)

