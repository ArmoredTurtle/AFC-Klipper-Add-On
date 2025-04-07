## Setting up hotend specific values

Some of the values with AFC are extremely dependent on your hotend.

Suggested starting values for hotend types (more to be added later) are below.  `tool_stn` and `tool_stn_unload` 
are in `AFC/AFC_Hardware.cfg`, `variable_retract_length` and `variable_pushback_length` are in
`AFC/AFC_Macro_Vars.cfg`. For `tool_stn`, if you have `pin_tool_end` defined, use the second value; otherwise, use
the first value. You may need to increase this value if you are using a ram buffer as the toolhead sensor.

### Hotend specific values

=== "Revo Voron"

    - `tool_stn`: 52 (if `pin_tool_end` is NOT defined) / 29 (if `pin_tool_end` is defined)
    - `tool_stn_unload`: 62
    - `variable_retract_length`: 22
    - `variable_pushback_length`: 20

=== "Rapido HF"

    - `tool_stn`: 64.1 (if `pin_tool_end` is NOT defined) / 41.1 (if `pin_tool_end` is defined)
    - `tool_stn_unload`: 105.9
    - `variable_retract_length`: 10
    - `variable_pushback_length`: 10

=== "Rapido V2 HF"
    
    - `tool_stn`: 74 (if `pin_tool_end` is NOT defined) / 52 (if `pin_tool_end` is defined)
    - `tool_stn_unload`: 81
    - `variable_retract_length`: 25
    - `variable_pushback_length`: 20

