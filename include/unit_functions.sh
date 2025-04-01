#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

name_unit() {
  while true; do
    read -p "Enter name for unit (Default: Turtle_1): " boxturtle_name
    boxturtle_name=${boxturtle_name:-Turtle_1}

    if [[ "$boxturtle_name" =~ ^[a-zA-Z0-9_-]+$ ]] && [[ ${#boxturtle_name} -le 24 ]]; then
      break
    else
      echo "Invalid input. The unit name must consist of only a-z, A-Z, 0-9, -, and _ and be no more than 24 characters long."
    fi
  done

  export message="Naming unit $boxturtle_name"
}

name_additional_unit() {
  if [ "$installation_type" == "HTLF" ]; then
    while true; do
      read -p "Enter name for unit (Default: HTLF_1): " boxturtle_name
      boxturtle_name=${boxturtle_name:-HTLF_1}

      if [[ "$boxturtle_name" =~ ^[a-zA-Z0-9_-]+$ ]] && [[ ${#boxturtle_name} -le 24 ]]; then
        break
      else
        echo "Invalid input. The unit name must consist of only a-z, A-Z, 0-9, -, and _ and be no more than 24 characters long."
      fi
    done
  elif [ "$installation_type" == "BoxTurtle (4-Lane)" ]; then
    while true; do
      read -p "Enter name for unit (Default: Turtle_2): " boxturtle_name
      boxturtle_name=${boxturtle_name:-Turtle_2}

      if [[ "$boxturtle_name" =~ ^[a-zA-Z0-9_-]+$ ]] && [[ ${#boxturtle_name} -le 24 ]]; then
        break
      else
        echo "Invalid input. The unit name must consist of only a-z, A-Z, 0-9, -, and _ and be no more than 24 characters long."
      fi
    done
  fi
  export turtle_renamed="True"
  export boxturtle_name
  export message="Naming unit $boxturtle_name"
}

rename_unit_prompt() {
  while true; do
    read -p "Enter name of unit you would like to replace (Default: Turtle_1): " old_unit_name
    old_unit_name=${old_unit_name:-Turtle_1}

    if [[ "$old_unit_name" =~ ^[a-zA-Z0-9_-]+$ ]] && [[ ${#old_unit_name} -le 24 ]]; then
      break
    else
      echo "Invalid input. The unit name must consist of only a-z, A-Z, 0-9, -, and _ and be no more than 24 characters long."
    fi
  done

  while true; do
    read -p "Enter new name for unit (Default: Turtle_2): " new_unit_name
    new_unit_name=${new_unit_name:-Turtle_2}

    if [[ "$new_unit_name" =~ ^[a-zA-Z0-9_-]+$ ]] && [[ ${#new_unit_name} -le 24 ]]; then
      break
    else
      echo "Invalid input. The unit name must consist of only a-z, A-Z, 0-9, -, and _ and be no more than 24 characters long."
    fi
  done

  export unit_message="Renaming unit $old_unit_name to $new_unit_name"

  if [ ! -f "$afc_config_dir/AFC_${old_unit_name}.cfg" ]; then
    export unit_message="Unit $old_unit_name not found, please enter a valid unit name."
    return
  else
    replace_unit_name "$old_unit_name" "$new_unit_name"
  fi
}

replace_unit_name() {
  local old_unit_name="$1"
  local new_unit_name="$2"

  find "$afc_config_dir" -type f -exec sed -i "s/$old_unit_name/$new_unit_name/g" {} +
  find "$afc_config_dir" -type f -name "AFC_${old_unit_name}.cfg" -exec mv {} "$afc_config_dir/AFC_${new_unit_name}.cfg" \;
}

verify_name_not_in_use() {
  local unit_name="$1"
  if grep -qR "$unit_name" "$afc_config_dir"; then
    export message="Unit $unit_name already exists, please enter a unique unit name."
    export invalid_name="True"
    return
  fi
}

install_additional_unit() {
  if [ "$installation_type" == "BoxTurtle (4-Lane)" ]; then
    cp "${afc_path}/templates/AFC_Turtle_1.cfg" "${afc_config_dir}/AFC_${boxturtle_name}.cfg"
    find "$afc_config_dir/AFC_${boxturtle_name}.cfg" -type f -exec sed -i "s/Turtle_1/$boxturtle_name/g" {} +
    cp "${afc_path}"/config/mcu/AFC_Lite.cfg "${afc_config_dir}"/mcu/AFC_"${boxturtle_name}"_mcu.cfg
    sed -i "s/include mcu\/AFC_Lite.cfg/include mcu\/AFC_${boxturtle_name}_mcu.cfg/g" "${afc_config_dir}"/AFC_"${boxturtle_name}".cfg
    # If we are installing a NightOwl, then copy these files over.
  elif [ "$installation_type" == "NightOwl" ]; then
    cp "${afc_path}/templates/AFC_NightOwl_1.cfg" "${afc_config_dir}/AFC_${boxturtle_name}.cfg"
  elif [ "$installation_type" == "HTLF" ]; then
    cp "${afc_path}/templates/AFC_HTLF_1-$htlf_board_type.cfg" "${afc_config_dir}/AFC_${boxturtle_name}.cfg"
  fi
}