#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

function auto_update() {
  check_and_append_prep "${AFC_CONFIG_PATH}/AFC.cfg"
  remove_t_macros
  # merge_configs "${AFC_CONFIG_PATH}/AFC_Hardware.cfg" "${AFC_PATH}/templates/AFC_Hardware-AFC.cfg" "${AFC_CONFIG_PATH}/AFC_Hardware-temp.cfg"
  # cleanup_blank_lines "${AFC_CONFIG_PATH}/AFC_Hardware-temp.cfg"
  # mv "${AFC_CONFIG_PATH}/AFC_Hardware-temp.cfg" "${AFC_CONFIG_PATH}/AFC_Hardware.cfg"
}

check_old_config_version() {
  local config_file="${AFC_CONFIG_PATH}/AFC.cfg"

  # Check if the configuration file exists
  if [[ ! -f "$config_file" ]]; then
    FORCE_UPDATE=False
    FORCE_UPDATE_NO_VERSION=False
    return
  fi

  # Check if 'Type: Box_Turtle' is found in the first 15 lines of the file
  if head -n 15 "$config_file" | grep -v '^\s*#' | grep -q 'Type: Box_Turtle'; then
    FORCE_UPDATE=True
    # Since we have software without an AFC_INSTALL_VERSION in it, we need a way to designate this as a version that needs to be updated.
    FORCE_UPDATE_NO_VERSION=True
  else
    FORCE_UPDATE=False
    FORCE_UPDATE_NO_VERSION=False
  fi
}

set_install_version_if_missing() {
  local version_file="${AFC_CONFIG_PATH}/.afc-version"

  # Check if the version file exists
  if [[ ! -f "$version_file" ]]; then
    return
  fi

  # Check if 'AFC_INSTALL_VERSION' is missing and add it if necessary
  if ! grep -q 'AFC_INSTALL_VERSION' "$version_file"; then
    if ! echo "AFC_INSTALL_VERSION=$CURRENT_INSTALL_VERSION" > "$version_file"; then
      echo "Error: Failed to write to version file '$version_file'."
      return 1
    fi
  fi
}

check_version_and_set_force_update() {
  local version_file="${AFC_CONFIG_PATH}/.afc-version"
  local current_version

  if [[ -f $version_file ]]; then
    current_version=$(grep -oP '(?<=AFC_INSTALL_VERSION=)[0-9]+\.[0-9]+\.[0-9]+' "$version_file")
  fi

  if [[ -z "$current_version" || "$current_version" < "$MIN_VERSION" ]]; then
    FORCE_UPDATE=True
  else
    FORCE_UPDATE=False
  fi
}