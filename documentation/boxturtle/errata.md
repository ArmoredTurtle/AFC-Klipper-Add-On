# BoxTurtle Errata

Below are issues that were not able to be corrected in time for v1.0 release.

## AFC-Lite v1.0 USB connector orientation

While BoxTurtle was originally designed for connecting with CAN bus (and that is still the recommended configuration if
possible), it can also be connected with USB for data communications.

If you have an AFC-Lite v1.0 board, the USB connector faces outward in an orientation that is not optimal for a regular
USB-C plug in the stock mounting position. This was corrected with AFC-Lite v1.1. As a workaround, use a right-angle
USB-C cable or adapter to connect the BoxTurtle.

## LDO Kit known issues

### 30 Tooth MJF gear loose (Batch 1 & 2)

The 30 tooth MJF gears provided in the kit will likely be too loose to use as-is on the 8 x 80mm shaft. Either print
the [FDM version of the gears](https://github.com/ArmoredTurtle/BoxTurtle/blob/main/STLs/Base_Build/Spooler/helical_gear_30_teeth_x4.stl)
or secure the MJF gear with some glue at the appropriate position on the shaft (using the installation tool). Make sure
to not glue the gear to the installation jig! Also ensure that any glue residue is removed that would prevent the spacer
from sitting flush against the gear.

Starting with Batch 3, these gears are properly toleranced and pre-affixed to the N20 motors and 8x80mm rods.

### TurtleNeck switches missing levers (Batch 1)

The TurtleNeck switches are missing the required metal levers, and the FilamATrix switches have levers.
Follow [this guide](https://www.youtube.com/watch?v=1cHecdyxhpw) on how to migrate the switches from the FilamATrix
switches to the TurtleNeck buffer switches.

### TurtleNeck switch cable labels (Batch 1)

The TurtleNeck switch cables are labeled 1 and 2 in Batch 1 kits. For simplicity, use "1" for the Advance switch and "2"
for the Trailing switch.

### Missing wheel heat set/screws (Batch 1, 2)

Changes were made to the wheel design late in the beta process after hardware kits had been created/bagged/labeled. As
such, the extra hardware required for the wheels (heat sets and M3x6 screws) are in a separate 'Hardware for Wheel' bag
included in your kit.

### 3mm ID PTFE tubing (Batch 1, 2)

The 3mm ID PTFE tubing is a bit short of length from the BOM. Make sure you cut the 80mm lengths between the motor mount
and extruder body first. The feeder inlet tubes are specified to be 50mm in the manual, but can easily be shorter at
40-45mm.

Starting with Batch 3, 1.3m of 3mmID PTFE are included which is more than double the original BOM.

### No cable included to connect BoxTurtle to the printer (Batch 1, 2, 3)

As each printer connection is different, cable was not included in batch 1 kits to connect the BoxTurtle to your
printer. A 2x2 pin Molex connector is included in the kits for you to create your own cable to connect the AFC lite for
power and (optionally) CAN bus data.

### N20 motor failure

If you encounter any suspected failure issue with your N20 respooler motors, please contact your reseller. LDO is
conducting analysis on any failures.

### M3 heat set count for FilamATrix (Batch 1, 2)

If you are doing a new build of Clockwork2 there will not be sufficient heat sets in the bag - the kits were designed
with an upgrade to an existing CW2 extruder in mind. Additionally, the kits may be a 1-2 heat sets short for all
components even after accounting for spares in the FilamATrix bag, this will be corrected in a future batch.