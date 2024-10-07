#!/bin/bash

# Force script to exit if an error occurs
set -e

export LC_ALL=C

KLIPPER_PATH="${HOME}/klipper"
KLIPPER_SERVICE=klipper
EXTENSION_LIST="AFC AFC_buffer AFC_stepper AFC_led AFC_assist"
GITREPO="https://github.com/ejsears/AFC-Klipper-Add-On.git"
AFC_PATH="${HOME}/AFC-Klipper-Add-On"
MOONRAKER_CONFIG="${HOME}/printer_data/config"
AFC_BRANCH=main
AFC_INSTALL_VARS="${AFC_PATH}/.afc_install_vars"

MOONRAKER_UPDATE_CONFIG='''
[update_manager afc-software]
type: git_repo
path: ~/AFC-Klipper-Add-On
origin: https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
managed_services: klipper moonraker
primary_branch: ${AFC_BRANCH}
install_script: install-afc.sh
'''

function clone_repo() {
  local afc_dir_name afc_base_name
  # Check if the repo is already cloned
  afc_dir_name="$(dirname "${AFC_PATH}")"
  afc_base_name="$(basename "${AFC_PATH}")"

  if [ ! -d "${AFC_PATH}" ]; then
    echo "Cloning AFC Klipper Add-On repo..."
    if git -C $afc_dir_name clone $GITREPO $afc_base_name; then
      echo "AFC Klipper Add-On repo cloned successfully"
      cd "${AFC_PATH}"
      git checkout "$AFC_BRANCH"
      cd -
    else
      echo "Failed to clone AFC Klipper Add-On repo"
      exit 1
    fi
  else
    echo "AFC Klipper Add-On repo already exists...continuing with updates"
  fi
}

function update_branch_in_file() {
  local current_branch

  # Check if the file exists
  if [ -f "${AFC_INSTALL_VARS}" ]; then
    # Read the current branch value from the file
    current_branch=$(grep -E '^branch=' "${AFC_INSTALL_VARS}" | cut -d'=' -f2)
  fi

  # If the current branch is not set or does not match the AFC_BRANCH, update the file
  if [ -z "${current_branch}" ] || [ "${current_branch}" != "${AFC_BRANCH}" ]; then
    echo "Updating branch in ${AFC_INSTALL_VARS} to ${AFC_BRANCH}"
    echo "branch=${AFC_BRANCH}" > "${AFC_INSTALL_VARS}"
  else
    echo "Branch in ${AFC_INSTALL_VARS} is already set to ${AFC_BRANCH}"
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
    sudo systemctl restart ${KLIPPER_SERVICE}
}

function restart_moonraker() {
    echo -e -n "\nRestarting Moonraker...\n"
    sudo systemctl restart moonraker
}

function update_moonraker_config() {
    echo -e -n "Updating Moonraker config with AFC-Klipper-Add-On\n"
    moonraker_config=$(grep -c '\[update_manager afc-software\]' ${MOONRAKER_CONFIG}/moonraker.conf || true)
    if [ $moonraker_config -eq 0 ]; then
        echo -e -n "\n${MOONRAKER_UPDATE_CONFIG}" >> ${MOONRAKER_CONFIG}/moonraker.conf
        echo -e -n "Moonraker config updated\n"
        restart_moonraker
    else
        echo -e -n "Moonraker config already configured for AFC-Klipper-Add-On"
    fi
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
    echo "  -k <klipper path>           Specify the path to the Klipper directory (default: ~/klipper)"
    echo "  -s <klipper service name>   Specify the name of the Klipper service (default: klipper)"
    echo "  -c <moonraker config path>  Specify the path to the Moonraker config directory (default: ~/printer_data/config)"
    echo "  -b <branch>                 Specify the branch to install from (default: main)"
    echo "  -u                          Uninstall the extensions"
    echo "  -h                          Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 [-k <klipper_path>] [-s <klipper_service_name>] [-c <moonraker_config_path>] [-b <branch>] [-u] [-h] "
}

do_uninstall=0

while getopts "k:s:c:uh" arg; do
    case ${arg} in
        k) KLIPPER_PATH=${OPTARG} ;;
        c) MOONRAKER_CONFIG=${OPTARG} ;;
        s) KLIPPER_SERVICE=${OPTARG} ;;
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
update_moonraker_config
exit 0
