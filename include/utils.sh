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
    print_msg INFO "  Backing up existing AFC config..."
    pushd "${PRINTER_CONFIG_PATH}" || exit
    mv AFC AFC.backup."$BACKUP_DATE"
    popd || exit
  fi
}

backup_afc_config_copy() {
  # Function to back up the existing AFC configuration.
  # Arguments:
  #   - AFC_CONFIG_PATH: The path to the AFC configuration directory.
  #   - PRINTER_CONFIG_PATH: The path to the printer configuration directory.

  if [ -d "${AFC_CONFIG_PATH}" ]; then
    print_msg INFO "  Backing up existing AFC config..."
    pushd "${PRINTER_CONFIG_PATH}" || exit
    cp -R AFC AFC.backup."$BACKUP_DATE"
    popd || exit
  fi
}

restart_service() {
  # Function to restart a given service.
  # Arguments:
  #   $1 - The name of the service to restart.

  local service_name=$1
  print_msg INFO "  Restarting ${service_name} service..."
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

backup_mainsail() {
  # Function to back up the existing Mainsail configuration.
  # Arguments:
  #   - MAINSAIL_DST: The path to the Mainsail configuration directory.

  if [ -d "${MAINSAIL_DST}" ]; then
    print_msg INFO "  Backing up existing Mainsail config..."
    pushd "${HOME}" || exit
    mv mainsail mainsail.backup."$BACKUP_DATE"
    popd || exit
  fi
}

backup_fluidd() {
  # Function to back up the existing Fluidd configuration.
  # Arguments:
  #   - FLUIDD_DST: The path to the Fluidd configuration directory.

  if [ -d "${FLUIDD_DST}" ]; then
    print_msg INFO "  Backing up existing Fluidd config..."
    pushd "${HOME}" || exit
    mv fluidd fluidd.backup."$BACKUP_DATE"
    popd || exit
  fi
}

stop_service() {
  # Function to restart a given service.
  # Arguments:
  #   $1 - The name of the service to restart.

  local service_name=$1
  print_msg INFO "  Stopping ${service_name} service..."
  if command -v systemctl &> /dev/null; then
    sudo systemctl stop "${service_name}"
  else
    sudo service "${service_name}" stop
  fi
}

start_service() {
  # Function to restart a given service.
  # Arguments:
  #   $1 - The name of the service to restart.

  local service_name=$1
  print_msg INFO "  Starting ${service_name} service..."
  if command -v systemctl &> /dev/null; then
    sudo systemctl start "${service_name}"
  else
    sudo service "${service_name}" start
  fi
}

exclude_from_klipper_git() {
  local EXTRAS_DIR="${AFC_PATH}/extras"
  local EXCLUDE_FILE="${KLIPPER_PATH}/.git/info/exclude"

  # Find all .py files in the extras directory and add them to the exclude file if they are not already present
  find "$EXTRAS_DIR" -type f -name "*.py" | while read -r file; do
    # Adjust the file path to the required format
    local relative_path="klippy/extras/$(basename "$file")"
    if ! grep -Fxq "$relative_path" "$EXCLUDE_FILE"; then
      echo "$relative_path" >> "$EXCLUDE_FILE"
    fi
  done
}

restart_klipper() {
  if query_printer_status; then
    restart_service klipper
  else
    print_msg ERROR "  Printer is not ready, most likely printing. Ensure you restart Klipper when the printer is idle."
  fi
}
