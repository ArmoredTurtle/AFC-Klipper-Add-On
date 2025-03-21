# AFC Klipper Add-On Command Reference

## Built-in AFC Functions

The following commands are built-in the AFC-Klipper-Add-On and are available through 
the Klipper console.

NOTE: LANE/HUB/BUFFER etc. names are case sensitive and should exactly match the names defined in config files
### AFC_CALIBRATION
_Description_: Open a prompt to start AFC calibration by selecting a unit to calibrate. Creates buttons for each unit and
allows the option to calibrate all lanes across all units.  
  
Usage: ``AFC_CALIBRATION``  
Example: ``AFC_CALIBRATION``  

### AFC_RESET
_Description_: This function opens a prompt allowing the user to select a loaded lane for reset. It displays a list of loaded lanes
and provides a reset button for each lane. If no lanes are loaded, an informative message is displayed indicating
that a lane must be loaded to proceed with resetting.  
  
Usage: ``AFC_RESET DISTANCE=<distance>``  
Example: `AFC_RESET LANE=lane1`  

### AFC_RESUME
_Description_: This function clears the error state of the AFC system, sets the in_toolchange flag to False,
runs the resume script, and restores the toolhead position to the last saved position.  
  
Usage: ``AFC_RESUME``  
Example: ``AFC_RESUME``  

### AFC_STATUS
_Description_: This function generates a status message for each unit and lane, indicating the preparation,
loading, hub, and tool states. The status message is formatted with HTML tags for display.  
  
Usage: ``AFC_STATUS``  
Example: ``AFC_STATUS``  

### ALL_CALIBRATION
_Description_: Open a prompt to confirm calibration of all lanes in all units. Provides 'Yes' to confirm and 'Back' to
return to the previous menu.  
  
Usage: ``ALL_CALIBRATION``  
Example: ``ALL_CALIBRATION``  

### CALIBRATE_AFC
_Description_: This function performs the calibration of the hub and Bowden length for one or more lanes within an AFC
(Automated Filament Control) system. The function uses precise movements to adjust the positions of the
steppers, check the state of the hubs and tools, and calculate distances for calibration based on the
user-provided input. If no specific lane is provided, the function defaults to notifying the user that no lane has been selected. The function also includes
the option to calibrate the Bowden length for a particular lane, if specified.  
  
Usage: ``CALIBRATE_AFC LANE=<lane> DISTANCE=<distance> TOLERANCE=<tolerance> BOWDEN=<lane>``  
Example: `CALIBRATE_AFC LANE=lane1`  

### CHANGE_TOOL
_Description_: This function handles the tool change process. It retrieves the lane specified by the 'LANE' parameter,
checks the filament sensor, saves the current position, and performs the tool change by unloading the
current lane and loading the new lane.
Optionally setting PURGE_LENGTH parameter to pass a value into poop macro.  
  
Usage: ``CHANGE_TOOL LANE=<lane> PURGE_LENGTH=<purge_length>(optional value)``  
Example: ``CHANGE_TOOL LANE=lane1 PURGE_LENGTH=100``  

### GET_TIP_FORMING
_Description_: Shows the tip forming configuration  
  
Usage: `GET_TIP_FORMING`  
Example: `GET_TIP_FORMING`  

### HUB_CUT_TEST
_Description_: This function tests the cutting sequence of the hub cutter for a specified lane.
It retrieves the lane specified by the 'LANE' parameter, performs the hub cut,
and responds with the status of the operation.  
  
Usage: ``HUB_CUT_TEST LANE=<lane>``  
Example: ``HUB_CUT_TEST LANE=lane1``  

### HUB_LOAD
_Description_: This function handles the loading of a specified lane into the hub. It performs
several checks and movements to ensure the lane is properly loaded.  
  
Usage: ``HUB_LOAD LANE=<lane>``  
Example: ``HUB_LOAD LANE=lane1``  

