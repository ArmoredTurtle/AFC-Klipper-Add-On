# Automated Filament Changer (AFC) Klipper Add-on

This Klipper plugin is for use on the Box Turtle Filament Changer (currently in closed beta). 

## Installation

To install this plugin, you should have the following pre-requisites installed:

  1) Klipper
  2) Moonraker
  3) WebUI (Mainsail or Fluidd) 

To install this plugin, you can use the following commands from the users home directory:

```bash
wget -O - https://raw.githubusercontent.com/ArmoredTurtle/AFC-Klipper-Add-On/main/install-afc.sh | bash
```

## Configuration

Sample configuration files for the most popular boards are located in the `Klipper_cfg_example/AFC` directory.

The `AFC` directory should be placed in your `~/printer_data/config` directory and included in your `printer.cfg` file.

```
[include AFC/*.cfg]
```

Ensure you rename one of the sample configuration files and replace the extension with `.cfg` such as `afc_hardware_AFC.cfg` and so forth.

You *MUST* double-check all pins in the configuration file for your specific hardware prior to using.
## Usage


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

