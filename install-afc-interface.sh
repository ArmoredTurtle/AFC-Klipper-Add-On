#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

set -e
export LC_ALL=C

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for include_file in "${SCRIPT_DIR}/include/"*; do
  source "$include_file"
done

install_type() {
  while true; do
    echo -ne "
    ${PROMPT}Please select your installation type:
    ${CYAN}1) Mainsail
    ${CYAN}2) Fluidd
    ${CYAN}3) Exit
    ${PROMPT}Please select an option: ${RESET}"
    read -r input
    case $input in
      1) INSTALLATION_TYPE="mainsail"; break ;;
      2) print_msg WARNING "  Fluidd is not yet supported. Please select another option." ;;
      3) echo "Exiting..."; exit 0 ;;
      *) echo "Invalid selection. Please try again." ;;
    esac
  done
}


clear
check_root
check_for_hh
check_for_afc
check_unzip

print_msg WARNING "  This script will install the Mainsail or Fluidd interface for AFC."
print_msg WARNING "  This will overwrite any existing Mainsail or Fluidd installation, however a backup will be made"

confirm_continue

install_type

if [ "$INSTALLATION_TYPE" == "mainsail" ]; then
  check_for_mainsail
  backup_mainsail
  if [ ! -f "$MAINSAIL_SRC" ]; then
    print_msg ERROR "  $MAINSAIL_SRC not found. Aborting."
    exit 1
  fi
  unzip -o "$MAINSAIL_SRC" -d "$MAINSAIL_DST"
  print_msg INFO "  Mainsail interface installed successfully. Please refresh any browser windows to see the changes."
fi
