---
Title: AFC-Lite Plugin Installation
---

## Install the AFC Klipper Add-On

BoxTurtle works best with the [AFC Klipper Add-On](https://github.com/ArmoredTurtle/AFC-Klipper-Add-On). The rest of
this guide will focus on configuring AFC for use with BoxTurtle.

Follow the instructions on that GitHub for latest details on installation and configuration, but at the time of writing
this is the easy button:

```
cd ~
git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
cd AFC-Klipper-Add-On
./install-afc.sh
```

The default options for the park, cut, kick, wipe, and tip forming macros can be used if you don't know what to choose.
These can all be changed later by editing `AFC/AFC.cfg` and doing a firmware restart.

After the installation completes, you should now see an AFC folder in your printer configuration directory, along with
several files in there named `AFC.cfg`, `AFC_Hardware.cfg`, `AFC_Macro_Vars.cfg`, and `AFC_Turtle_1.cfg` (if
using the default name). If you do not see these files, or if you see duplicate files (e.g., your `printer.cfg`) -
this may be a caching issue with your web UI (mainsail/fluidd). Force a refresh with shift-reload or Ctrl+F5 and the
problem should resolve itself.

After installation, please ensure sure you update the following settings:

- In `AFC/AFC_Turtle_1.cfg`:
    - `canbus_uuid` if using CAN bus
    - `serial` if using USB
- In `AFC/AFC_Hardware.cfg`
    - `pin_tool_start` and/or ``pin_tool_end`

In your `printer.cfg`'s `[extruder]` section, update the setting `max_extrude_only_distance` to the value 400. If
the setting is not there, add it:

`max_extrude_only_distance: 400`

For best results, reboot your printer after installing the Add-On and including it in your printer.cfg. This will ensure
all required modules are enabled.