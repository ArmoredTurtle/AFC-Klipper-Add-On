#!/usr/bin/env bash

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

pushd() {
  command pushd "$@" >/dev/null
}

popd() {
  command popd >/dev/null
}

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

# Colors
NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'

BOLD_RED='\033[1;31m'
BOLD_GREEN='\033[1;32m'
BOLD_YELLOW='\033[1;33m'
BOLD_BLUE='\033[1;34m'
BOLD_PURPLE='\033[1;35m'
BOLD_CYAN='\033[1;36m'
BOLD_WHITE='\033[1;37m'

# Messages
INFO="${BLUE}"
ERROR="${BOLD_RED}"
SUCCESS="${BOLD_PURPLE}"
PROMPT="${BOLD_WHITE}"
WARNING="${BOLD_YELLOW}"
RESET="${NC}"

print_msg() {
  local type=$1
  shift
  case $type in
    INFO) echo -e "${INFO}$1${RESET}" ;;
    WARNING) echo -e "${WARNING}$1${RESET}" ;;
    ERROR) echo -e "${ERROR}$1${RESET}" ;;
    PROMPT) echo -e "${PROMPT}$1${RESET}" ;;
    *) echo -e "$1" ;;
  esac
}

check_root() {
  if [ "$EUID" -eq 0 ]; then
    print_msg ERROR "Do not run as root, use a normal user"
    exit 1
  fi
}

restart_service() {
  local service_name=$1
  print_msg INFO "Restarting ${service_name} service..."
  if command -v systemctl &> /dev/null; then
    sudo systemctl restart "${service_name}"
  else
    sudo service "${service_name}" restart
  fi
}

check_klipper() {
  if sudo systemctl list-units --full -all -t service --no-legend | grep -q -F "${KLIPPER_SERVICE}.service"; then
    print_msg SUCCESS "Klipper service found!"
  else
    print_msg ERROR "Klipper service not found. Install Klipper first."
    exit 1
  fi
}

check_existing_dirs() {
  if [ ! -d "${KLIPPER_PATH}" ]; then
    print_msg ERROR "Klipper directory not found. Use '-k <klipper_dir>' to override."
    exit 1
  fi

  if [ ! -d "${MOONRAKER_PATH}" ]; then
    print_msg ERROR "Moonraker directory not found. Use '-m <moonraker_dir>' to override."
    exit 1
  fi
}

