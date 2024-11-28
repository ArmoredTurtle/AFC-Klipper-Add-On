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


check_version_and_set_force_update() {
  local version_file=".afc-version"
  local min_version="1.0.0"
  local current_version

  if [[ -f "$version_file" ]]; then
    current_version=$(grep -oP '(?<=AFC_VERSION=)[0-9]+\.[0-9]+\.[0-9]+' "$version_file")
  fi

  if [[ -z "$current_version" || "$current_version" < "$min_version" ]]; then
    FORCE_UPDATE=True
  else
    FORCE_UPDATE=False
  fi
}