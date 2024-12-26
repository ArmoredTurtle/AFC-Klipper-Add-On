#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

function update_moonraker_config() {
  # Function to update the Moonraker configuration with AFC-Klipper-Add-On settings.
  # Uses the global variables:
  #   - MOONRAKER_PATH: The path to the Moonraker installation.
  #   - MOONRAKER_UPDATE_CONFIG: The configuration settings to be added to Moonraker.

  local moonraker_config
  print_msg INFO "  Updating Moonraker config with AFC-Klipper-Add-On"

  # Check if the AFC-Klipper-Add-On configuration is already present in the Moonraker config file.
  moonraker_config=$(grep -c '\[update_manager afc-software\]' "${MOONRAKER_PATH}/moonraker.conf" || true)

  if [ "$moonraker_config" -eq 0 ]; then
    # If not present, append the configuration settings to the Moonraker config file.
    echo -e -n "\n${MOONRAKER_UPDATE_CONFIG}" >>"${MOONRAKER_PATH}/moonraker.conf"
    print_msg INFO "  Moonraker config updated"
    # Restart the Moonraker service to apply the new configuration.
    restart_service moonraker
  else
    # If already present, log that the configuration is already updated.
    print_msg INFO "  Moonraker config already updated"
  fi
}

manage_include() {
  # Function to manage the inclusion of AFC configuration files in a specified file.
  # Arguments:
  #   $1: file_path - The path to the file where the include statement should be added or removed.
  #   $2: action - The action to perform, either 'add' to add the include statement or 'remove' to remove it.
  #
  # The function uses the following local variables:
  #   - include_statement: The include statement to be added or removed.
  #   - save_config_line: A marker line in the file to help position the include statement.

  local file_path="$1"
  local action="$2"
  local include_statement="[include AFC/*.cfg]"
  local save_config_line="#*# <---------------------- SAVE_CONFIG ---------------------->"

  if [ "$action" == "add" ]; then
    # Add the include statement if it is not already present in the file.
    if ! grep -qF "$include_statement" "$file_path"; then
      if grep -qF "$save_config_line" "$file_path"; then
        # Insert the include statement before the save_config_line if it exists.
        sed -i "/$save_config_line/i $include_statement" "$file_path"
        print_msg INFO "  Added '$include_statement' in $file_path"
      else
        # Append the include statement to the end of the file if save_config_line does not exist.
        echo "$include_statement" >> "$file_path"
        print_msg INFO "  Added '$include_statement' to $file_path"
      fi
    else
      print_msg WARNING "  '$include_statement' is already present in $file_path, not adding."
    fi
  elif [ "$action" == "remove" ]; then
    # Remove the include statement if it is present in the file.
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

update_config_value() {
  # Function to update a specific key-value pair in a configuration file.
  # Arguments:
  #   $1: file_path - The path to the configuration file.
  #   $2: key - The key whose value needs to be updated.
  #   $3: new_value - The new value to be assigned to the key.

  local file_path="$1"
  local key="$2"
  local new_value="$3"

  # Create a temporary file to store the updated content.
  local temp_file=$(mktemp)

  # Read the configuration file line by line.
  while IFS= read -r line; do
    # Check if the line contains the key and capture any comment at the end of the line.
    if [[ "$line" =~ ^[[:space:]]*$key[[:space:]]*:[[:space:]]*([^[:space:]]+)[[:space:]]*(#.*)?$ ]]; then
      local comment="${BASH_REMATCH[2]}"
      # Write the updated key-value pair along with the comment to the temporary file.
      echo "$key: $new_value ${comment}" >> "$temp_file"
    else
      # Write the original line to the temporary file if it does not contain the key.
      echo "$line" >> "$temp_file"
    fi
  done < "$file_path"

  # Replace the original configuration file with the updated temporary file.
  mv "$temp_file" "$file_path"
}

update_switch_pin() {
  # Function to update the switch pin value in the filament switch sensor section of a configuration file.
  # Arguments:
  #   $1: file_path - The path to the configuration file.
  #   $2: new_value - The new value to be assigned to the switch pin.

  local file_path="$1"
  local new_value="$2"
  local temp_file=$(mktemp)
  local in_section=false

  # Read the configuration file line by line.
  while IFS= read -r line; do
    # Check if the line indicates the start of the filament switch sensor section.
    if [[ "$line" =~ ^\[AFC_extruder\ extruder\]$ ]]; then
      in_section=true
      echo "$line" >> "$temp_file"
    # If within the section and the line contains the switch pin, update its value.
    elif $in_section && [[ "$line" =~ ^pin_tool_start: ]]; then
      echo "pin_tool_start: $new_value" >> "$temp_file"
      in_section=false
    else
      # Write the original line to the temporary file if it does not match the above conditions.
      echo "$line" >> "$temp_file"
    fi
  done < "$file_path"

  # Replace the original configuration file with the updated temporary file.
  mv "$temp_file" "$file_path"
}

uncomment_board_type() {
  # Function to uncomment the board type configuration in a specified file.
  # Arguments:
  #   $1: file_path - The path to the configuration file.
  #   $2: board_type - The type of board to uncomment in the configuration file.
  #
  # The function uses the following local variables:
  #   - temp_file: A temporary file to store the updated content.

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

check_and_append_prep() {
  # Function to check for the presence of a specific section in a configuration file and append it if not present.
  # Arguments:
  #   $1: file_path - The path to the configuration file.
  local file_path="$1"
  local section="[AFC_prep]"
  local content="enable: True"

  if ! grep -qF "$section" "$file_path"; then
    echo -e "\n$section\n$content" >> "$file_path"
  fi
}

replace_varfile_path() {
  # Function to replace the VarFile path in a configuration file.
  # Arguments:
  #   $1: file_path - The path to the configuration file.
  #   $2: old_path - The old VarFile path to be replaced.
  #   $3: new_path - The new VarFile path to replace with.
  local file_path="$1"
  local old_path="VarFile: ../printer_data/config/AFC/AFC.var"
  local new_path="VarFile: ${AFC_CONFIG_PATH}/AFC.var"

  if grep -qF "$old_path" "$file_path"; then
    sed -i "s|$old_path|$new_path|" "$file_path"
  fi
}

remove_t_macros() {
  # Function to remove the T macros from the configuration file.
  local t_macro
  local t_macros

  t_macros=$(grep -o -E 'T[0-9]+' "${AFC_CONFIG_PATH}/macros/AFC_macros.cfg")

  for t_macro in $t_macros; do
    crudini --del "${AFC_CONFIG_PATH}"/macros/AFC_macros.cfg "gcode_macro $t_macro"
  done
}