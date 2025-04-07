# Troubleshooting

## Common Issues

### `TMC 'AFC_stepper lane1' reports error: GSTAT:      00000001 reset=1(Reset)`

This may be due to static building up in the system from the PTFE tubing in dry/low humidity environments. Many users
have found that running a ground wire from the stepper motor screws to a common GND pin on the AFC-Lite board, resolves
this issue. One example way to do this is below:

For each motor:

- Replace the M3x8 extruder motor mount screw with a M3x12 screw.
- Crimp a ring connector on a wire. Place a m3 washer over the now extended motor mount screw, followed by the ring
terminal, followed by an M3 hex or nyloc nut.

Join the wires from all the motors into a 5 port [WAGO 221-415](https://www.wago.com/us/wire-splicing-connectors/compact-splicing-connector/p/221-415). In the 5th port, run a wire from the WAGO to any spare
ground pin on the AFC-Lite board (e.g., the GND pin on RGB2).

### LEDs not displaying correct colors

If your leds are not displaying the correct color update the following value under your AFC_led section in 
`~/printer_data/config/AFC/AFC_Turtle_(n).cfg` file.

- color_order: change to match the color order for you leds. Different color orders are: RGB, RGBW, GRB, GRBW

### Filament pulling past extruder during unloads

During unloads if your filament retracts too much and goes past the lanes extruder then decrease your 
`afc_bowden_length` value in `~/printer_data/config/AFC/AFC.cfg` file.

### Timer too close (TTC) error

If you keep getting TTC errors start by adding the following to `~/printer_data/config/AFC/AFC.cfg` file under the 
[AFC] section.

`trsync_update: True`

### Layer shift when using the cut macro

If you notice a layer shift occurs while using the cut macro, setting a higher stepper current while cutting has shown 
to help with this. Update and uncomment the following values in `~/printer_data/config/AFC/AFC_Macro_Vars.cfg` file.

- `variable_cut_current_stepper_x` - start with ~1.7-1.8A
- `variable_cut_current_stepper_y` - start with ~1.7-1.8A
- Only needed if cutting action is along the z - `variable_cut_current_stepper_z`

- Make sure your stepper names are updated for variables: `variable_cut_current_stepper_x`, `variable_cut_current_stepper_y`, `variable_cut_current_stepper_z`