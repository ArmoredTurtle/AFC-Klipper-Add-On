#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

info_menu() {
  printf "\e[49m             \e[38;5;143;49m▄▄\e[38;5;143;48;5;143m▄\e[49;38;5;143m▀\e[38;5;143;48;5;143m▄\e[38;5;143;49m▄▄\e[49m             \e[m  \n"
  printf "\e[49m         \e[38;5;143;49m▄▄\e[38;5;143;48;5;143m▄▄\e[49;38;5;143m▀\e[38;5;29;48;5;143m▄\e[38;5;29;49m▄\e[38;5;29;48;5;29m▄\e[38;5;29;49m▄\e[38;5;29;48;5;143m▄\e[49;38;5;143m▀\e[38;5;143;48;5;143m▄▄\e[38;5;143;49m▄▄\e[49m         \e[m\n"
  printf "\e[49m      \e[38;5;143;49m▄\e[38;5;143;48;5;143m▄▄\e[49;38;5;143m▀\e[38;5;29;48;5;143m▄\e[38;5;29;49m▄\e[38;5;29;48;5;29m▄▄\e[48;5;29m     \e[38;5;29;48;5;29m▄▄\e[38;5;29;49m▄\e[38;5;29;48;5;143m▄\e[49;38;5;143m▀\e[38;5;143;48;5;143m▄▄\e[38;5;143;49m▄\e[49m      \e[m\n"
  printf "\e[49m  \e[38;5;143;49m▄▄\e[38;5;143;48;5;143m▄▄\e[49;38;5;143m▀\e[38;5;29;48;5;143m▄\e[38;5;29;49m▄\e[38;5;29;48;5;29m▄\e[48;5;29m   \e[38;5;29;48;5;29m▄▄\e[49;38;5;29m▀▀▀\e[38;5;29;48;5;29m▄▄\e[48;5;29m   \e[38;5;29;48;5;29m▄\e[38;5;29;49m▄\e[38;5;29;48;5;143m▄\e[49;38;5;143m▀\e[38;5;143;48;5;143m▄▄\e[38;5;143;49m▄▄\e[49m  \e[m  This installation script will install/update the AFC Klipper extension to your system.\n"
  printf "\e[38;5;143;48;5;143m▄▄\e[49;38;5;143m▀\e[38;5;29;48;5;143m▄\e[38;5;29;49m▄\e[38;5;29;48;5;29m▄▄\e[48;5;29m   \e[38;5;29;48;5;29m▄▄\e[49;38;5;29m▀▀\e[49m     \e[49;38;5;29m▀▀\e[38;5;29;48;5;29m▄▄\e[48;5;29m   \e[38;5;29;48;5;29m▄▄\e[38;5;29;49m▄\e[38;5;29;48;5;143m▄\e[49;38;5;143m▀\e[38;5;143;48;5;143m▄▄\e[m\n"
  printf "\e[48;5;143m \e[49m \e[48;5;29m     \e[38;5;29;48;5;29m▄\e[49;38;5;29m▀▀\e[49m             \e[49;38;5;29m▀▀\e[38;5;29;48;5;29m▄\e[48;5;29m     \e[49m \e[48;5;143m \e[m  Discord: https://discord.gg/armoredturtle\n"
  printf "\e[48;5;143m \e[49m \e[48;5;29m    \e[49;38;5;29m▀\e[38;5;29;49m▄▄\e[38;5;29;48;5;29m▄▄▄▄\e[38;5;29;49m▄▄\e[49m   \e[38;5;29;49m▄▄\e[38;5;29;48;5;29m▄▄▄▄\e[38;5;29;49m▄▄\e[49;38;5;29m▀\e[48;5;29m    \e[49m \e[48;5;143m \e[m  Github: https://github.com/ArmoredTurtle\n"
  printf "\e[48;5;143m \e[49m \e[48;5;29m    \e[49m \e[49;38;5;29m▀▀\e[38;5;29;48;5;29m▄\e[48;5;29m \e[38;5;29;48;5;29m▄\e[48;5;29m   \e[38;5;29;48;5;29m▄▄▄\e[48;5;29m   \e[38;5;29;48;5;29m▄\e[48;5;29m \e[38;5;29;48;5;29m▄\e[49;38;5;29m▀▀\e[49m \e[48;5;29m    \e[49m \e[48;5;143m \e[m  Documentation: https://armoredturtle.xyz/\n"
  printf "\e[48;5;143m \e[49m \e[48;5;29m    \e[49m     \e[49;38;5;29m▀▀\e[48;5;29m      \e[38;5;29;48;5;29m▄\e[49;38;5;29m▀▀\e[49m     \e[48;5;29m    \e[49m \e[48;5;143m \e[m\n"
  printf "\e[48;5;143m \e[49m \e[48;5;29m    \e[49m        \e[48;5;29m     \e[49m        \e[48;5;29m    \e[49m \e[48;5;143m \e[m\n"
  printf "\e[48;5;143m \e[49m \e[48;5;29m    \e[49m        \e[48;5;29m     \e[49m        \e[48;5;29m    \e[49m \e[48;5;143m \e[m\n"
  printf "\e[48;5;143m \e[49m \e[48;5;29m    \e[49m        \e[48;5;29m     \e[49m        \e[48;5;29m    \e[49m \e[48;5;143m \e[m\n"
  printf "\e[48;5;143m \e[49m \e[48;5;29m    \e[49m        \e[48;5;29m     \e[49m        \e[48;5;29m    \e[49m \e[48;5;143m \e[m\n"
  printf "\e[48;5;143m \e[49m \e[48;5;29m    \e[49m        \e[48;5;29m     \e[49m        \e[48;5;29m    \e[49m \e[48;5;143m \e[m\n"
  printf "\e[38;5;143;48;5;143m▄▄\e[38;5;143;49m▄\e[38;5;143;48;5;29m▄\e[49;38;5;29m▀\e[38;5;29;48;5;29m▄\e[49m        \e[48;5;29m     \e[49m        \e[38;5;29;48;5;29m▄\e[49;38;5;29m▀\e[38;5;143;48;5;29m▄\e[38;5;143;49m▄\e[38;5;143;48;5;143m▄▄\e[m\n"
  printf "\e[49m  \e[49;38;5;143m▀▀\e[38;5;143;48;5;143m▄▄\e[38;5;143;49m▄▄\e[49m      \e[48;5;29m     \e[49m      \e[38;5;143;49m▄▄\e[38;5;143;48;5;143m▄▄\e[49;38;5;143m▀▀\e[49m  \e[m\n"
  printf "\e[49m      \e[49;38;5;143m▀\e[38;5;143;48;5;143m▄▄\e[38;5;143;49m▄▄\e[49m   \e[48;5;29m     \e[49m   \e[38;5;143;49m▄▄\e[38;5;143;48;5;143m▄▄\e[49;38;5;143m▀\e[49m      \e[m\n"
  printf "\e[49m         \e[49;38;5;143m▀▀\e[38;5;143;48;5;143m▄▄\e[38;5;143;49m▄▄\e[49;38;5;29m▀\e[38;5;29;48;5;29m▄\e[49;38;5;29m▀\e[38;5;143;49m▄▄\e[38;5;143;48;5;143m▄▄\e[49;38;5;143m▀▀\e[49m         \e[m\n"
  printf "\e[49m             \e[49;38;5;143m▀▀\e[38;5;143;48;5;143m▄\e[38;5;143;49m▄\e[38;5;143;48;5;143m▄\e[49;38;5;143m▀▀\e[49m             \e[m\n"
}

