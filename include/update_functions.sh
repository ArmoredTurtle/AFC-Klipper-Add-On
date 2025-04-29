#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

update_afc() {
  local macro update_macros confirm_update_macros
  read -p "Do you want to update the AFC provided macros? (y/n): " update_macros
  update_macros="${update_macros,,}"
  if [[ "$update_macros" == "y" ]]; then
    print_msg WARNING "Updating macros will overwrite any custom changes you have made to these macros."
    print_msg WARNING "This includes the brush, cut, kick, park, afc_macros, and poop macros."
    read -p "Please confirm you want to update these macros: (y/n): " confirm_update_macros
    confirm_update_macros="${confirm_update_macros,,}"
    if [[ "$confirm_update_macros" == "y" ]]; then
      for macro in "Brush" "Cut" "Kick" "Park" "Poop" "AFC_macros"; do
        rm -rf "${afc_config_dir}/macros/${macro}.cfg"
      done
      if cp "${afc_path}/config/macros/"*.cfg "${afc_config_dir}/macros/"; then
        update_message+="""
AFC Macros updated successfully.
        """
      else
        update_message+="""
AFC Macros update failed.
        """
      fi
    fi
  fi
  link_extensions
  remove_t_macros
  update_message+="""
AFC Klipper Add-On updated successfully.
"""
  export update_message
  files_updated_or_installed="True"
}