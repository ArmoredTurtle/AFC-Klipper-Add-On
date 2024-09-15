#!/bin/bash

# Force script to exit if an error occurs
set -e

export LC_ALL=C

KLIPPER_PATH="${HOME}/klipper"
EXTENSION_LIST="AFC AFC_buffer AFC_stepper AFC_led AFC_assist"
GITREPO="https://github.com/ejsears/AFC-Klipper-Add-On.git"
AFC_PATH="${HOME}/AFC-Klipper-Add-On"

function clone_repo() {
  local afc_dir_name afc_base_name
  # Check if the repo is already cloned
  afc_dir_name="$(dirname "${AFC_PATH}")"
  afc_base_name="$(basename "${AFC_PATH}")"

  if [ ! -d "${AFC_PATH}" ]; then
    echo "Cloning AFC Klipper Add-On repo..."
    if git -c "$afc_dir_name" clone $GITREPO "$afc_base_name"; then
      chmod +x "${AFC_PATH}"/install-afc.sh
      echo "Repo cloned successfully"
    else
      echo "Failed to clone repo"
      exit 1
    fi
  else
    echo "AFC Klipper Add-On repo already exists...continuing with updates"
  fi
}

# Step 1:  Verify Klipper has been installed
function check_klipper() {
    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
        echo "Klipper service found!"
    else
        echo "Klipper service not found, please install Klipper first"
        exit 1
    fi
}

# Step 2: Check if the extensions are already present.
# This is a way to check if this is the initial installation.
function check_existing() {
    for extension in ${EXTENSION_LIST}; do
        [ -L "${KLIPPER_PATH}/klippy/extras/${extension}.py" ] || return 1
    done
    return 0
}

# Step 3: Link extension to Klipper
function link_extensions() {
    echo "Linking extensions to Klipper..."
    for extension in ${EXTENSION_LIST}; do
        ln -sf "${AFC_PATH}/${extension}.py" "${KLIPPER_PATH}/klippy/extras/${extension}.py"
    done
}

function unlink_extensions() {
    echo "Unlinking extensions from Klipper..."
    for extension in ${EXTENSION_LIST}; do
        rm -f "${KLIPPER_PATH}/klippy/extras/${extension}.py"
    done
}

# Step 4: Restart Klipper
function restart_klipper() {
    echo "Restarting Klipper..."
    sudo systemctl restart klipper
}

function verify_ready() {
    if [ "$(id -u)" -eq 0 ]; then
        echo "This script must not run as root"
        exit 1
    fi
}

function show_help() {
    echo "Usage: install-afc.sh [options]"
    echo ""
    echo "Options:"
    echo "  -k <path>    Specify the path to the Klipper directory"
    echo "  -u           Uninstall the extensions"
    echo "  -h           Display this help message"
    echo ""
    echo "Example:"
    echo "  install-afc.sh -k ~/klipper"
}

function show_moonraker_config() {
    local REQUIRED_CONFIG="[update_manager afc-software]
type: git_repo
path: ~/AFC-Klipper-Add-On
origin: https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
managed_services: klipper moonraker
primary_branch: main
install_script: install-afc.sh
"
    echo "Please ensure the following is in your moonraker.conf if you want automatic updates:"
    echo ""
    echo "${REQUIRED_CONFIG}"
}

do_uninstall=0

while getopts "k:uh" arg; do
    case ${arg} in
        k) KLIPPER_PATH=${OPTARG} ;;
        u) do_uninstall=1 ;;
        h) show_help; exit 0 ;;
        *) exit 1 ;;
    esac
done

clone_repo
check_klipper
verify_ready

if ! check_existing; then
    link_extensions
else
    if [ ${do_uninstall} -eq 1 ]; then
        unlink_extensions
    fi
fi

restart_klipper
show_moonraker_config
exit 0
