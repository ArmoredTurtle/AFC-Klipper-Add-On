# ruff: noqa: F841
# BOX Turtle Plug and Play
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

def load_config_prefix(config):
    unit = config.get_name().split()[-1]
    mcu = config.get('mcu_id')
    lane_count = config.getfloat('lane_count')
    hub = config.getboolean('Turtle_hub')
    Temp_Mon = config.getboolean('Monitor_Temp')



