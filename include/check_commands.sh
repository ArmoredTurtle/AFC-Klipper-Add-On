#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

check_klipper() {
  # Function to check if the Klipper service is running.
  # Uses systemctl to list all services and checks if the Klipper service is present.
  # If the service is found, it prints a success message.
  # If the service is not found, it prints an error message and exits with status 1.

  if sudo systemctl list-units --full -all -t service --no-legend | grep -q -F "${KLIPPER_SERVICE}.service"; then
    print_msg SUCCESS "Klipper service found!"
  else
    print_msg ERROR "Klipper service not found. Install Klipper first."
    exit 1
  fi
}

check_root() {
  # Function to check if the script is being run as the root user.
  # If the script is run as root, it prints an error message and exits with status 1.
  # This is to ensure the script is run by a normal user for security reasons.

  if [ "$EUID" -eq 0 ]; then
    print_msg ERROR "Do not run as root, use a normal user"
    exit 1
  fi
}

check_existing_dirs() {
  # Function to check if the required directories for Klipper and Moonraker exist.
  # If the Klipper directory is not found, it prints an error message and exits with status 1.
  # If the Moonraker directory is not found, it prints an error message and exits with status 1.
  # The user can override the default directories using '-k <klipper_dir>' and '-m <moonraker_dir>' options.

  if [ ! -d "${KLIPPER_PATH}" ]; then
    print_msg ERROR "Klipper directory not found. Use '-k <klipper_dir>' to override."
    exit 1
  fi

  if [ ! -d "${MOONRAKER_PATH}" ]; then
    print_msg ERROR "Moonraker directory not found. Use '-m <moonraker_dir>' to override."
    exit 1
  fi
}

check_existing_install() {
  # Function to check for a prior AFC Klipper installation.
  # It iterates through all Python files in the extras directory of the AFC_PATH.
  # For each file, it checks if a symbolic link exists in the Klipper extras directory.
  # If an existing installation is found, it sets the PRIOR_INSTALLATION variable to True and breaks the loop.

  local extension
  print_msg INFO "Checking for prior AFC Klipper installation..."
  for extension in "${AFC_PATH}"/extras/*.py; do
    extension=$(basename "${extension}")
    if [ -L "${KLIPPER_PATH}/klippy/extras/${extension}" ]; then
      print_msg INFO "Existing installation found..."
      PRIOR_INSTALLATION=True
      break
    fi
  done
}

check_for_hh() {
  # Function to check if the "Happy Hare" extension is installed in Klipper extras.
  # It checks for the presence of the mmu.py file in the Klipper extras directory.
  # If the file exists, it searches for the text "Happy Hare" within the file.
  # If "Happy Hare" is found, it prints an error message and exits with status 1.
  # This is because AFC is not compatible with the "Happy Hare" extension.

  local file_path="${KLIPPER_PATH}/klippy/extras/mmu.py"
  local search_text="Happy Hare"

  if [ -f "$file_path" ]; then
    if grep -q "$search_text" "$file_path"; then
      print_msg ERROR "  Happy Hare was found installed in your klipper extras. AFC is not currently compatible"
      print_msg ERROR "  with Happy Hare. Please remove it, and then re-run this install-afc.sh script."
      exit 1
    fi
  fi
}