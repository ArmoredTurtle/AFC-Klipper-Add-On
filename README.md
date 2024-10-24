# Automated Filament Changer (AFC) Klipper Add-on

This Klipper plugin is for use on the Box Turtle Filament Changer (currently in closed beta). 

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

Join us on Discord [here](https://www.youtube.com/redirect?event=video_description&redir_token=QUFFLUhqbk9nSWh2YlRNR3hRYUlEdkVEeVV5VTNUNEo3QXxBQ3Jtc0trYjUtazZiVlZYM1Q4eFhlby05bGJodjFlMVRMOUwwa2NhSGdYMWptSXN0ZW45Y1hKR0dyc0Zmc3QtTlo3Yk5RM2RrcGNDU2tCXzVDa2FNSzlDam4tN3NGZEpSSEF3YUtBUXNya1h0TDhmampkeWEwOA&q=https%3A%2F%2Fdiscord.gg%2FXq9Y3CjYbd&v=sNd2FQ8EbhI).  
Armored Turtle Configuration / Build Manuals [here](https://armoredturtle.xyz/)

