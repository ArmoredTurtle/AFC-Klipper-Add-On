#!/bin/bash

# Force script to exit if an error occurs
set -e

KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"
EXTENSION_LIST="AFC AFC_buffer AFC_stepper AFC_led"
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"

# Step 1:  Verify Klipper has been installed
function check_klipper() {
    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
        echo "Klipper service found!"
    else
        echo "Klipper service not found, please install Klipper first"
        exit -1
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
        ln -sf "${SRCDIR}/${extension}.py" "${KLIPPER_PATH}/klippy/extras/${extension}.py"
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
        exit -1
    fi
}

do_uninstall=0

while getopts "k:u" arg; do
    case ${arg} in
        k) KLIPPER_PATH=${OPTARG} ;;
        u) do_uninstall=1 ;;
    esac
done

verify_ready
if ! check_existing; then
    link_extensions
else
    if [ ${do_uninstall} -eq 1 ]; then
        unlink_extensions
    fi
fi
restart_klipper
exit 0
