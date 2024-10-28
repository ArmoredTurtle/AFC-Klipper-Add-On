#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

set -e
export LC_ALL=C

# Paths
KLIPPER_PATH="${HOME}/klipper"
MOONRAKER_PATH="${HOME}/printer_data/config"
AFC_PATH="${HOME}/AFC-Klipper-Add-On"
PRINTER_CONFIG_PATH="${HOME}/printer_data/config"
AFC_CONFIG_PATH="${PRINTER_CONFIG_PATH}/AFC"

# Variables
KLIPPER_SERVICE=klipper
GITREPO="https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git"
PRIOR_INSTALLATION=False
UPDATE_CONFIG=False
UNINSTALL=False
BRANCH=main

# Moonraker Config
MOONRAKER_UPDATE_CONFIG="""
[update_manager afc-software]
type: git_repo
path: ~/AFC-Klipper-Add-On
origin: $GITREPO
managed_services: klipper moonraker
primary_branch: $BRANCH
install_script: install-afc.sh
"""

# Debugging: Check if the directory exists
if [ ! -d "${AFC_PATH}/include/" ]; then
  echo "Directory ${AFC_PATH}/include/ does not exist."
  exit 1
fi

# Debugging: Check if there are any files in the directory
if [ -z "$(ls -A "${AFC_PATH}/include/")" ]; then
  echo "No files found in ${AFC_PATH}/include/"
  exit 1
fi

# Source the files
for file in "${AFC_PATH}/include/"*; do
  source "$file"
done

install_type() {
  while true; do
    echo -ne "
    ${PROMPT}Please select your installation type:
    ${CYAN}1) Box Turtle
    ${CYAN}2) Exit
    ${PROMPT}Please select an option: ${RESET}"
    read -r input
    case $input in
      1) INSTALLATION_TYPE="Box_Turtle"; break ;;
      2) echo "Exiting..."; exit 0 ;;
      *) echo "Invalid selection. Please try again." ;;
    esac
  done
}

choose_board_type() {
  while true; do
    echo -ne "
    ${PROMPT}Please select your board type:
    ${CYAN}1) AFC-Lite
    ${CYAN}2) MMB v1.0
    ${CYAN}3) MMB v1.1
    ${CYAN}4) Exit
    ${PROMPT}Please select an option: ${RESET}"
    read -r input
    case $input in
      1) BOARD_TYPE="AFC_Lite"; break ;;
      2) BOARD_TYPE="MMB_1.0"; break ;;
      3) BOARD_TYPE="MMB_1.1"; break ;;
      4) echo "Exiting..."; exit 0 ;;
      *) echo "Invalid selection" ;;
    esac
  done
}

toolhead_pin() {
  while true; do
    echo -ne "
    ${PROMPT}Please enter your toolhead sensor pin (if known).
    ${PROMPT}This should be in the format of 'MCU:Pin' (e.g 'EBBCan:PB2').
    ${ERROR}This is required to be set.
    ${PROMPT}Press enter if unknown.
    ${PROMPT}Pin: ${RESET}"
    read -r input
    TOOLHEAD_PIN=${input:-"UNKNOWN"}
    break
  done
}

buffer_system() {
  while true; do
    echo -ne "
    ${PROMPT}Please select your buffer system:
    ${CYAN}1) TurtleNeck Buffer
    ${CYAN}2) TurtleNeck v2 Buffer
    ${CYAN}3) Annex Belay
    ${CYAN}4) Other
    ${PROMPT}Please select an option: ${RESET}"
    read -r input
    case $input in
      1) BUFFER_SYSTEM="TurtleNeck"; break ;;
      2) BUFFER_SYSTEM="TurtleNeckV2"; break ;;
      3) BUFFER_SYSTEM="AnnexBelay"; break ;;
      4) BUFFER_SYSTEM="Other"; break ;;
      *) echo "Invalid selection" ;;
    esac
  done
}

macro_helpers() {
  # Function to prompt the user with a series of questions to enable/disable various functions.
  # The user's responses will be stored in corresponding variables.
  #
  # Local variables:
  #   question - The current question being asked.
  #   var - The variable name to store the user's response.
  #   default - The default value for the question.
  #   ordered_questions - An array of questions to be asked in order.
  local question var default ordered_questions
  print_msg PROMPT "  The following questions will enable / disable various functions."
  print_msg WARNING "  Further configuration for your system is required to be setup in the 'AFC_Macro_Vars.cfg' file."

  declare -A questions=(
    ["Do you want to add AFC includes to your printer.cfg file automatically?"]="INCLUDE_AFC_CFG True"
    ["Do you want to enable tip forming?"]="ENABLE_FORM_TIP False"
    ["Do you want to enable a toolhead cutter?"]="ENABLE_TOOL_CUT True"
    ["Do you want to enable the hub cutter?"]="ENABLE_HUB_CUT False"
    ["Do you want to enable the park macro?"]="ENABLE_PARK_MACRO True"
    ["Do you want to enable the poop macro?"]="ENABLE_POOP_MACRO True"
    ["Do you want to enable the kick macro?"]="ENABLE_KICK_MACRO True"
    ["Do you want to enable the wipe macro?"]="ENABLE_WIPE_MACRO True"
  )

  ordered_questions=(
    "Do you want to add AFC includes to your printer.cfg file automatically?"
    "Do you want to enable tip forming?"
    "Do you want to enable a toolhead cutter?"
    "Do you want to enable the hub cutter?"
    "Do you want to enable the park macro?"
    "Do you want to enable the poop macro?"
    "Do you want to enable the kick macro?"
    "Do you want to enable the wipe macro?"
  )

  for question in "${ordered_questions[@]}"; do
    IFS=' ' read -r var default <<< "${questions[$question]}"
    prompt_boolean "  $question" "$var" "$default"
  done
}