### LANE_RESET
_Description_: This function resets a specified lane to the hub position in the AFC system. It checks for various error conditions,
such as whether the toolhead is loaded or whether the hub is already clear. The function moves the lane back to the
hub based on the specified or default distances, ensuring the lane's correct state before completing the reset.  
  
Usage: ``LANE_RESET LANE=<lane> DISTANCE=<distance>``  
Example: `LANE_RESET LANE=lane1`  

### LANE_UNLOAD
_Description_: This function handles the unloading of a specified lane from the extruder. It performs
several checks and movements to ensure the lane is properly unloaded.  
  
Usage: ``LANE_UNLOAD LANE=<lane>``  
Example: ``LANE_UNLOAD LANE=lane1``  

### QUERY_BUFFER
_Description_: Reports the current state of the buffer sensor and, if applicable, the rotation
distance of the current AFC stepper motor.  
  
Usage: `QUERY_BUFFER BUFFER=<buffer_name>`  
Example: `QUERY_BUFFER BUFFER=TN`  

### RESET_AFC_MAPPING
_Description_: This commands resets all tool lane mapping to the order that is setup in configuration. Useful to put in your PRINT_END macro to reset mapping  
  
Usage: `RESET_AFC_MAPPING`  
Example: `RESET_AFC_MAPPING`  

### RESET_FAILURE
_Description_: This function clears the error state of the AFC system by setting the error state to False.  
  
Usage: ``RESET_FAILURE``  
Example: ``RESET_FAILURE``  

### SAVE_EXTRUDER_VALUES
_Description_: Macro call to write tool_stn, tool_stn_unload and tool_sensor_after_extruder variables to config file for specified extruder.  
  
Usage: ``SAVE_EXTRUDER_VALUES EXTRUDER=<extruder>``  
Example: ``SAVE_EXTRUDER_VALUES EXTRUDER=extruder``  

### SAVE_HUB_DIST
_Description_: Macro call to write dist_hub variable to config file for specified lane.  
  
Usage: ``SAVE_HUB_DIST LANE=<lane_name>``  
Example: ``SAVE_HUB_DIST LANE=lane1``  

### SAVE_SPEED_MULTIPLIER
_Description_: Macro call to write fwd_speed_multiplier and rwd_speed_multiplier variables to config file for specified lane.  
  
Usage: ``SAVE_SPEED_MULTIPLIER LANE=<lane_name>``  
Example: ``SAVE_SPEED_MULTIPLIER LANE=lane1``  

### SET_AFC_TOOLCHANGES
_Description_: This macro can be used to set total number of toolchanges from slicer. AFC will keep track of tool changes and print out
current tool change number when a T(n) command is called from gcode.  
The following call can be added to the slicer by adding the following lines to Change filament G-code section in your slicer.
You may already have `T[next_extruder]`, just make sure the toolchange call is after your T(n) call
```
T[next_extruder]
{ if toolchange_count == 1 }SET_AFC_TOOLCHANGES TOOLCHANGES=[total_toolchanges]{endif }
```
The following can also be added to your `PRINT_END` section in your slicer to set number of toolchanges back to zero
`SET_AFC_TOOLCHANGES TOOLCHANGES=0`  
  
Usage: ``SET_AFC_TOOLCHANGES TOOLCHANGES=<number>``  
Example: ``SET_AFC_TOOLCHANGES TOOLCHANGES=100``  

### SET_BOWDEN_LENGTH
_Description_: This function adjusts the length of the Bowden tube between the hub and the toolhead.
It retrieves the hub specified by the 'HUB' parameter and the length adjustment specified
by the 'LENGTH' parameter. UNLOAD_LENGTH adjusts unload Bowden length. If the hub is not specified
and a lane is currently loaded, it uses the hub of the current lane. To reset length back to config
value, pass in `reset` for each length to reset to value in config file. Adding +/- in front of the
length will increase/decrease bowden length by that amount.  
  
