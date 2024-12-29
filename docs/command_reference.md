# AFC Klipper Add-On Command Reference

## Built-in AFC Functions

The following commands are built-in the AFC-Klipper-Add-On and are available through 
the Klipper console.

### SET_MULTIPLIER
_Description_: This function handles the adjustment of the buffer multipliers for the turtleneck buffer.
It retrieves the multiplier type ('HIGH' or 'LOW') and the factor to be applied. The function
ensures that the factor is valid and updates the corresponding multiplier.  
Usage: `SET_BUFFER_MULTIPLIER MULTIPLIER=<HIGH/LOW> FACTOR=<factor>`  
Example: `SET_BUFFER_MULTIPLIER MULTIPLIER=HIGH FACTOR=1.2`  

### SET_ROTATION_FACTOR
_Description_: Adjusts the rotation distance of the current AFC stepper motor by applying a
specified factor. If no factor is provided, it defaults to 1.0, which resets
the rotation distance to the base value.  
Usage: `SET_ROTATION_FACTOR FACTOR=<factor>`  
Example: `SET_ROTATION_FACTOR FACTOR=1.2`  

### QUERY_BUFFER
_Description_: Reports the current state of the buffer sensor and, if applicable, the rotation
distance of the current AFC stepper motor.  
Usage: `QUERY_BUFFER BUFFER=<buffer_name>`  
Example: `QUERY_BUFFER BUFFER=TN2`  

### SET_BUFFER_VELOCITY
_Description_: Allows users to tweak buffer velocity setting while printing. This setting is not
saved in configuration. Please update your configuration file once you find a velocity that
works for your setup.  
Usage: `SET_BUFFER_VELOCITY BUFFER=<buffer_name> VELOCITY=<value>`  
Example: `SET_BUFFER_VELOCITY BUFFER=TN2 VELOCITY=100`  

### CALIBRATE_AFC
_Description_: This function performs the calibration of the hub and Bowden length for one or more lanes within an AFC
(Automated Filament Changer) system. The function uses precise movements to adjust the positions of the
steppers, check the state of the hubs and tools, and calculate distances for calibration based on the
user-provided input. If no specific lane is provided, the function defaults to notifying the user that no lane has been selected. The function also includes
the option to calibrate the Bowden length for a particular lane, if specified.  
Usage: ``CALIBRATE_AFC LANE=<lane> DISTANCE=<distance> TOLERANCE=<tolerance> BOWDEN=<lane>``  
Example: `CALIBRATE_AFC LANE=leg1`  

### RESET_FAILURE
_Description_: This function clears the error state of the AFC system by setting the error state to False.  
Usage: ``RESET_FAILURE``  
Example: ``RESET_FAILURE``  

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

### SET_BOWDEN_LENGTH
_Description_: This function adjusts the length of the Bowden tube between the hub and the toolhead.
It retrieves the hub specified by the 'HUB' parameter and the length adjustment specified
by the 'LENGTH' parameter. If the hub is not specified and a lane is currently loaded,
it uses the hub of the current lane.  
Usage: ``SET_BOWDEN_LENGTH HUB=<hub> LENGTH=<length>``  
Example: ``SET_BOWDEN_LENGTH HUB=Turtle_1 LENGTH=100``  

### HUB_CUT_TEST
_Description_: This function tests the cutting sequence of the hub cutter for a specified lane.
It retrieves the lane specified by the 'LANE' parameter, performs the hub cut,
and responds with the status of the operation.  
Usage: ``HUB_CUT_TEST LANE=<lane>``  
Example: ``HUB_CUT_TEST LANE=leg1``  

### TEST
_Description_: This function tests the assist motors of a specified lane at various speeds.
It performs the following steps:
1. Retrieves the lane specified by the 'LANE' parameter.
2. Tests the assist motor at full speed, 50%, 30%, and 10% speeds.
3. Reports the status of each test step.  
Usage: ``TEST LANE=<lane>``  
Example: ``TEST LANE=leg1``  

### HUB_LOAD
_Description_: This function handles the loading of a specified lane into the hub. It performs
several checks and movements to ensure the lane is properly loaded.  
Usage: ``HUB_LOAD LANE=<lane>``  
Example: ``HUB_LOAD LANE=leg1``  