function show_help() {
  echo "Usage: install-afc.sh [options]"
  echo ""
  echo "Options:"
  echo "  -k <path>                   Specify the path to the Klipper directory"
  echo "  -m <moonraker config path>  Specify the path to the Moonraker config directory (default: ~/printer_data/config)"
  echo "  -s <klipper service name>   Specify the name of the Klipper service (default: klipper)"
  echo "  -u                          Uninstall the extensions"
  echo "  -b <branch>                 Specify the branch to use (default: main)"
  echo "  -h                          Display this help message"
  echo ""
  echo "Example:"
  echo " $0 [-k <klipper_path>] [-s <klipper_service_name>] [-m <moonraker_config_path>] [-b <branch>] [-u] [-h] "
}

prompt_boolean() {
  # Function to prompt the user for a boolean input (True/False).
  # Arguments:
  #   $1: prompt_message - The message to display to the user.
  #   $2: var_name - The name of the variable to store the user's input.
  #   $3: default_value - The default value to use if the user provides no input.
  #
  # The function uses the following local variables:
  #   - input: The user's input.

  local prompt_message=$1
  local var_name=$2
  local default_value=$3
  local input

  echo -ne "${PROMPT}${prompt_message} (True/False) [${PURPLE}Default: ${default_value}${PROMPT}]:${RESET} "
  read -r input

  # If input is empty, use the default value
  if [ -z "$input" ]; then
    input=$default_value
  fi
  if [[ "$input" != "True" && "$input" != "False" ]]; then
    echo "Invalid input. Please enter 'True' or 'False'."
    prompt_boolean "$prompt_message" "$var_name" "$default_value"
  else
    eval "$var_name=$input"
  fi
}

confirm_continue() {
  # Function to prompt the user to press Y, y, or Enter to continue.
  # Exits the script if the user does not press Y, y, or Enter.

  read -p "  Do you want to continue? (Y/n): " -n 1 -r
  echo
  if [[ -z $REPLY || $REPLY =~ ^[Yy]$ ]]; then
    return
  else
    print_msg ERROR "  Operation aborted."
    exit 1
  fi
}