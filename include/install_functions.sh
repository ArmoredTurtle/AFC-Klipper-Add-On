#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

check_dirs() {
  # Debugging: Check if the directory exists
  if [ ! -d "${afc_path}/include/" ]; then
    echo "Directory ${afc_path}/include/ does not exist."
    exit 1
  fi

  # Debugging: Check if there are any files in the directory
  if [ -z "$(ls -A "${afc_path}/include/")" ]; then
    echo "No files found in ${afc_path}/include/"
    exit 1
  fi
}

link_extensions() {
  # Function to link AFC extensions to Klipper.
  # Uses the global variables:
  #   - KLIPPER_DIR: The path to the Klipper installation.
  #   - AFC_PATH: The path to the AFC Klipper Add-On repository.
  local message

  if [ -d "${klipper_dir}/klippy/extras" ]; then
    for extension in "${afc_path}"/extras/*.py; do
      ln -sf "${afc_path}/extras/$(basename "${extension}")" "${klipper_dir}/klippy/extras/$(basename "${extension}")"
    done
  else
    export message="AFC Klipper extensions not installed; Klipper extras directory not found."
  fi
}

unlink_extensions() {
  # Function to unlink AFC extensions from Klipper.
  # Uses the global variables:
  #   - KLIPPER_PATH: The path to the Klipper installation.
  #   - AFC_PATH: The path to the AFC Klipper Add-On repository.
  if [ -d "${klipper_dir}/klippy/extras" ]; then
    for extension in "${afc_path}"/extras/*.py; do
      rm -f "${klipper_dir}/klippy/extras/$(basename "${extension}")"
    done
  else
    print_msg ERROR "AFC Klipper extensions not uninstalled; Klipper extras directory not found."
    exit 1
  fi
}

copy_unit_files() {
  # If we are installing a BoxTurtle, then copy these files over.
  if [ "$installation_type" == "BoxTurtle (4-Lane)" ]; then
    cp "${afc_path}/templates/AFC_Hardware-AFC.cfg" "${afc_config_dir}/AFC_Hardware.cfg"
    cp "${afc_path}/templates/AFC_Turtle_1.cfg" "${afc_config_dir}/AFC_${boxturtle_name}.cfg"
    # If we are installing a NightOwl, then copy these files over.
  elif [ "$installation_type" == "NightOwl" ]; then
    cp "${afc_path}/templates/AFC_Hardware-NightOwl.cfg" "${afc_config_dir}/AFC_Hardware.cfg"
    cp "${afc_path}/templates/AFC_NightOwl_1.cfg" "${afc_config_dir}/AFC_NightOwl_1.cfg"
  fi
}

install_afc() {
  # Link the python extensions
  link_extensions
  copy_config
  copy_unit_files
  # Add our extensions to the klipper gitignore
  exclude_from_klipper_git
  # Include the AFC configuration files if selected
  if [ "$afc_includes" == True ]; then
    manage_include "${printer_config_dir}/printer.cfg" "add"
  fi
  # Update selected configuration values
  update_config_value "${afc_file}" "Type" "${installation_type}"
  update_config_value "${afc_file}" "park" "${park_macro}"
  update_config_value "${afc_file}" "poop" "${poop_macro}"
  update_config_value "${afc_file}" "form_tip" "${tip_forming}"
  update_config_value "${afc_file}" "tool_cut" "${toolhead_cutter}"
  update_config_value "${afc_file}" "hub_cut" "${hub_cutter}"
  update_config_value "${afc_file}" "kick" "${kick_macro}"
  update_config_value "${afc_file}" "wipe" "${wipe_macro}"
  if [ "$toolhead_sensor" == "Sensor" ]; then
    update_switch_pin "${afc_config_dir}/AFC_Hardware.cfg" "${toolhead_sensor_pin}"
  elif [ "$toolhead_sensor" == "Ramming" ]; then
    update_switch_pin "${afc_config_dir}/AFC_Hardware.cfg" "buffer"
  fi

  # When using Boxturtle as Installation Type then insert selected buffer configuration
  # NightOwl uses Turtleneck as default for now
  if [ "$installation_type" == "BoxTurtle (4-Lane)" ] || [ "$installation_type" == "BoxTurtle (8-Lane)" ]; then
    # Make sure the unit name is correct per the user choice
    if [ "$boxturtle_name" != "Turtle_1" ]; then
      find "$afc_config_dir" -type f -exec sed -i "s/Turtle_1/$boxturtle_name/g" {} +
    fi
    if [ "$buffer_type" == "TurtleNeck" ]; then
      query_tn_pins "TN"
      append_buffer_config "TurtleNeck" "$tn_advance_pin" "$tn_trailing_pin"
      add_buffer_to_extruder "${afc_config_dir}/AFC_${boxturtle_name}.cfg" "${boxturtle_name}"
    elif [ "$buffer_type" == "TurtleNeckV2" ]; then
      append_buffer_config "TurtleNeckV2"
      add_buffer_to_extruder "${afc_config_dir}/AFC_${boxturtle_name}.cfg" "${boxturtle_name}"
    fi
  fi
  check_and_append_prep "${afc_config_dir}/AFC.cfg"
  replace_varfile_path "${afc_config_dir}/AFC.cfg"
  update_moonraker_config

  export message
  export files_updated_or_installed="True"
  update_afc_version "$current_install_version"

  # Final step should be displaying any messages and exit cleanly.
  message="""
- AFC Configuration updated with selected options at ${afc_file}

- AFC-Klipper-Add-On python extensions installed to ${klipper_dir}/klippy/extras/
"""

if [ "$installation_type" == "BoxTurtle (4-Lane)" ] || [ "$installation_type" == "BoxTurtle (8-Lane)" ]; then
  message+="""
- Ensure you enter either your CAN bus or serial information in the ${afc_config_dir}/AFC_${boxturtle_name}.cfg file
  """
elif [ "$installation_type" == "NightOwl" ]; then
  message+="""
- Ensure you enter either your CAN bus or serial information in the ${afc_config_dir}/AFC_NightOwl_1.cfg file
  """
fi

if [ "$buffer_type" == "TurtleNeckV2" ]; then
  message+="""
- Ensure you add the correct serial information to the ${afc_config_dir}/mcu/TurtleNeckv2.cfg file
  """
fi

message+="""
You may now quit the script or return to the main menu.

If you would like to add any additional units, please restart to script to ensure the
current units are loaded correctly.
"""

}