#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

exit_afc_install() {
  if [ "$files_updated_or_installed" == "True" ]; then
    echo "AFC_INSTALL_VERSION=$CURRENT_INSTALL_VERSION" > "${AFC_CONFIG_PATH}/.afc-version"
  restart_klipper
  fi
  exit 0
}