#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.


# Path related constants
printer_config_dir="$HOME/printer_data/config"
klipper_dir="$HOME/klipper"
afc_path="$HOME/AFC-Klipper-Add-On"
afc_config_dir="$printer_config_dir/AFC"
afc_file="$afc_config_dir/AFC.cfg"
moonraker_config_file="$printer_config_dir/moonraker.conf"

# Service related constants
klipper_service="klipper"

# Git related constants
gitrepo="https://github.com/ejsears/AFC-Klipper-Add-On.git"
branch="install-script-redesign"

# Misc constants
prior_installation="False"
installation_type="BoxTurtle"
uninstall="False"
force_update="True"
backup_date=$(date +%Y%m%d%H%M%S)
current_install_version="1.0.0"
min_version="1.0.0"
files_updated_or_installed="False"
test_mode="False"

# AFC default configs
park_macro="True"
poop_macro="True"
afc_includes="True"
tip_forming="True"
toolhead_cutter="True"
hub_cutter="False"
kick_macro="True"
wipe_macro="True"
installation_type="BoxTurtle"
toolhead_sensor="Sensor"
toolhead_sensor_pin="Unknown"
buffer_type="TurtleNeck"


# Moonraker Config
moonraker_update_config="""
[update_manager afc-software]
type: git_repo
path: ~/AFC-Klipper-Add-On
origin: $gitrepo
managed_services: $klipper_service
primary_branch: main
is_system_service: False
info_tags:
    desc=AFC Klipper Add On
"""
