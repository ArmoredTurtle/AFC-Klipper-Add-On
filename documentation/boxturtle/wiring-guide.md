# BoxTurtle Wiring Guide

## Lane numbering

Lane 1 = leftmost filament lane\
Lane 4  = rightmost filament lane

## AFC-Lite Wiring guide

Prep = Trigger Filament Sensor Switches\
Load = Extruder Filament Sensor Switches

![BoxTurtle_AFC-Lite_Pinout](../assets/images/boxturtle-afc-lite-pinout.png)

**NOTE**: You need to connect 24V and GND to the CAN bus port pins even if you are connecting using USB-C for data transmission. The AFC-Lite PCB does not support USB Power Delivery.

## Extruder Steppers
| Lane | Recommended Wire Length | Recommended Wire Gauge | Connector |
| ---- | ----------- | --------- | ------------|
| Lane 1 | 210mm | Dependent on motor | JST-XH-4 |
| Lane 2 | 320mm | Dependent on motor | JST-XH-4 |
| Lane 3 | 420mm | Dependent on motor | JST-XH-4 |
| Lane 4 | 520mm | Dependent on motor | JST-XH-4 |

##  Indicator LEDs
The default configuration of the LED indicators is to create a neopixel chain of 4 LEDs, using DOUT on one LED to go to DIN of the next LED. JST-SM connectors are spec'd to provide easy disconnect for lane service, but any wire-to-wire connector can be used in their place (e.g. Molex Microfit 3).

| Lane | Component                                     | Recommended Wire Length | Recommended Wire Gauge | Connector                                               |
| ---- |-----------------------------------------------| --------- | ------------|---------------------------------------------------------|
| Lane 1 | [WS2812 PCB](../assets/images/WS2812_PCB.png) | 130mm/130mm tail | 26-30ga | [JST-SM-M](../assets/images/JST-XH_JST-SM.png)/JST-SM-F |
| Lane 2 | [WS2812 PCB](../assets/images/WS2812_PCB.png)                 | 130mm/130mm tail | 26-30ga | [JST-SM-M](../assets/images/JST-XH_JST-SM.png)/JST-SM-F                  |
| Lane 3 | [WS2812 PCB](../assets/images/WS2812_PCB.png)                  | 130mm/130mm tail | 26-30ga | [JST-SM-M](../assets/images/JST-XH_JST-SM.png)/JST-SM-F                  |
| Lane 4 | [WS2812 PCB](../assets/images/WS2812_PCB.png)                  | 130mm/130mm tail | 26-30ga | [JST-SM-M](../assets/images/JST-XH_JST-SM.png)/JST-SM-F                  |
| Jumper |                                               |  80mm | 26-30ga | JST-XH-3/JST-SM-F                                       |

##  N20 motors for Respoolers
| Lane | Component                                           | Recommended Wire Length | Recommended Wire Gauge | Connector |
| ---- |-----------------------------------------------------| --------- | ------------| --------- |
| Lane 1 | [N20 6V 500RPM](../assets/images/N20_6V_500RPM.png) | 205mm | 26ga | JST-XH-2 |
| Lane 2 | [N20 6V 500RPM](../assets/images/N20_6V_500RPM.png)                  | 315mm | 26ga | JST-XH-2 |
| Lane 3 | [N20 6V 500RPM](../assets/images/N20_6V_500RPM.png)                  | 415mm | 26ga | JST-XH-2 |
| Lane 4 | [N20 6V 500RPM](../assets/images/N20_6V_500RPM.png)                  | 515mm | 26ga | JST-XH-2 |

## Trigger (PREP) sensors
| Lane | Component | Recommended Wire Length | Recommended Wire Gauge | Connector |
| ---- | ----------- | --------- | ------------| --------- |
| Lane 1 | [D2F-L w/ Lever](../assets/images/D2F_W-Lever.png) | 155mm | 26ga | JST-XH-3 |
| Lane 2 | [D2F-L w/ Lever](../assets/images/D2F_W-Lever.png) | 235mm | 26ga | JST-XH-3|
| Lane 3 | [D2F-L w/ Lever](../assets/images/D2F_W-Lever.png) | 335mm | 26ga | JST-XH-3 |
| Lane 4 | [D2F-L w/ Lever](../assets/images/D2F_W-Lever.png) | 435mm | 26ga | JST-XH-3 |

## Extruder (LOAD) sensors
| Lane | Component | Recommended Wire Length | Recommended Wire Gauge | Connector |
| ---- | ----------- | --------- | ------------| --------- |
| Lane 1 | [D2HW-C201](../assets/images/D2HW-C201H.png) | 200mm | 26ga | JST-XH-3 |
| Lane 2 | [D2HW-C201](../assets/images/D2HW-C201H.png) | 310mm | 26ga | JST-XH-3 |
| Lane 3 | [D2HW-C201](../assets/images/D2HW-C201H.png) | 410mm | 26ga | JST-XH-3 |
| Lane 4 | [D2HW-C201](../assets/images/D2HW-C201H.png) | 465mm | 26ga | JST-XH-3 |

## Hub (HUB) sensor
| Component | Recommended Wire Length | Recommended Wire Gauge | Connector |
| ----------- | --------- | ------------| --------- |
| [D2HW-C201](../assets/images/D2HW-C201H.png) | 510mm | 26ga | JST-XH-3 |

## TurtleNeck (TN) sensors
| Component | Recommended Wire Length | Recommended Wire Gauge | Connector | Notes |
| ----------- | --------- | ------------| --------- | ---- |
| [D2F-L w/ Lever](../assets/images/TN_D2L_500_X2.png)  | 500mm | 26ga | JST-XH-3 | Quantity 2 |