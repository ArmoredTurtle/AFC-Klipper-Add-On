---
Title: FAQ
---

# Frequently Asked Questions

!!! Question 

    Is the AFC Software only for Box Turtle?

??? Answer 
    No - The AFC Klipper add-on is not designed specifically for Box Turtle and can be implemented with other filament
    changing systems with a similar form factor. 2 Endstops per lane plus a hub are required.

!!! Question

    Does Happy Hare support BoxTurtle/AFC?

??? Answer
    Yes, although the AFC Klipper Add-on is incompatible with Happy Hare, in order to use AFC you must remove 
    Happy Hare, or vice versa.

!!! Question
    
    How much filament will I need to print Box Turtle?

??? Answer

    For a standard build you will need:
        1.4kg Primary color
        .3kg Accent Color
        60g TPU

!!! Question

    Do any parts need support when printing?

??? Answer

    All STL files from ArmoredTurtle are pre-oriented and have built-in supports where they are needed. For best results do
    not change the orientation or add additional supports.

!!! Question
    
    What switch type does my kit use?

??? Answer 
    
    If you are printing parts for an LDO Box Turtle or Isik's Tech kit , you will want to use the D2HW option 
    when selecting STL files for extruders and hub. For any other kit, please refer to the vendor's BOM.

!!! Question

    My 30t Gear is Loose!

??? Answer

    The MJF gears provided by LDO are extras from the beta kits, and difficult to manufacture with proper 
    tolerances. We recommend you print your own 30t and 15t gears, adjusting the XY scale/shrinkage to get a proper 
    fit. If you really want to use the MJF gears, you can secure them with a drop of glue, just make sure it is in 
    the correct location on the shaft before it dries.

!!! warning

    ❗Potential CAN issues with Cartographer and AFC-Lite ❗
    There have been reports of issues with Cartographer and AFC-Lite running on the same CAN Network
    This ultimately could result in damage to the Cartographer Probe. Suggestions from the cartographer community include:
        
        - Running Cartographer or AFC-Lite on USB instead of CAN
        - If you can not switch one to USB, run the devices on separate CAN networks