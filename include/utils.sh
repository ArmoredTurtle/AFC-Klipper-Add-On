#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

function clone_repo() {
  # Function to clone the AFC Klipper Add-On repository if it is not already cloned.
  # Uses the global variables:
  #   - AFC_PATH: The path where the repository should be cloned.
  #   - GITREPO: The URL of the repository to clone.
  #   - BRANCH: The branch to check out after cloning or pulling the repository.

  local afc_dir_name afc_base_name
  afc_dir_name="$(dirname "${AFC_PATH}")"
  afc_base_name="$(basename "${AFC_PATH}")"

  if [ ! -d "${AFC_PATH}" ]; then
    echo "Cloning AFC Klipper Add-On repo..."
    if git -C $afc_dir_name clone --quiet $GITREPO $afc_base_name; then
      print_msg INFO "AFC Klipper Add-On repo cloned successfully"
      pushd "${AFC_PATH}" || exit
      git checkout --quiet "${BRANCH}"
      popd || exit
    else
      print_msg ERROR "Failed to clone AFC Klipper Add-On repo"
      exit 1
    fi
  else
    pushd "${AFC_PATH}" || exit
    git pull --quiet
    git checkout --quiet "${BRANCH}"
    popd || exit
  fi
}

backup_afc_config() {
  # Function to back up the existing AFC configuration.
  # Arguments:
  #   - AFC_CONFIG_PATH: The path to the AFC configuration directory.
  #   - PRINTER_CONFIG_PATH: The path to the printer configuration directory.

  if [ -d "${AFC_CONFIG_PATH}" ]; then
    print_msg INFO "Backing up existing AFC config..."
    pushd "${PRINTER_CONFIG_PATH}" || exit
    mv AFC AFC.backup."$(date +%Y%m%d%H%M%S)"
    popd || exit
  fi
}

restart_service() {
  # Function to restart a given service.
  # Arguments:
  #   $1 - The name of the service to restart.

  local service_name=$1
  print_msg INFO "Restarting ${service_name} service..."
  if command -v systemctl &> /dev/null; then
    sudo systemctl restart "${service_name}"
  else
    sudo service "${service_name}" restart
  fi
}


function copy_config() {
  if [ -d "${AFC_CONFIG_PATH}" ]; then
    mkdir -p "${AFC_CONFIG_PATH}"
  fi
  print_msg INFO "  Copying AFC config files..."
  cp -R "${AFC_PATH}/config" "${AFC_CONFIG_PATH}"
}


pushd() {
  command pushd "$@" >/dev/null
}

popd() {
  command popd >/dev/null
}