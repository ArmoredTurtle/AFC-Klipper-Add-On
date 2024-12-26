#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

# Paths
KLIPPER_PATH="${HOME}/klipper"
MOONRAKER_PATH="${HOME}/printer_data/config"
AFC_PATH="${HOME}/AFC-Klipper-Add-On"
PRINTER_CONFIG_PATH="${HOME}/printer_data/config"
AFC_CONFIG_PATH="${PRINTER_CONFIG_PATH}/AFC"

# Interface specific paths
MAINSAIL_SRC="$AFC_PATH/software/mainsail-afc.zip"
FLUIDD_SRC="$AFC_PATH/software/mainsail-afc.zip"
MAINSAIL_DST="$HOME/mainsail"
FLUIDD_DST="$HOME/fluidd"

# Variables
KLIPPER_SERVICE=klipper
GITREPO="https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git"
PRIOR_INSTALLATION=False
UPDATE_CONFIG=False
AUTO_UPDATE_CONFIG=False
UNINSTALL=False
BRANCH=main

# This FORCE_UPDATE variable is used to force an update of the AFC configuration files. This would typically be used
# when there are major changes to the AFC configuration files that require more changes than we can handle automatically.
# Anything before 1.0.0 or if it isn't defined will cause the FORCE_UPDATE to be TRUE
CURRENT_INSTALL_VERSION="1.0.0"
MIN_VERSION="1.0.0"
FORCE_UPDATE=True
BACKUP_DATE=$(date +%Y%m%d%H%M%S)


# Moonraker Config
MOONRAKER_UPDATE_CONFIG="""
[update_manager afc-software]
type: git_repo
path: ~/AFC-Klipper-Add-On
origin: $GITREPO
managed_services: klipper
primary_branch: $BRANCH
info_tags:
    desc=AFC Klipper Add On
"""