link_extensions() {
  local extension
  print_msg INFO "Linking AFC extensions to Klipper..."
  if [ -d "${KLIPPER_PATH}/klippy/extras" ]; then
    for extension in "${AFC_PATH}"/extras/*.py; do
      extension=$(basename "${extension}")
      ln -sf "${AFC_PATH}/extras/${extension}" "${KLIPPER_PATH}/klippy/extras/${extension}"
    done
  else
    print_msg ERROR "AFC Klipper extensions not installed; Klipper extras directory not found."
    exit 1
  fi
}

unlink_extensions() {
  local extension
  print_msg INFO "Unlinking AFC extensions from Klipper..."
  if [ -d "${KLIPPER_PATH}/klippy/extras" ]; then
    for extension in "${AFC_PATH}"/extras/*.py; do
      extension=$(basename "${extension}")
      rm -f "${KLIPPER_PATH}/klippy/extras/${extension}"
    done
  else
    print_msg ERROR "AFC Klipper extensions not uninstalled; Klipper extras directory not found."
    exit 1
  fi
}

check_existing_install() {
  local extension
  print_msg INFO "Checking for prior AFC Klipper installation..."
  for extension in "${AFC_PATH}"/extras/*.py; do
    extension=$(basename "${extension}")
    if [ -L "${KLIPPER_PATH}/klippy/extras/${extension}" ]; then
      print_msg INFO "Existing installation found..."
      PRIOR_INSTALLATION=True``
      break
    fi
  done
}

backup_afc_config() {
  if [ -d "${AFC_CONFIG_PATH}" ]; then
    print_msg INFO "Backing up existing AFC config..."
    pushd "${PRINTER_CONFIG_PATH}"
    mv AFC AFC.backup.$(date +%Y%m%d%H%M%S)
    popd
  fi
}

prompt_boolean() {
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

print_section_delimiter() {
  print_msg SUCCESS "----------------------------------------"
}

check_for_hh() {
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

install_type() {
  while true; do
    echo -ne "
    ${PROMPT}Please select your installation type:
    ${CYAN}1) Box Turtle
    ${CYAN}2) Exit
    ${PROMPT}Please select an option: ${RESET}"
    read -r input
    case $input in
      1)
        INSTALLATION_TYPE="Box_Turtle"
        break
        ;;
      2)
        echo "Exiting..."
        exit 0
        ;;
      *)
        echo "Invalid selection. Please try again."
        ;;
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
      1)
        BOARD_TYPE="AFC_Lite"
        break
        ;;
      2)
        BOARD_TYPE="MMB_1.0"
        break
        ;;
      3)
        BOARD_TYPE="MMB_1.1"
        break
        ;;
      4) echo "Exiting..." && exit 0 ;;
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
    if [ -z "$input" ]; then
      TOOLHEAD_PIN="UNKNOWN"
      break
    else
      TOOLHEAD_PIN=$input
      break
    fi
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
      1)
        BUFFER_SYSTEM="TurtleNeck"
        break
        ;;
      2)
        BUFFER_SYSTEM="TurtleNeckV2"
        break
        ;;
      3)
        BUFFER_SYSTEM="AnnexBelay"
        break
        ;;
      4)
        BUFFER_SYSTEM="Other"
        break
        ;;
      *) echo "Invalid selection" ;;
    esac
  done
}

macro_helpers() {
  local question
  local var
  local default
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

  for question in "${!questions[@]}"; do
    IFS=' ' read -r var default <<< "${questions[$question]}"
    prompt_boolean "  $question" "$var" "$default"
  done
}

function clone_repo() {
  local afc_dir_name afc_base_name
  # Check if the repo is already cloned
  afc_dir_name="$(dirname "${AFC_PATH}")"
  afc_base_name="$(basename "${AFC_PATH}")"

  if [ ! -d "${AFC_PATH}" ]; then
    echo "Cloning AFC Klipper Add-On repo..."
    if git -C $afc_dir_name clone --quiet $GITREPO $afc_base_name; then
      print_msg INFO "AFC Klipper Add-On repo cloned successfully"
      pushd "${AFC_PATH}"
      git checkout --quiet "${BRANCH}"
      popd
    else
      print_msg ERROR "Failed to clone AFC Klipper Add-On repo"
      exit 1
    fi
  else
    pushd "${AFC_PATH}"
    git pull --quiet
    git checkout --quiet "${BRANCH}"
    popd
  fi
}

function update_moonraker_config() {
  local moonraker_config
  print_msg INFO "  Updating Moonraker config with AFC-Klipper-Add-On"
  moonraker_config=$(grep -c '\[update_manager afc-software\]' "${MOONRAKER_PATH}/moonraker.conf" || true)
  if [ "$moonraker_config" -eq 0 ]; then
    echo -e -n "\n${MOONRAKER_UPDATE_CONFIG}" >>"${MOONRAKER_PATH}/moonraker.conf"
    print_msg INFO "Moonraker config updated"
    restart_service moonraker
  else
    print_msg INFO "  Moonraker config already updated"
  fi
}

# Check if the include AFC/*.cfg is in the printer.cfg file and add or remove it based on the action.
manage_include() {
  local file_path="$1"
  local action="$2"
  local include_statement="[include AFC/*.cfg]"
  local save_config_line="#*# <---------------------- SAVE_CONFIG ---------------------->"

  if [ "$action" == "add" ]; then
    if ! grep -qF "$include_statement" "$file_path"; then
      if grep -qF "$save_config_line" "$file_path"; then
        sed -i "/$save_config_line/i $include_statement" "$file_path"
        print_msg INFO "  Added '$include_statement' in $file_path"
      else
        echo "$include_statement" >> "$file_path"
        print_msg INFO "  Added '$include_statement' to $file_path"
      fi
    else
      print_msg WARNING "  '$include_statement' is already present in $file_path, not adding."
    fi
  elif [ "$action" == "remove" ]; then
    if grep -qF "$include_statement" "$file_path"; then
      grep -vF "$include_statement" "$file_path" > "${file_path}.tmp"
      mv "${file_path}.tmp" "$file_path"
      print_msg INFO "  Removed '$include_statement' from $file_path"
    else
      print_msg WARNING "  '$include_statement' is not present in $file_path, nothing to remove."
    fi
  else
    print_msg ERROR "  Invalid action specified. Use 'add' or 'remove'."
  fi
}

# Updates a configuration value in a file. Looks for the value of the key and replaces it with the new value.
update_config_value() {
  local file_path="$1"
  local key="$2"
  local new_value="$3"

  # Create a temporary file
  local temp_file=$(mktemp)

  # Read the file line by line
  while IFS= read -r line; do
    if [[ "$line" =~ ^[[:space:]]*$key[[:space:]]*:[[:space:]]*([^[:space:]]+)[[:space:]]*(#.*)?$ ]]; then
      local comment="${BASH_REMATCH[2]}"
      echo "$key: $new_value ${comment}" >> "$temp_file"
    else
      echo "$line" >> "$temp_file"
    fi
  done < "$file_path"

  # Replace the original file with the updated file
  mv "$temp_file" "$file_path"
}

uncomment_board_type() {
  local file_path="$1"
  local board_type="$2"
  local temp_file=$(mktemp)

  while IFS= read -r line; do
    case "$board_type" in
      "MMB_1.0")
        if [[ "$line" =~ ^#\[include\ mcu/MMB_1\.0\.cfg\]$ ]]; then
          echo "[include mcu/MMB_1.0.cfg]" >> "$temp_file"
        else
          echo "$line" >> "$temp_file"
        fi
        ;;
      "MMB_1.1")
        if [[ "$line" =~ ^#\[include\ mcu/MMB_1\.1\.cfg\]$ ]]; then
          echo "[include mcu/MMB_1.1.cfg]" >> "$temp_file"
        else
          echo "$line" >> "$temp_file"
        fi
        ;;
      "AFC_Lite")
        if [[ "$line" =~ ^#\[include\ mcu/AFC_Lite\.cfg\]$ ]]; then
          echo "[include mcu/AFC_Lite.cfg]" >> "$temp_file"
        else
          echo "$line" >> "$temp_file"
        fi
        ;;
      *)
        echo "$line" >> "$temp_file"
        ;;
    esac
  done < "$file_path"
  mv "$temp_file" "$file_path"
}

update_distance() {
  local file_path="$1"
  local new_distance="$2"
  local section="[AFC_buffer neck]"
  local key="distance"
  local in_section=false
  local temp_file=$(mktemp)

  while IFS= read -r line; do
    if [[ "$line" == "$section" ]]; then
      in_section=true
      echo "$line" >> "$temp_file"
    elif $in_section && [[ "$line" =~ ^$key ]]; then
      echo "$key: $new_distance" >> "$temp_file"
      in_section=false
    else
      echo "$line" >> "$temp_file"
    fi
  done < "$file_path"

  mv "$temp_file" "$file_path"
}

update_switch_pin() {
  local file_path="$1"
  local new_value="$2"
  local temp_file=$(mktemp)
  local in_section=false

  while IFS= read -r line; do
    if [[ "$line" =~ ^\[filament_switch_sensor\ tool_start\]$ ]]; then
      in_section=true
      echo "$line" >> "$temp_file"
    elif $in_section && [[ "$line" =~ ^switch_pin: ]]; then
      echo "switch_pin: $new_value" >> "$temp_file"
      in_section=false
    else
      echo "$line" >> "$temp_file"
    fi
  done < "$file_path"

  mv "$temp_file" "$file_path"
}

# Copies the AFC configuration files to the specified AFC configuration path.
# If the AFC configuration directory does not exist, it creates the directory.
function copy_config() {
  if [ -d "${AFC_CONFIG_PATH}" ]; then
    mkdir -p "${AFC_CONFIG_PATH}"
  fi
  print_msg INFO "Copying AFC config files..."
  cp -R "${AFC_PATH}/config" "${AFC_CONFIG_PATH}"
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

###################### Main script logic below ######################

clear
check_root
check_for_hh

if [ "$UNINSTALL" = "True" ]; then
  unlink_extensions
  manage_include "${PRINTER_CONFIG_PATH}/printer.cfg" "remove"
  print_msg INFO "Uninstall complete."
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
    print_msg WARNING "Skipping configuration update and updating AFC extensions only."
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

  # Update distance on buffer config
  if [ "$BUFFER_SYSTEM" == "TurtleNeck" ] || [ "$BUFFER_SYSTEM" == "TurtleNeckV2" ]; then
    update_distance "${AFC_CONFIG_PATH}/AFC_Hardware.cfg" "25"
  elif [ "$BUFFER_SYSTEM" == "AnnexBelay" ]; then
    update_distance "${AFC_CONFIG_PATH}/AFC_Hardware.cfg" "6"
  else
    print_msg WARNING "Buffer system not recognized. Please update the distance in the AFC_Hardware.cfg file."
  fi

  # Update moonraker config
  update_moonraker_config

  print_msg INFO "  Prior to starting Klipper, please review all files in the AFC directory to ensure they are correct."
  print_msg WARNING "  This includes especially the AFC_Macro_Vars.cfg file and the pins in AFC_Hardware.cfg"
  print_msg INFO "  Once you have reviewed the files, restart Klipper to apply the changes."
fi