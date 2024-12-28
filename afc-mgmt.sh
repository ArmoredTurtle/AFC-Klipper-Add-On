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

source include/colors.sh
source include/constants.sh
source include/install_functions.sh
source include/check_commands.sh
source include/utils.sh
source include/buffer_configurations.sh

source include/main_menu.sh
source include/install_menu.sh
source include/uninstall.sh

###################### Main script logic below ######################

while getopts "k:s:m:b:p:uh" arg; do
  case ${arg} in
  k) klipper_dir=${OPTARG} ;;
  m) moonraker_config_file=${OPTARG} ;;
  s) klipper_service=${OPTARG} ;;
  b) branch=${OPTARG} ;;
  p) printer_config_dir=${OPTARG} ;;
  u) uninstall=True ;;
  h)
    show_help
    exit 0
    ;;
  *) exit 1 ;;
  esac
done


clear
# Make sure necessary directories exist
check_root
check_for_hh
clone_repo
check_existing_install
set_install_version_if_missing
if [ "$force_update_no_version" == "False" ]; then
  check_version_and_set_force_update
fi

main_menu