### LANE_UNLOAD
_Description_: This function handles the unloading of a specified lane from the extruder. It performs
several checks and movements to ensure the lane is properly unloaded.  
Usage: ``LANE_UNLOAD LANE=<lane>``  
Example: ``LANE_UNLOAD LANE=leg1``  

### TOOL_LOAD
_Description_: This function handles the loading of a specified lane into the tool. It retrieves
the lane specified by the 'LANE' parameter and calls the TOOL_LOAD method to perform
the loading process.  
Usage: ``TOOL_LOAD LANE=<lane>``  
Example: ``TOOL_LOAD LANE=leg1``  

### TOOL_UNLOAD
_Description_: This function handles the unloading of a specified lane from the tool head. It retrieves
the lane specified by the 'LANE' parameter or uses the currently loaded lane if no parameter
is provided, and calls the TOOL_UNLOAD method to perform the unloading process.  
Usage: ``TOOL_UNLOAD [LANE=<lane>]``  
Example: ``TOOL_UNLOAD LANE=leg1``  

### CHANGE_TOOL
_Description_: This function handles the tool change process. It retrieves the lane specified by the 'LANE' parameter,
checks the filament sensor, saves the current position, and performs the tool change by unloading the
current lane and loading the new lane.  
Usage: ``CHANGE_TOOL LANE=<lane>``  
Example: ``CHANGE_TOOL LANE=leg1``  

### TEST_AFC_TIP_FORMING
_Description_: Gives ability to test AFC tip forming without doing a tool change  
Usage: `TEST_AFC_TIP_FORMING`  
Example: `TEST_AFC_TIP_FORMING LANE=leg1`  

### GET_TIP_FORMING
_Description_: Shows the tip forming configuration  
Usage: `GET_TIP_FORMING`  
Example: `GET_TIP_FORMING LANE=leg1`  

### SET_TIP_FORMING
_Description_: Sets the tip forming configuration  
Usage: `SET_TIP_FORMING PARAMETER=VALUE ...`  
Example: `SET_TIP_FORMING ramming_volume=20 toolchange_temp=220`  

### SET_MAP
_Description_: This function handles changing the GCODE tool change command for a Lane.  
Usage: ``SET_MAP LANE=<lane> MAP=<cmd>``  
Example: ``SET_MAP LANE=leg1 MAP=T1``  

### SET_COLOR
_Description_: This function handles changing the color of a specified lane. It retrieves the lane
specified by the 'LANE' parameter and sets its color to the value provided by the 'COLOR' parameter.  
Usage: ``SET_COLOR LANE=<lane> COLOR=<color>``  
Example: ``SET_COLOR LANE=leg1 COLOR=FF0000``  

### SET_WEIGHT
_Description_: This function handles changing the material of a specified lane. It retrieves the lane
specified by the 'LANE' parameter and sets its material to the value provided by the 'MATERIAL' parameter.  
Usage: `SET_WEIGHT LANE=<lane> WEIGHT=<weight>`  
Example: `SET_WEIGHT LANE=leg1 WEIGHT=850`  

### SET_MATERIAL
_Description_: This function handles changing the material of a specified lane. It retrieves the lane
specified by the 'LANE' parameter and sets its material to the value provided by the 'MATERIAL' parameter.  
Usage: `SET_MATERIAL LANE=<lane> MATERIAL=<material>`  
Example: `SET_MATERIAL LANE=leg1 MATERIAL=ABS`  

### SET_SPOOLID
_Description_: This function handles setting the spool ID for a specified lane. It retrieves the lane
specified by the 'LANE' parameter and updates its spool ID, material, color, and weight
based on the information retrieved from the Spoolman API.  
Usage: ``SET_SPOOLID LANE=<lane> SPOOL_ID=<spool_id>``  
Example: ``SET_SPOOLID LANE=leg1 SPOOL_ID=12345``  

### SET_RUNOUT
_Description_: This function handles setting the runout lane (infanet spool) for a specified lane. It retrieves the lane
specified by the 'LANE' parameter and updates its the lane to use if filament is empty
based on the information retrieved from the Spoolman API.  
Usage: ``SET_RUNOUT LANE=<lane> RUNOUT=<lane>``  
Example: ``SET_RUNOUT LANE=lane1 RUNOUT=lane4``  

### RESET_AFC_MAPPING
_Description_: This commands resets all tool lane mapping to the order that is setup in configuration.  
Usage: `RESET_AFC_MAPPING`  
Example: `RESET_AFC_MAPPING LANE=leg1`  

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
