---
Title: Boxturtle Initial Startup Guide Overview
---

# BoxTurtle Initial Startup & Commissioning Guide

The following guide will help you on the journey to multicolor printing after you have physically completed
the [assembly of your BoxTurtle](https://armoredturtle.xyz).

## Prerequisites

### Calibrate/tune existing printer extruder

If you are installing this on a new printer or extruder (
including [FilamATrix](https://github.com/thunderkeys/FilamATrix)) ensure you have calibrated your printer/extruder
before introducing AFC/multicolor printing. If your extruder rotation distance is off by a large factor, this will cause
issues with defining values such as `tool_stn` and others later on in the configuration.

It is a lot easier to do some of the calibrations (such as rotation distance) *BEFORE* installing your BoxTurtle.

Our recommended guide to follow for calibration
is [Ellis' Print Tuning Guide](https://ellis3dp.com/Print-Tuning-Guide/).

### Ensure minimum system requirements

The AFC Klipper Add-On requires a minimum Klipper/Kalico version of 0.12.0, as well as a corresponding klippy-env python
environment at least 3.x.

If you are on Klipper/Kalico 12, but running `~/klippy-env/bin/python --version` returns version 2.7.x, you can
recreate it with the following.

```
sudo service klipper stop

mv ~/klippy-env ~/klippy-env2.7
virtualenv -p python3 ~/klippy-env
~/klippy-env/bin/pip install -r ~/klipper/scripts/klippy-requirements.txt

sudo service klipper start
```

After recreating it, you may need to reinstall any custom add-ons, such as Klippain Shake&Tune, TMC Autotune, etc.

Ensure you have a clean, functioning klipper install with all of these minimum requirements met before proceeding to the
next step.