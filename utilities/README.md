### generate_docs.py

This utility will parse the functions in the AFC code that begin with `cmd_` and generate
docs based on their docstring.

For example, the following function: 

```python
    def cmd_AFC_RESUME(self, gcmd):
        """
        This function clears the error state of the AFC system, sets the in_toolchange flag to False,
        runs the resume script, and restores the toolhead position to the last saved position.

        Usage: `AFC_RESUME`
        Example: `AFC_RESUME`

        Args:
            gcmd: The G-code command object containing the parameters for the command.

        Returns:
            None
        """
        self.set_error_state(False)
        self.in_toolchange = False
        self.gcode.run_script_from_command(self.AFC_RENAME_RESUME_NAME)
        self.restore_pos()
```

Will result in the following documentation being generated:

```markdown
### AFC_RESUME
_Description_: This function clears the error state of the AFC system, sets the in_toolchange flag to False,
runs the resume script, and restores the toolhead position to the last saved position.  
Usage: ``AFC_RESUME``  
Example: ``AFC_RESUME`` 
```

Adding `NO_DOC: True` in the docstring will cause no documentation to be generated such as in

```python
    def cmd_LANE_MOVE(self, gcmd):
        """
        This function handles the manual movement of a specified lane. It retrieves the lane
        specified by the 'LANE' parameter and moves it by the distance specified by the 'DISTANCE' parameter.

        Usage: `LANE_MOVE LANE=<lane> DISTANCE=<distance>`
        Example: `LANE_MOVE LANE=lane1 DISTANCE=100`

        Args:
            gcmd: The G-code command object containing the parameters for the command.
                  Expected parameters:
                  - LANE: The name of the lane to be moved.
                  - DISTANCE: The distance to move the lane.

        NO_DOC: True

        Returns:
            None
        """
        lane = gcmd.get('LANE', None)
        distance = gcmd.get_float('DISTANCE', 0)
        CUR_LANE = self.printer.lookup_object('AFC_stepper ' + lane)
        CUR_LANE.move(distance, self.short_moves_speed, self.short_moves_accel)
```

This utility will also parse the macros in `config/macros/AFC_macros` and generate a short description
based on the description in the macro.

This should be run any time there is significant changes to the docstrings.
