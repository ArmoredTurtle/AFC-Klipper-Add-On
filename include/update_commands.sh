#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

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
      else
        # Append the include statement to the end of the file if save_config_line does not exist.
        echo "$include_statement" >> "$file_path"
      fi
    fi
  elif [ "$action" == "remove" ]; then
    # Remove the include statement if it is present in the file.
    if grep -qF "$include_statement" "$file_path"; then
      grep -vF "$include_statement" "$file_path" > "${file_path}.tmp"
      mv "${file_path}.tmp" "$file_path"
    fi
  fi
}
