#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

function auto_update() {
  check_and_append_prep "${AFC_CONFIG_PATH}/AFC.cfg"
  # merge_configs "${AFC_CONFIG_PATH}/AFC_Hardware.cfg" "${AFC_PATH}/templates/AFC_Hardware-AFC.cfg" "${AFC_CONFIG_PATH}/AFC_Hardware-temp.cfg"
  # cleanup_blank_lines "${AFC_CONFIG_PATH}/AFC_Hardware-temp.cfg"
  # mv "${AFC_CONFIG_PATH}/AFC_Hardware-temp.cfg" "${AFC_CONFIG_PATH}/AFC_Hardware.cfg"
}