Usage: ``SET_BOWDEN_LENGTH HUB=<hub> LENGTH=<length> UNLOAD_LENGTH=<length>``  
Example: ``SET_BOWDEN_LENGTH HUB=Turtle_1 LENGTH=+100 UNLOAD_LENGTH=-100``  

### SET_BUFFER_MULTIPLIER
_Description_: This function handles the adjustment of the buffer multipliers for the turtleneck buffer.
It retrieves the multiplier type ('HIGH' or 'LOW') and the factor to be applied. The function
ensures that the factor is valid and updates the corresponding multiplier.  
  
Usage: `SET_BUFFER_MULTIPLIER BUFFER=<buffer_name> MULTIPLIER=<HIGH/LOW> FACTOR=<factor>`  
Example: `SET_BUFFER_MULTIPLIER BUFFER=TN MULTIPLIER=HIGH FACTOR=1.2`  

### SET_BUFFER_VELOCITY
_Description_: Allows users to tweak buffer velocity setting while printing. This setting is not
saved in configuration. Please update your configuration file once you find a velocity that
works for your setup.  
  
Usage: `SET_BUFFER_VELOCITY BUFFER=<buffer_name> VELOCITY=<value>`  
Example: `SET_BUFFER_VELOCITY BUFFER=TN2 VELOCITY=100`  

### SET_COLOR
_Description_: This function handles changing the color of a specified lane. It retrieves the lane
specified by the 'LANE' parameter and sets its color to the value provided by the 'COLOR' parameter.  
  
Usage: ``SET_COLOR LANE=<lane> COLOR=<color>``  
Example: ``SET_COLOR LANE=lane1 COLOR=FF0000``  

### SET_HUB_DIST
_Description_: This function adjusts the distance between a lanes extruder and hub. Adding +/- in front of the length will
increase/decrease length by that amount. To reset length back to config value, pass in `reset` for length to
reset to value in config file.  
  
Usage: ``SET_HUB_DIST LANE=<lane_name> LENGTH=+/-<fwd_multiplier>``  
Example: ``SET_HUB_DIST LANE=lane1 LENGTH=+100``  

### SET_LANE_LOADED
_Description_: This macro handles manually setting a lane loaded into the toolhead. This is useful when manually loading lanes
during prints after AFC detects an error when loading/unloading and pauses. If there is a lane already loaded this macro
will also desync that lane extruder from the toolhead extruder and set its values and led appropriately.  
Retrieves the lane specified by the 'LANE' parameter and set the appropriate values in AFC to continue using the lane.  
  
Usage: ``SET_LANE_LOADED LANE=<lane>``  
Example: ``SET_LANE_LOADED LANE=lane1``  

### SET_MAP
_Description_: This function handles changing the GCODE tool change command for a Lane.  
  
Usage: ``SET_MAP LANE=<lane> MAP=<cmd>``  
Example: ``SET_MAP LANE=lane1 MAP=T1``  

### SET_MATERIAL
_Description_: This function handles changing the material of a specified lane. It retrieves the lane
specified by the 'LANE' parameter and sets its material to the value provided by the 'MATERIAL' parameter.  
  
Usage: `SET_MATERIAL LANE=<lane> MATERIAL=<material>`  
Example: `SET_MATERIAL LANE=lane1 MATERIAL=ABS`  

### SET_ROTATION_FACTOR
_Description_: Adjusts the rotation distance of the current AFC stepper motor by applying a
specified factor. If no factor is provided, it defaults to 1.0, which resets
the rotation distance to the base value.  
  
Usage: `SET_ROTATION_FACTOR BUFFER=<buffer_name> FACTOR=<factor>`  
Example: `SET_ROTATION_FACTOR BUFFER=TN FACTOR=1.2`  

