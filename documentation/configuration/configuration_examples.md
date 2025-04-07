# Configuration Examples

The following examples provide a starting point for configuring the AFC-Klipper-Add-On. These examples are intended to be
a guide and may need to be adjusted based on your specific setup and requirements.

## Example 1: Basic Configuration

This example illustrates the use of a single BoxTurtle unit with 4 lanes and a single hub.

``` mermaid
stateDiagram-v2
    state "Lane1" as L1
    state "Lane2" as L2
    state "Lane3" as L3
    state "Lane4" as L4

    state "Hub1" as H1
    state "Buffer" as T
    state "Toolhead" as TH

    L1 --> H1
    L2 --> H1
    L3 --> H1
    L4 --> H1

    H1 --> T
    T --> TH

    %% Adding styles for colors and text visibility
    style L1 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L2 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L3 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L4 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style H1 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style T fill:#dda0dd,stroke:#000000,stroke-width:2px,color:#000000
    style TH fill:#4d75b3,stroke:#000000,stroke-width:2px,color:#000000
``` 

### [AFC_Turtle_1.cfg]

``` cfg
[AFC_stepper lane1]
unit: Turtle_1:1
...
[AFC_stepper lane4]
...
[AFC_hub Turtle_1]
switch_pin: ^turtleneck:PB6
...
```

## Example 2: Multiple Box Turtles

This example illustrates the use of two BoxTurtle units, each with 4 lanes and a single hub.

``` mermaid
stateDiagram-v2
    state "Lane1" as L1
    state "Lane2" as L2
    state "Lane3" as L3
    state "Lane4" as L4
    state "Lane5" as L5
    state "Lane6" as L6
    state "Lane7" as L7
    state "Lane8" as L8

    state "Hub1" as H1
    state "Hub2" as H2
    state "Combiner" as C
    state "Buffer" as T
    state "Toolhead" as TH

    L1 --> H1
    L2 --> H1
    L3 --> H1
    L4 --> H1
    L5 --> H2
    L6 --> H2
    L7 --> H2
    L8 --> H2

    H1 --> C
    H2 --> C
    C --> T
    T --> TH

    %% Adding styles for colors and text visibility
    style L1 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L2 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L3 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L4 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L5 fill:#794db3,stroke:#000000,stroke-width:2px,color:#000000
    style L6 fill:#794db3,stroke:#000000,stroke-width:2px,color:#000000
    style L7 fill:#794db3,stroke:#000000,stroke-width:2px,color:#000000
    style L8 fill:#794db3,stroke:#000000,stroke-width:2px,color:#000000
    style H1 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style H2 fill:#794db3,stroke:#000000,stroke-width:2px,color:#000000
    style C fill:#9e7283,stroke:#000000,stroke-width:2px,color:#000000
    style T fill:#dda0dd,stroke:#000000,stroke-width:2px,color:#000000
    style TH fill:#4d75b3,stroke:#000000,stroke-width:2px,color:#000000
```    

### [AFC_Turtle_1.cfg]

``` cfg
[AFC_stepper lane1]
unit: Turtle_1:1
...
[AFC_stepper lane4]
...
[AFC_hub Turtle_1]
switch_pin: ^turtleneck:PB6
...
```

### [AFC_Turtle_2.cfg]
``` cfg
[AFC_stepper lane5]
unit: Turtle_2:5
hub: Turtle_2
...
[AFC_stepper lane8]
unit: Turtle_2:8
hub: Turtle_2
...

[AFC_hub Turtle_2]
switch_pin: ^turtleneck:PB7
...

```
## Example 3: Advanced Configuration

This example illustrates the use of an 8 lane BoxTurtle that is set up with multiple **external** hubs.

``` mermaid
stateDiagram-v2
    Lane1 --> Hub1
    Lane2 --> Hub1
    Lane3 --> Hub1
    Lane4 --> Hub1
    Lane5 --> Hub2
    Lane6 --> Hub2
    Lane7 --> Hub2
    Lane8 --> Hub2

    Hub1 --> Combiner
    Hub2 --> Combiner
    Combiner --> Buffer
    Buffer --> Toolhead

    %% Adding styles for colors and text visibility
    style Lane1 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style Lane2 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style Lane3 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style Lane4 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style Lane5 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style Lane6 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style Lane7 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style Lane8 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style Hub1 fill:#34402d,stroke:#000000,stroke-width:2px,color:#000000
    style Hub2 fill:#794db3,stroke:#000000,stroke-width:2px,color:#000000
    style Combiner fill:#9e7283,stroke:#000000,stroke-width:2px,color:#000000
    style Buffer fill:#dda0dd,stroke:#000000,stroke-width:2px,color:#000000
    style Toolhead fill:#4d75b3,stroke:#000000,stroke-width:2px,color:#000000
```

