#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

update_afc() {
  link_extensions
  remove_t_macros
  update_message="""
AFC Klipper Add-On updated successfully.
"""
  export update_message
  files_updated_or_installed="True"
}