### SET_RUNOUT
_Description_: This function handles setting the runout lane (infinite spool) for a specified lane. It retrieves the lane
specified by the 'LANE' parameter and updates its the lane to use if filament runs out by untriggering prep sensor  
  
Usage: ``SET_RUNOUT LANE=<lane> RUNOUT=<lane>``  
Example: ``SET_RUNOUT LANE=lane1 RUNOUT=lane4``  

### SET_SPEED_MULTIPLIER
_Description_: Macro call to update fwd_speed_multiplier or rwd_speed_multiplier values without having to set in config and restart klipper. This macro allows adjusting
these values while printing. Multiplier values must be between 0.0 - 1.0  
    
Use FWD variable to set forward multiplier, use RWD to set reverse multiplier  
    
After running this command run SAVE_SPEED_MULTIPLIER LANE=<lane_name> to save value to config file  
  
Usage: ``SET_SPEED_MULTIPLIER LANE=<lane_name> FWD=<fwd_multiplier> RWD=<rwd_multiplier>``  
Example: ``SET_SPEED_MULTIPLIER LANE=lane1 RWD=0.9``  

### SET_SPOOL_ID
_Description_: This function handles setting the spool ID for a specified lane. It retrieves the lane
specified by the 'LANE' parameter and updates its spool ID, material, color, and weight
based on the information retrieved from the Spoolman API.  
  
Usage: ``SET_SPOOL_ID LANE=<lane> SPOOL_ID=<spool_id>``  
Example: ``SET_SPOOL_ID LANE=lane1 SPOOL_ID=12345``  

### SET_TIP_FORMING
_Description_: Sets the tip forming configuration
Unspecified ones are left unchanged. True boolean values (use_skinnydip) are specified as "true"
(case insensitive); every other values is considered as "false".
Note: this will not update the configuration file. To make settings permanent, update the configuration file
manually.  
  
Usage: `SET_TIP_FORMING PARAMETER=VALUE ...`  
Example: `SET_TIP_FORMING ramming_volume=20 toolchange_temp=220`  

### SET_WEIGHT
_Description_: This function handles changing the material of a specified lane. It retrieves the lane
specified by the 'LANE' parameter and sets its material to the value provided by the 'MATERIAL' parameter.  
  
Usage: `SET_WEIGHT LANE=<lane> WEIGHT=<weight>`  
Example: `SET_WEIGHT LANE=lane1 WEIGHT=850`  

### TEST
_Description_: This function tests the assist motors of a specified lane at various speeds.
It performs the following steps:
1. Retrieves the lane specified by the 'LANE' parameter.
2. Tests the assist motor at full speed, 50%, 30%, and 10% speeds.
3. Reports the status of each test step.  
  
Usage: ``TEST LANE=<lane>``  
Example: ``TEST LANE=lane1``  

### TEST_AFC_TIP_FORMING
_Description_: Gives ability to test AFC tip forming without doing a tool change  
  
Usage: `TEST_AFC_TIP_FORMING`  
Example: `TEST_AFC_TIP_FORMING`  

### TOOL_LOAD
_Description_: This function handles the loading of a specified lane into the tool. It retrieves
the lane specified by the 'LANE' parameter and calls the TOOL_LOAD method to perform
the loading process.  
Optionally setting PURGE_LENGTH parameter to pass a value into poop macro.  
  
Usage: ``TOOL_LOAD LANE=<lane> PURGE_LENGTH=<purge_length>(optional value)``  
Example: ``TOOL_LOAD LANE=lane1 PURGE_LENGTH=80``  

### TOOL_UNLOAD
_Description_: This function handles the unloading of a specified lane from the tool head. It retrieves
the lane specified by the 'LANE' parameter or uses the currently loaded lane if no parameter
is provided, and calls the TOOL_UNLOAD method to perform the unloading process.  
  
Usage: ``TOOL_UNLOAD LANE=<lane>``  
Example: ``TOOL_UNLOAD LANE=lane1``  

