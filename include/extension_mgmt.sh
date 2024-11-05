#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

link_extensions() {
  # Function to link AFC extensions to Klipper.
  # Uses the global variables:
  #   - KLIPPER_PATH: The path to the Klipper installation.
  #   - AFC_PATH: The path to the AFC Klipper Add-On repository.

  print_msg INFO "  Linking AFC extensions to Klipper..."
  if [ -d "${KLIPPER_PATH}/klippy/extras" ]; then
    for extension in "${AFC_PATH}"/extras/*.py; do
      ln -sf "${AFC_PATH}/extras/$(basename "${extension}")" "${KLIPPER_PATH}/klippy/extras/$(basename "${extension}")"
    done
  else
    print_msg ERROR "  AFC Klipper extensions not installed; Klipper extras directory not found."
    exit 1
  fi
}

unlink_extensions() {
  # Function to unlink AFC extensions from Klipper.
  # Uses the global variables:
  #   - KLIPPER_PATH: The path to the Klipper installation.
  #   - AFC_PATH: The path to the AFC Klipper Add-On repository.

  print_msg INFO "  Unlinking AFC extensions from Klipper..."
  if [ -d "${KLIPPER_PATH}/klippy/extras" ]; then
    for extension in "${AFC_PATH}"/extras/*.py; do
      rm -f "${KLIPPER_PATH}/klippy/extras/$(basename "${extension}")"
    done
  else
    print_msg ERROR "  AFC Klipper extensions not uninstalled; Klipper extras directory not found."
    exit 1
  fi
}