###################### Main script logic below ######################

while getopts "k:s:m:b:uh" arg; do
  case ${arg} in
  k) KLIPPER_PATH=${OPTARG} ;;
  m) MOONRAKER_PATH=${OPTARG} ;;
  s) KLIPPER_SERVICE=${OPTARG} ;;
  b) BRANCH=${OPTARG} ;;
  u) UNINSTALL=True ;;
  h)
    show_help
    exit 0
    ;;
  *) exit 1 ;;
  esac
done


clear
check_root
check_for_hh

if [ "$UNINSTALL" = "True" ]; then
  unlink_extensions
  manage_include "${PRINTER_CONFIG_PATH}/printer.cfg" "remove"
  print_msg INFO "  Uninstall complete."
  backup_afc_config
  print_msg WARNING "Ensure you perform the following steps:"
  print_msg INFO " 1. Review your printer.cfg to ensure the AFC configuration is removed."
  print_msg INFO " 2. Remove any AFC configuration from your moonraker config."
  print_msg INFO " 3. Restart your Klipper service."
  exit 0
fi

clone_repo
check_existing_install
info_menu

if [ "$PRIOR_INSTALLATION" = "True" ]; then
  print_msg WARNING "A prior installation of AFC has been detected."
  prompt_boolean "Would you like to like to update the config files from the repo?" "update_config_repo" "False"
  if [ "$update_config_repo" = "True" ]; then
    backup_afc_config
    UPDATE_CONFIG=True
  else
    print_msg WARNING "  Skipping configuration update and updating AFC extensions only."
    link_extensions
    exit 0
  fi
fi

if [ "$PRIOR_INSTALLATION" = "False" ] || [ "$UPDATE_CONFIG" = "True" ]; then
  link_extensions
  copy_config
  install_type
  choose_board_type
  toolhead_pin
  buffer_system

  print_section_delimiter

  macro_helpers
  print_msg INFO "  Updating configuration files with selected values..."

  # Make sure to copy the right AFC_Hardware.cfg file based on the board type.
  if [ "$BOARD_TYPE" == "AFC_Lite" ]; then
    cp "${AFC_PATH}/templates/AFC_Hardware-AFC.cfg" "${AFC_CONFIG_PATH}/AFC_Hardware.cfg"
  else
    cp "${AFC_PATH}/templates/AFC_Hardware-MMB.cfg" "${AFC_CONFIG_PATH}/AFC_Hardware.cfg"
  fi

  ## This section will choose the correct board type for MMB
  if [ "$BOARD_TYPE" == "MMB_1.0" ] || [ "$BOARD_TYPE" == "MMB_1.1" ]; then
    uncomment_board_type "${AFC_CONFIG_PATH}/AFC_Hardware.cfg" "${BOARD_TYPE}"
  fi

  # The below section will update configuration values in the AFC configuration files. This takes the format of
  # update_config_value <file_path> <key> <new_value>. Any trailing comments will be preserved.
  update_config_value "${AFC_CONFIG_PATH}/AFC.cfg" "Type" "${INSTALLATION_TYPE}"
  update_config_value "${AFC_CONFIG_PATH}/AFC.cfg" "tool_cut" "${ENABLE_TOOL_CUT}"
  update_config_value "${AFC_CONFIG_PATH}/AFC.cfg" "park" "${ENABLE_PARK_MACRO}"
  update_config_value "${AFC_CONFIG_PATH}/AFC.cfg" "hub_cut" "${ENABLE_HUB_CUT}"
  update_config_value "${AFC_CONFIG_PATH}/AFC.cfg" "poop" "${ENABLE_POOP_MACRO}"
  update_config_value "${AFC_CONFIG_PATH}/AFC.cfg" "kick" "${ENABLE_KICK_MACRO}"
  update_config_value "${AFC_CONFIG_PATH}/AFC.cfg" "wipe" "${ENABLE_WIPE_MACRO}"
  update_config_value "${AFC_CONFIG_PATH}/AFC.cfg" "form_tip" "${ENABLE_FORM_TIP}"

  # The section will update the toolhead pin in the AFC_Hardware.cfg file.
  update_switch_pin "${AFC_CONFIG_PATH}/AFC_Hardware.cfg" "${TOOLHEAD_PIN}"

  # Update printer.cfg if selected
  if [ "$INCLUDE_AFC_CFG" = "True" ]; then
    manage_include "${PRINTER_CONFIG_PATH}/printer.cfg" "add"
  fi

  # Update buffer configuration
  if [ "$BUFFER_SYSTEM" == "TurtleNeck" ]; then
    append_buffer_config "TurtleNeck"
  elif [ "$BUFFER_SYSTEM" == "TurtleNeckV2" ]; then
    append_buffer_config "TurtleNeckV2"
  elif [ "$BUFFER_SYSTEM" == "AnnexBelay" ]; then
    append_buffer_config "AnnexBelay"
  else
    print_msg WARNING "  Buffer not configured, skipping configuration."
  fi

  # Update moonraker config
  update_moonraker_config

  print_msg INFO "  Prior to starting Klipper, please review all files in the AFC directory to ensure they are correct."
  print_msg WARNING "  This includes especially the AFC_Macro_Vars.cfg file and the pins in AFC_Hardware.cfg"
  print_msg INFO "  Once you have reviewed the files, restart Klipper to apply the changes."
fi