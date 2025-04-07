## Updating your PRINT_START macro

!!!info
        Please note this is just an example macro to show how to incorporate the initial tool into your 
        print start macro.

Please adjust it to match your printer setup. A good starting point for a PRINT_START macro
is [jontek2's "A Better PRINT_START macro"](https://github.com/jontek2/A-better-print_start-macro)

Add the TOOL parameter we added to the Machine start G-Code earlier to your PRINT_START macro.

``` g-code
[gcode_macro PRINT_START]
gcode:
  {% set BED_TEMP = params.BED|default(60)|float %}
  {% set EXTRUDER_TEMP = params.EXTRUDER|default(195)|float %}
  {% set S_EXTRUDER_TEMP = 150|float %}
  {% set initial_tool = params.TOOL|default("0")|int %}

  G90 ; use absolute coordinates
  M83 ; extruder relative mode

  G28 # Home Printer
  # Do any other leveling such as QGL here

  AFC_PARK

  M140 S{BED_TEMP} # Set bed temp
  M109 S{EXTRUDER_TEMP} # wait for extruder temp
  T{initial_tool} #Load Initial Tool

  M104 S{S_EXTRUDER_TEMP} # set standby extruder temp
  M190 S{BED_TEMP} # wait for bed temp

  G28 Z

  # Bedmesh or load bedmesh

  AFC_PARK
  M109 S{EXTRUDER_TEMP} ; wait for extruder temp

  # Add any pre print prime/purge line here
  # Start Print
```

If you are modifying an existing macro:

- Add the following to the top of the PRINT_START macro just under the `gcode:` line

``` g-code
  {% set BED_TEMP = params.BED|default(60)|float %}
  {% set EXTRUDER_TEMP = params.EXTRUDER|default(195)|float %}
  {% set S_EXTRUDER_TEMP = 150|float %}
  {% set initial_tool = params.TOOL|default("0")|int %}
```

- Home the printer using `G28`
- Set hotend to extrusion temperature `M104 S{EXTRUDER_TEMP}`
- Load the first filament to be used with `T{initial_tool}`
- Move to park position with `AFC_PARK`
- Lower the hotend to standby temperature with `M104 S{S_EXTRUDER_TEMP}`
- Perform any other necessary pre-flight tasks (e.g., heat soak, re-homing Z, bed meshing, prime/purge line, etc)