# Configuration Overview

The AFC-Klipper-Add-On is designed to be highly configurable, allowing you to tailor its functionality to your specific needs. 
This section provides an overview of the configuration options available in the AFC-Klipper-Add-On. 

## Configuration Files

The AFC-Klipper-Add-On uses a variety of configuration files to define its behavior and settings. These files are 
installed by the `install-afc.sh` script and are by default located in the `~/printer_data/config/AFC` directory.

!!! note
    The configuration files are typically named with a `.cfg` extension and can be edited using any text editor. 

When the AFC-Klipper-Add-On is installed, a set of default configuration files are created. An example of the default 
installation directory structure for a BoxTurtle is shown below. 

```plaintext
~/printer_data/config/AFC
├── AFC.cfg
├── AFC_Turtle_1.cfg
├── AFC_Hardware.cfg
├── AFC_Macro_Vars.cfg
├── macros
│   ├── AFC_macros.cfg
│   ├── Brush.cfg
│   ├── Cut.cfg
│   ├── Kick.cfg
│   ├── Park.cfg
│   └── Poop.cfg
└── mcu
    ├── AFC_Lite.cfg
    ├── MMB_1.0.cfg
    └── MMB_1.1.cfg
```

!!! note
    The actual directory structure may vary depending on your specific setup and the version of the AFC-Klipper-Add-On 
    you are using. The above example is for illustrative purposes only. 


Each of these configuration files serves a specific purpose and can be customized to suit your needs. Each file is 
covered in more detail in their respective section of the documentation with all available configuration options 
explained.

The naming convention for the `AFC_Turtle_1.cfg` file is covered in the `AFC_UnitType_1.cfg` section of the documentation.

Each section of the configuration file is formatted as follows:

```plaintext
[Configuration Section]
configuration_option: value
```

Where `Configuration Section` is the name of the section and `configuration_option` contains the value for that option.

Some options may have a default, and are not included in the default configuration file. These options are typically
set to a reasonable default value, but can be overridden in the configuration file if needed. These options will be 
highlighted in the documentation with a note indicating that they are optional and are set to a default value.