An abbreviated portion of the relevant configuration files is shown below to illustrate the above setup.

In the below configuration example, we are setting the first 4 lanes without a `hub` parameter, and the last 4 lanes 
with a `hub` parameter. Since no `hub` parameter is specified for the first 4 lanes, they will be using the default.

For the default, the system will match the `hub` that matches the `unit` name. In this case, the default hub is
`Turtle_1`, which is the first hub in the example. The last 4 lanes are using `hub2` as their hub.

### [AFC_Turtle_1.cfg]

```cfg

[AFC_stepper lane1]
unit: Turtle_1:1
...
[AFC_stepper lane4]
...

[AFC_stepper lane5]
unit: Turtle_1:5
hub: hub2
...
[AFC_stepper lane8]
unit: Turtle_1:8
hub: hub2

[AFC_hub Turtle_1]
switch_pin: ^turtleneck:PB6
...

[AFC_hub hub2]
switch_pin: ^turtleneck:PB7
```

## Example 4: Different Unit Types

This example illustrates the use of different unit types, such as a BoxTurtle and 2 NightOwls.

``` mermaid
stateDiagram-v2
    state "Lane1" as L1
    state "Lane2" as L2
    state "Lane3" as L3
    state "Lane4" as L4
    state "Lane5" as L5
    state "Lane6" as L6
    state "Lane7" as L7
    state "Lane8" as L8

    state "Hub1" as H1
    state "Hub2" as H2
    state "Hub3" as H3
    state "Combiner" as C
    state "Buffer" as T
    state "Toolhead" as TH

    L1 --> H1
    L2 --> H1
    L3 --> H1
    L4 --> H1
    L5 --> H2
    L6 --> H2
    L7 --> H3
    L8 --> H3

    H1 --> C
    H2 --> C
    H3 --> C
    C --> T
    T --> TH

    %% Adding styles for colors and text visibility
    style L1 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L2 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L3 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L4 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style L5 fill:#794db3,stroke:#000000,stroke-width:2px,color:#000000
    style L6 fill:#794db3,stroke:#000000,stroke-width:2px,color:#000000
    style L7 fill:#4a4518,stroke:#000000,stroke-width:2px,color:#000000
    style L8 fill:#4a4518,stroke:#000000,stroke-width:2px,color:#000000
    style H1 fill:#54534e,stroke:#000000,stroke-width:2px,color:#000000
    style H2 fill:#794db3,stroke:#000000,stroke-width:2px,color:#000000
    style H3 fill:#4a4518,stroke:#000000,stroke-width:2px,color:#000000
    style C fill:#9e7283,stroke:#000000,stroke-width:2px,color:#000000
    style T fill:#dda0dd,stroke:#000000,stroke-width:2px,color:#000000
    style TH fill:#4d75b3,stroke:#000000,stroke-width:2px,color:#000000
```  

This is a similar setup to [Example 3](#example-3-advanced-configuration), but with different unit types.

An abbreviated portion of the relevant configuration files is shown below to illustrate the above setup.

In the below configuration example, we are setting the first 4 lanes without a `hub` parameter, and the next 2 
groups of 2 lanes each with a different `hub` parameter. Since no `hub` parameter is specified for the first 4 lanes, 
they will be using the default.

For the default, the system will match the `hub` that matches the `unit` name. In this case, the default hub is
`Turtle_1`, which is the first hub in the example. Each set of the last 2 lanes is using a different hub such as 
`NightOwl_1` and `NightOwl_2`.

### [AFC_Turtle_1.cfg]

```cfg

[AFC_stepper lane1]
unit: Turtle_1:1
...
[AFC_stepper lane4]
...
[AFC_hub Turtle_1]
switch_pin: ^turtleneck:PB6
...
```

### [AFC_NightOwl_1.cfg]

```cfg
[AFC_stepper lane5]
unit: NightOwl_1:5
hub: NightOwl_1
...
[AFC_stepper lane6]
unit: NightOwl_1:6
hub: NightOwl_1
...
[AFC_hub NightOwl_1]
switch_pin: ^turtleneck:PB7
...
```

### [AFC_NightOwl_2.cfg]

```cfg
[AFC_stepper lane7]
unit: NightOwl_2:7
hub: NightOwl_2
...
[AFC_stepper lane8]
unit: NightOwl_8:8
hub: NightOwl_2

[AFC_hub NightOwl_2]
switch_pin: ^turtleneck:PB8
...
```