### TURN_OFF_AFC_LED
_Description_: This macro handles turning off all LEDs for AFC_led configurations. Color for LEDs are saved if colors are changed while they are turned off.  
  
Usage: ``TURN_OFF_AFC_LED``  
Example: ``TURN_OFF_AFC_LED``  

### TURN_ON_AFC_LED
_Description_: This macro handles turning on all LEDs for AFC_led configurations. LEDs are restored to last previous state.  
  
Usage: ``TURN_ON_AFC_LED``  
Example: ``TURN_ON_AFC_LED``  

### UNIT_BOW_CALIBRATION
_Description_: Open a prompt to calibrate the Bowden length for a specific lane in the selected unit. Provides buttons
for each lane, with a note to only calibrate one lane per unit.  
  
Usage: ``UNIT_CALIBRATION UNIT=<unit>``  
Example: ``UNIT_CALIBRATION UNIT=Turtle_1``  

### UNIT_CALIBRATION
_Description_: Open a prompt to calibrate either the distance between the extruder and the hub or the Bowden length
for the selected unit. Provides buttons for lane calibration, Bowden length calibration, and a back option.  
  
Usage: ``UNIT_CALIBRATION UNIT=<unit>``  
Example: ``UNIT_CALIBRATION UNIT=Turtle_1``  

### UNIT_LANE_CALIBRATION
_Description_: Open a prompt to calibrate the extruder-to-hub distance for each lane in the selected unit. Creates buttons
for each lane, grouped in sets of two, and allows calibration for all lanes or individual lanes.  
  
Usage: ``UNIT_LANE_CALIBRATION UNIT=<unit>``  
Example: ``UNIT_LANE_CALIBRATION UNIT=Turtle_1``  

### UNSET_LANE_LOADED
_Description_: Unsets current lane from AFC loaded status. Mainly this would be used if AFC thinks that there is a lane loaded into the toolhead
but nothing is actually loaded. Retrieves the lane specified by the 'LANE' parameter and set the appropriate values in AFC to continue using the lane.  
  
Usage: ``UNSET_LANE_LOADED``  
Example: ``UNSET_LANE_LOADED``  

### UPDATE_TOOLHEAD_SENSORS
_Description_: Macro call to adjust `tool_stn`\`tool_stn_unload`\`tool_sensor_after_extruder` lengths for specified extruder without having to update config file and restart klipper.  
  
`tool_stn length` is the length from the sensor before extruder gears (tool_start) to nozzle. If sensor after extruder gears(tool_end)
is set then the value if from tool_end sensor.  
  
`tool_stn_unload` length is the length to unload so that filament is not in extruder gears anymore.  
  
`tool_sensor_after_extruder` length is mainly used for those that have a filament sensor after extruder gears, target this
length to retract filament enough so that it's not in the extruder gears anymore.  
  
Please pause print if you need to adjust this value while printing  
  
Usage: ``UPDATE_TOOLHEAD_SENSORS EXTRUDER=<extruder> TOOL_STN=<length> TOOL_STN_UNLOAD=<length> TOOL_AFTER_EXTRUDER=<length>``  
Example: ``UPDATE_TOOLHEAD_SENSORS EXTRUDER=extruder TOOL_STN=100``  

## AFC Macros

The following macros are defined in the `config/macros/AFC_macros.cfg` file.
These macros can be executed either from the console, called from another macro, or triggered through 
the Mainsail or Fluidd web interfaces.

### BT_TOOL_UNLOAD
_Description_: Unload the currently loaded lane
### BT_CHANGE_TOOL
_Description_: Switch to a new lane by ejecting the previously loaded one
### BT_LANE_EJECT
_Description_: Fully eject the filament from the lane
### BT_LANE_MOVE
_Description_: Move the specified lane the specified amount
### BT_RESUME
_Description_: Resume the print after an error
### BT_PREP
_Description_: Run the AFC PREP sequence
