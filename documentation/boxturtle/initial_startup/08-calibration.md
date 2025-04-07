## Calibration

Follow [this guide](../../installation/calibration.md) and run the guided calibration to find the necessary lengths of your BoxTurtle lanes.

Note that these values may need to be tweaked slightly if the loading sequence does not function. Make small
adjustments (5/10mm) to see if performance/reliability improves.

## First load of filament to toolhead

You're now ready to attempt your first Automated Filament Control action!

- Home your printer (using G28 or Mainsail/Fluidd GUI buttons)
- Heat the hotend to your filament's extrusion temperature (e.g., PLA 210, ABS 260, etc.).
- Load the filament for lane 1 with the `T0` command.
- Confirm that filament travels to the toolhead and performs any configured poop or wipe actions. After the load has
  successfully completed, test that you are able to manually extrude filament using the console/GUI.
- Change filament to lane 2 using the `T1` command. Confirm that the toolhead moves to the park position, performs the
  cut (or tip shaping, if not using a cutter), retracts the filament for lane 1 back to the BoxTurtle hub. It will then
  load the filament in lane 2 to the toolhead, and perform the poop, wipe, kick and wipe macros.
- Repeat this process for lane 3 (`T2`) and lane 4 (`T3`).

If you are able to successfully load and unload filament without intervention, you are ready to move on to the next
step. Almost there!