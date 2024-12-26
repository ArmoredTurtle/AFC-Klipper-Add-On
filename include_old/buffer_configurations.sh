#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

append_buffer_config() {
  local buffer_system="$1"
  local config_path="${AFC_CONFIG_PATH}/AFC_Hardware.cfg"
  local afc_config_path="${AFC_CONFIG_PATH}/AFC.cfg"
  local hardware_config_path="${AFC_CONFIG_PATH}/AFC_Hardware.cfg"
  local buffer_config=""
  local buffer_name=""
  tn_advance_pin=$2
  tn_trailing_pin=$3

  case "$buffer_system" in
    "TurtleNeck")
      buffer_config=$(cat <<EOF
[AFC_buffer TN]
advance_pin: ${tn_advance_pin}    # set advance pin
trailing_pin: ${tn_trailing_pin}  # set trailing pin
multiplier_high: 1.05   # default 1.05, factor to feed more filament
multiplier_low:  0.95   # default 0.95, factor to feed less filament
velocity: 100
EOF
)
      buffer_name="TN"
      ;;
    "TurtleNeckV2")
      buffer_config=$(cat <<'EOF'
[AFC_buffer TN2]
advance_pin: !turtleneck:ADVANCE
trailing_pin: !turtleneck:TRAILING
multiplier_high: 1.05   # default 1.05, factor to feed more filament
multiplier_low:  0.95   # default 0.95, factor to feed less filament
led_index: Buffer_Indicator:1
velocity: 100

[AFC_led Buffer_Indicator]
pin: turtleneck:RGB
chain_count: 1
color_order: GRBW
initial_RED: 0.0
initial_GREEN: 0.0
initial_BLUE: 0.0
initial_WHITE: 0.0
EOF
)
      buffer_name="TN2"
      ;;
    "AnnexBelay")
      buffer_config=$(cat <<'EOF'
[AFC_buffer Belay]
pin: mcu:BUFFER
distance: 12
velocity: 1000
accel: 1000
EOF
)
      buffer_name="Belay"
      ;;
    *)
      echo "Invalid BUFFER_SYSTEM: $buffer_system"
      return 1
      ;;
  esac

  # Check if the buffer configuration already exists in the config file
  print_msg INFO "  Checking if buffer configuration already exists in $config_path"
  if ! grep -qF "$(echo "$buffer_config" | head -n 1)" "$config_path"; then
    # Append the buffer configuration to the config file
    echo -e "\n$buffer_config" >> "$config_path"
  else
    print_msg INFO "  Buffer configuration already exists in $config_path. Skipping modification."
  fi

  # Add [include mcu/TurtleNeckv2.cfg] to AFC_Hardware.cfg if buffer_system is TurtleNeckV2 and not already present
  if [ "$buffer_system" == "TurtleNeckV2" ]; then
    if ! grep -qF "[include mcu/TurtleNeckv2.cfg]" "$hardware_config_path"; then
      awk '/\[include mcu\/.*\]/ {print; print "[include mcu/TurtleNeckv2.cfg]"; next}1' "$hardware_config_path" > temp && mv temp "$hardware_config_path"
      print_msg INFO "  Ensure you add the correct serial information to the ~/printer_data/config/AFC/mcu/TurtleNeckv2.cfg file"
    fi
  fi
}

add_buffer_to_extruder() {
  # Function to add a buffer configuration to the [AFC_extruder extruder] section in a configuration file.
  # Arguments:
  #   $1: file_path - The path to the configuration file.
  #   $2: buffer_name - The name of the buffer to be added.
  local file_path="$1"
  local buffer_name="$2"
  local section="[AFC_extruder extruder]"
  local buffer_line="buffer: $buffer_name"

  awk -v section="$section" -v buffer="$buffer_line" '
    BEGIN { in_section = 0 }
    # Match the start of the target section
    $0 == section {
      in_section = 1
      print $0
      next
    }
    # Insert buffer line before the first blank line within the target section
    in_section && /^$/ {
      print buffer
      in_section = 0
    }
    # End section processing if a new section starts
    in_section && /^\[.+\]/ { in_section = 0 }
    # Print all lines
    { print $0 }
  ' "$file_path" > "$file_path.tmp" && mv "$file_path.tmp" "$file_path"

  print_msg WARNING "  Added '$buffer_line' to the '$section' section in $file_path"
}

query_tn_pins() {
  # Function to query the user for the TurtleNeck pins.
  # Arguments:
  #   $1: buffer_name - The name of the buffer to be added.
  local buffer_name="$1"
  local input
  tn_advance_pin="^AFC:TN_ADV"
  tn_trailing_pin="^AFC:TN_TRL"

  print_msg INFO "  \n  Please enter the pin numbers for the TurtleNeck buffer '$buffer_name':"
  print_msg INFO "  (Leave blank to use the default values)"
  print_msg INFO "  Ensure you use a pull-up '^' if you are using a AFC end stop pin."
  print_msg INFO "  (Example: ^AFC:TN_ADV)"
  print_msg INFO "  (Example: ^AFC:TN_TRL)"

  read -p "  Enter the advance pin (default: $tn_advance_pin): " -r input
  if [ -n "$input" ]; then
    tn_advance_pin="$input"
  fi

  read -p "  Enter the trailing pin (default: $tn_trailing_pin): " -r input
  if [ -n "$input" ]; then
    tn_trailing_pin="$input"
  fi

  print_msg INFO "  Set ${buffer_name} Advance pin: $tn_advance_pin"
  print_msg INFO "  Set ${buffer_name} Trailing pin: $tn_trailing_pin"
}