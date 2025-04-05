---
Title: Macro Variables
---

## Setting up macro variables

!!!note
    AFC will perform macros (if enabled) on each tool change (``T0``, ``T1``, etc.) in the following order:

- Load sequence
    - If toolhead is loaded from another lane, that will first be unloaded (see below sequence)
    - Poop
    - Wipe/Brush
    - Kick
    - Wipe/Brush
    - Print
- Unload sequence
    - If toolhead cutter is enabled:
        - Cut
        - Park
    - If tip forming is enabled:
        - Park
        - Tip Form

### Uncommon variables

AFC has many variables that you can tweak for macros, including definition of complete custom macros to replace the
stock ones. Most users will never need to touch these, and they will not be covered in this section. A full 
listing of all configuration options is available [here](../../configuration/configuration_overview.md). Below are the 
most common variables that will need adjusting for a stock BoxTurtle configuration with a Stealthburner/FilamATrix 
toolhead.

For more details, please refer to the AFC-Klipper-Add-On GitHub docs or the comments in the `AFC/AFC.cfg` and
`AFC/AFC_Macro_Vars.cfg` files.

If you have chosen not to enable a macro during the installation, the command will still show in mainsail, and have a
configuration in `AFC_Macro_Vars.cfg`, but it will not be called during the load/unload sequences.

#### Park

The park macro is enabled or disabled by setting the `park` variable in `AFC/AFC.cfg` (this is prompted for during
the installation script, but you can change it at any time and do a firmware restart to enact the change.)

Adjust the following macro variables in `AFC/AFC_Macro_Vars.cfg` for the park macro (if enabled) for your specific
printer.

- `variable_park_loc_xy` - This is the X,Y coordinate your toolhead will park at prior to other filament changes.

#### Cut

The cut macro is enabled or disabled by setting the `tool_cut` variable in `AFC/AFC.cfg` (this is prompted for
during the installation script, but you can change it at any time and do a firmware restart to enact the change.)
Adjust the following macro variables in `AFC/AFC_Macro_Vars.cfg` for the cut macro (if enabled) for your specific
printer.

- `variable_retract_length` - How much to retract filament before performing the cut. This reduces purge waste and
  improves reliability of insertion of the next filament. Hotend dependent, a good starting value is the length of your
  melt zone. Please see the hotend diagrams for suggested values. The default is `20`.
- `variable_pin_loc_xy` - X,Y position where your toolhead cutter arm *just* touches the depressor pin. There is no
  default value, this must be defined.
- `variable_cut_direction` - For FilamATrix, you want this to be set to `left`. Other toolhead cutters may actuate
  in a different direction (e.g., Dragon Burner cutter may be `front`). The default value is `left`.
- `variable_pin_park_dist` - How far to park the toolhead near the depressor pin before initiating the move. This acts
  as a safety as well as helps generate momentum for the cut. The default value is `6.0`.
- `variable_cut_move_dist` - How far the toolhead has to move from `variable_pin_loc_xy` to fully depress the
  cutter. This should be reduced from the actual value by 0.5mm as a buffer to prevent skipped steps. The default value
  is `8.5`
- `variable_cut_count` - How many times to attempt the cut. The default value is `2`, to ensure a clean/complete
  cut.

#### Poop

The poop macro is enabled or disabled by setting the `poop` variable in `AFC/AFC.cfg` (this is prompted for during
the installation script, but you can change it at any time and do a firmware restart to enact the change.)

Adjust the following macro variables in `AFC/AFC_Macro_Vars.cfg` for the poop macro (if enabled) for your specific
printer.

- `variable_purge_loc_xy` - X,Y position where to perform the poop operation. Usually, this is on the corner of your
  bed.

#### Kick

The kick macro is enabled or disabled by setting the `kick` variable in `AFC/AFC.cfg` (this is prompted for during
the installation script, but you can change it at any time and do a firmware restart to enact the change.)
Adjust the following macro variables in `AFC/AFC_Macro_Vars.cfg` for the kick macro (if enabled) for your specific
printer.

- `variable_kick_start_loc` - the X, Y, Z location to move to prior to begin the kick operation. If you do not want a
  Z move, set the Z coordinate to `-1`.
- `variable_kick_direction` - the direction to move to kick the poop off (left, right, front, back)
- `variable_kick_move_dist` - how for to move in that direction to kick the poop off

#### Wipe/Brush

The wipe macro is enabled or disabled by setting the `wipe` variable in `AFC/AFC.cfg` (this is prompted for during
the installation script, but you can change it at any time and do a firmware restart to enact the change.)
Adjust the following macro variables in `AFC/AFC_Macro_Vars.cfg` for the brush macro (if enabled) for your specific
printer.

- `variable_brush_loc` - X, Y, Z coordinates of the center of the brush. If you do not want a Z move, set the Z
  coordinate to `-1``.
- `variable_y_brush` - Set to ``true`` if you want the macro to do a brush in the Y direction first before doing X.
  When set to `false`, only it will move only in the X direction.
- `variable_brush_width` and `variable_brush_depth` - the width and depth of your brush, in mm.
- `variable_brush_count` - Number of passes to make on the brush, the default is `4`.

#### Tip forming

!!!note
    While a toolhead cutter is recommended for best results, if you do not have one you will need to configure tip
    forming. The full process for this is outside the scope of this document and will be very hotend and perhaps even
    filament dependent. If using a 'Hub Cutter' (e.g., BT-Snappy or EREC) you will still likely need to do tip forming to
    prevent stringy tips from getting jammed in the toolhead, hub or BoxTurtle extruder gears.

Tip forming is enabled or disabled by setting the `form_tip` variable in `AFC/AFC.cfg` (this is prompted for during
the installation script, but you can change it at any time and do a firmware restart to enact the change.)

Adjust the following tip forming variables in `AFC/AFC.cfg` for tip forming (if enabled) for your specific printer.
Note the different location that the above macros.

- `cooling_tube_position` - Starting location of the cooling tube in mm (based off toolhead sensor)
- `cooling_tube_length` - Length of the cooling move in mm
- `cooling_moves` - number of cooling moves to perform, the default is `4`.

### Enacting changes

Perform a `FIRMWARE_RESTART` (a full printer reboot is not required) after adjusting all the macro variables in
`AFC/AFC_Macro_Vars.cfg` file.