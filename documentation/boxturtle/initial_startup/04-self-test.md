## First self-test

AFC will run a self-test automatically on startup. It will run through the respoolers on each lane (from left to right,
lanes 1-4) and will update the lightbox LED indicating status for each lane.

The default status indicators are:

- Red: No filament loaded/detected at extruder sensor
- Green: Filament loaded to lane extruder sensor
- Blue: Filament loaded to toolhead
- White: Filament in process of being loaded

If the colors are different between LEDs, or if loading one changes the colors of others, your neopixel
`color_order` (found in `AFC/AFC_Turtle_1.cfg`) is incorrect. Try changing from the default of `GRBW` to `GRB`
to start, those are the two most common options.

After the self-test completes, you hopefully will see a picture of a happy turtle in the console log (NOTE: an upright
turtle is a happy turtle)! If you get a picture of an error turtle (upside down), you may have a misconfigured AFC
setting, broken pin or some other issue that needs attention.

You can display the status of sensors in Mainsail/Fluidd as regular filament switches by setting
`enable_sensors_in_gui: True` either globally in `AFC/AFC.cfg` or in the individual component section (e.g.
extruders in `AFC/Turtle_1.cfg`.

If you are unable to resolve the error after visiting
the [troubleshooting guide](../../troubleshooting/troubleshooting.md),
you can get support from the community on the Armored Turtle discord by opening a help thread (run the Discord command
``/help``) to learn how).