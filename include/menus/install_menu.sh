#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

install_menu() {
  local message
  local choice
  while true; do
    clear
    printf "      \e[49m                                    \e[m
                          \e[49m                                    \e[m
                          \e[49m                                    \e[m
                          \e[49m                                    \e[m
                          \e[49m            \e[38;5;3;49m▄\e[38;5;101;49m▄▄▄\e[38;5;101;48;5;101m▄▄▄\e[38;5;101;48;5;243m▄\e[38;5;101;49m▄▄▄\e[38;5;65;49m▄\e[49m            \e[m
                          \e[49m         \e[38;5;65;49m▄▄\e[38;5;239;48;5;236m▄\e[38;5;238;48;5;240m▄\e[48;5;101m           \e[38;5;101;48;5;101m▄▄▄\e[38;5;101;49m▄\e[49m        \e[m
                          \e[49m       \e[38;5;101;49m▄\e[38;5;101;48;5;101m▄\e[38;5;241;48;5;101m▄\e[38;5;236;48;5;241m▄\e[38;5;239;48;5;236m▄\e[38;5;242;48;5;236m▄\e[38;5;239;48;5;238m▄\e[38;5;236;48;5;241m▄\e[38;5;237;48;5;101m▄\e[38;5;59;48;5;101m▄\e[48;5;101m           \e[38;5;239;48;5;242m▄\e[38;5;236;49m▄\e[49m      \e[m
                          \e[49m  \e[38;5;149;49m▄\e[38;5;149;48;5;149m▄▄▄\e[48;5;149m  \e[38;5;149;48;5;143m▄\e[38;5;149;48;5;239m▄\e[38;5;143;48;5;240m▄\e[38;5;101;48;5;101m▄\e[48;5;101m  \e[38;5;101;48;5;65m▄\e[38;5;101;48;5;59m▄\e[38;5;101;48;5;237m▄\e[38;5;59;48;5;237m▄\e[38;5;236;48;5;240m▄\e[38;5;237;48;5;101m▄\e[38;5;239;48;5;101m▄▄▄\e[38;5;238;48;5;101m▄\e[38;5;237;48;5;101m▄▄▄▄\e[38;5;236;48;5;237m▄\e[38;5;65;48;5;240m▄\e[38;5;65;48;5;242m▄\e[38;5;65;49m▄\e[49m    \e[m
                          \e[38;5;149;49m▄\e[38;5;149;48;5;149m▄▄\e[38;5;107;48;5;149m▄\e[38;5;149;48;5;149m▄\e[48;5;149m   \e[38;5;143;48;5;149m▄▄\e[48;5;149m \e[38;5;149;48;5;149m▄\e[38;5;143;48;5;101m▄\e[38;5;101;48;5;101m▄\e[48;5;101m    \e[38;5;101;48;5;242m▄\e[38;5;238;48;5;237m▄\e[38;5;239;48;5;236m▄\e[38;5;101;48;5;238m▄\e[38;5;101;48;5;239m▄▄▄▄▄▄\e[38;5;238;48;5;236m▄\e[38;5;237;48;5;242m▄\e[48;5;101m \e[38;5;101;48;5;101m▄\e[38;5;65;49m▄\e[49m   \e[m
                          \e[38;5;149;48;5;149m▄\e[48;5;149m \e[38;5;238;48;5;241m▄\e[48;5;236m \e[38;5;242;48;5;101m▄\e[48;5;149m  \e[38;5;101;48;5;101m▄\e[48;5;236m \e[38;5;236;48;5;239m▄\e[38;5;149;48;5;149m▄\e[48;5;149m  \e[38;5;149;48;5;107m▄\e[38;5;101;48;5;101m▄\e[48;5;101m    \e[38;5;238;48;5;238m▄\e[38;5;239;48;5;239m▄\e[48;5;101m       \e[38;5;101;48;5;242m▄\e[38;5;239;48;5;236m▄\e[38;5;237;48;5;241m▄\e[48;5;101m \e[38;5;65;48;5;101m▄\e[38;5;149;48;5;149m▄▄▄\e[m
                          \e[38;5;149;48;5;149m▄\e[48;5;149m \e[38;5;149;48;5;107m▄\e[38;5;149;48;5;242m▄\e[38;5;143;48;5;143m▄\e[48;5;149m  \e[38;5;149;48;5;143m▄\e[38;5;143;48;5;240m▄\e[38;5;149;48;5;101m▄\e[48;5;149m    \e[38;5;143;48;5;101m▄\e[38;5;237;48;5;65m▄\e[38;5;242;48;5;101m▄\e[48;5;101m  \e[38;5;237;48;5;237m▄\e[38;5;240;48;5;239m▄\e[48;5;101m        \e[38;5;101;48;5;242m▄\e[38;5;237;48;5;236m▄\e[38;5;236;48;5;241m▄\e[38;5;236;48;5;238m▄\e[38;5;101;48;5;143m▄\e[38;5;149;48;5;149m▄\e[49;38;5;149m▀\e[m
                          \e[38;5;149;48;5;149m▄\e[48;5;149m  \e[38;5;149;48;5;149m▄\e[38;5;143;48;5;239m▄\e[38;5;242;48;5;242m▄\e[38;5;240;48;5;241m▄\e[38;5;143;48;5;237m▄\e[38;5;149;48;5;107m▄\e[48;5;149m      \e[38;5;101;48;5;239m▄\e[38;5;237;48;5;237m▄\e[38;5;237;48;5;242m▄\e[38;5;65;48;5;101m▄\e[48;5;237m \e[38;5;240;48;5;240m▄\e[48;5;101m    \e[38;5;242;48;5;101m▄\e[38;5;240;48;5;101m▄\e[38;5;238;48;5;101m▄\e[38;5;236;48;5;242m▄\e[38;5;236;48;5;239m▄\e[38;5;59;48;5;236m▄\e[38;5;101;48;5;237m▄\e[38;5;101;48;5;242m▄\e[38;5;242;48;5;101m▄\e[49;38;5;149m▀\e[49m \e[m
                          \e[49;38;5;149m▀\e[38;5;149;48;5;149m▄\e[48;5;149m             \e[38;5;143;48;5;143m▄\e[38;5;101;48;5;242m▄\e[38;5;242;48;5;237m▄\e[38;5;240;48;5;236m▄\e[38;5;238;48;5;236m▄\e[38;5;237;48;5;238m▄\e[38;5;237;48;5;239m▄\e[38;5;238;48;5;239m▄\e[38;5;240;48;5;239m▄\e[38;5;242;48;5;237m▄\e[38;5;65;48;5;236m▄\e[38;5;101;48;5;236m▄\e[38;5;101;48;5;238m▄\e[38;5;101;48;5;241m▄\e[38;5;101;48;5;101m▄▄\e[38;5;143;48;5;101m▄\e[38;5;149;48;5;101m▄\e[38;5;149;49m▄\e[49m  \e[m
                          \e[49m  \e[49;38;5;149m▀\e[38;5;149;48;5;149m▄▄\e[48;5;149m          \e[38;5;149;48;5;143m▄\e[48;5;101m       \e[38;5;101;48;5;101m▄▄\e[38;5;107;48;5;101m▄\e[38;5;143;48;5;101m▄▄\e[38;5;149;48;5;101m▄\e[38;5;149;48;5;143m▄\e[38;5;149;48;5;149m▄\e[48;5;149m  \e[38;5;149;48;5;149m▄\e[49m  \e[m
                          \e[49m   \e[38;5;149;49m▄\e[48;5;149m \e[38;5;149;48;5;149m▄▄▄▄▄\e[48;5;149m    \e[38;5;149;48;5;149m▄▄▄▄▄▄▄▄▄\e[49;38;5;149m▀▀▀\e[49m  \e[38;5;149;48;5;149m▄\e[48;5;149m    \e[38;5;149;48;5;149m▄\e[49m  \e[m
                          \e[49m   \e[38;5;149;48;5;149m▄\e[48;5;149m     \e[38;5;149;48;5;149m▄\e[49m      \e[38;5;149;48;5;149m▄\e[48;5;149m     \e[38;5;149;48;5;149m▄\e[49m     \e[49;38;5;149m▀▀▀▀▀\e[49m   \e[m
                          \e[49m   \e[49;38;5;149m▀▀▀▀▀▀\e[49;38;5;185m▀\e[49m      \e[38;5;149;48;5;149m▄\e[48;5;149m    \e[38;5;149;48;5;149m▄▄\e[49m             \e[m
                          \e[49m                                    \e[m
";
    printf "%b▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ \n" "$MENU_GREEN"
    printf "█%b                                    AFC Script Help      %b                            █\n" "$RESET" "$MENU_GREEN"
    printf "%b▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀%b \n" "$MENU_GREEN" "$RESET"
    printf "%b\n" "$message"
    printf "%b▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ \n" "$MENU_GREEN"
    printf "█%b            Please review the following options to configure your system%b             █\n" "$RESET" "$MENU_GREEN"
    printf "█%b        Use the provided option selection to cycle through available choices%b         █\n" "$RESET" "$MENU_GREEN"
    printf "%b▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀%b \n" "$MENU_GREEN" "$RESET"
    if [ "$files_updated_or_installed" == "False" ]; then
      printf "T. Installation Type: %s \n" "$installation_type"
      printf "1. Add the AFC includes to the your printer.cfg automatically? : %s \n" "$afc_includes"
      printf "2. Enable tip-forming? : %s \n" "$tip_forming"
      printf "3. Enable a toolhead cutter? : %s \n" "$toolhead_cutter"
      printf "4. Enable a hub cutter? : %s \n" "$hub_cutter"
      printf "5. Enable the kick macro? : %s \n" "$kick_macro"
      printf "6. Enable Park Macro? : %s \n" "$park_macro"
      printf "7. Enable Poop Macro? : %s \n" "$poop_macro"
      printf "8. Enable Wipe Macro? : %s \n" "$wipe_macro"
      printf "9. Use a toolhead sensor or ramming with a TN/TN2 buffer? : %s \n" "$toolhead_sensor"
      if [ "$toolhead_sensor" == "Sensor" ]; then
        if [ "$toolhead_sensor_pin" == "Unknown" ]; then
          printf "A. Toolhead sensor pin: ${RED}%s${RESET} \n" "$toolhead_sensor_pin"
        else
          printf "A. Toolhead sensor pin: %s \n" "$toolhead_sensor_pin"
        fi
      fi
      printf "B. Buffer type: %s \n" "$buffer_type"
    fi
    echo ""
    if [ "$files_updated_or_installed" == "False" ]; then
      printf "I. Install system with current selections\n"
    fi
    printf "M. Return to Main Menu\n"
    printf "Q. Quit\n"
    echo ""
    read -p "Enter your choice: " choice

    choice="${choice^^}"

    case $choice in
      T)
        message="Currently only BoxTurtle is supported, more coming soon!"
        export message ;;
      1)
        afc_includes=$([ "$afc_includes" == "True" ] && echo "False" || echo "True")
        message="AFC Includes $([ "$afc_includes" == "True" ] && echo "Enabled" || echo "Disabled")"
        export message ;;
      2)
        tip_forming=$([ "$tip_forming" == "True" ] && echo "False" || echo "True")
        message="Tip Forming $([ "$tip_forming" == "True" ] && echo "Enabled" || echo "Disabled")"
        export message ;;
      3)
        toolhead_cutter=$([ "$toolhead_cutter" == "True" ] && echo "False" || echo "True")
        message="Toolhead Cutter $([ "$toolhead_cutter" == "True" ] && echo "Enabled" || echo "Disabled")"
        export message ;;
      4)
        hub_cutter=$([ "$hub_cutter" == "True" ] && echo "False" || echo "True")
        message="Hub Cutter $([ "$hub_cutter" == "True" ] && echo "Enabled" || echo "Disabled")"
        export message ;;
      5)
        kick_macro=$([ "$kick_macro" == "True" ] && echo "False" || echo "True")
        message="Kick Macro $([ "$kick_macro" == "True" ] && echo "Enabled" || echo "Disabled")"
        export message ;;
      6)
        park_macro=$([ "$park_macro" == "True" ] && echo "False" || echo "True")
        message="Park Macro $([ "$park_macro" == "True" ] && echo "Enabled" || echo "Disabled")"
        export message ;;
      7)
        poop_macro=$([ "$poop_macro" == "True" ] && echo "False" || echo "True")
        message="Poop Macro $([ "$poop_macro" == "True" ] && echo "Enabled" || echo "Disabled")"
        export message ;;
      8)
        wipe_macro=$([ "$wipe_macro" == "True" ] && echo "False" || echo "True")
        message="Wipe Macro $([ "$wipe_macro" == "True" ] && echo "Enabled" || echo "Disabled")"
        export message ;;
      9)
        toolhead_sensor=$([ "$toolhead_sensor" == "Sensor" ] && echo "Ramming" || echo "Sensor")
        message=$([ "$toolhead_sensor" == "Sensor" ] && echo "Using toolhead sensor" || echo "Using ramming with a TN/TN2 buffer")
        export message ;;
      A)
        read -p "Enter toolhead sensor pin (Example: nhk:gpio13): " toolhead_sensor_pin
        message="Toolhead sensor pin set to $toolhead_sensor_pin"
        export message ;;
      B)
        buffer_type=$(
          case "$buffer_type" in
            "TurtleNeck") echo "TurtleNeckV2" ;;
            "TurtleNeckV2") echo "None" ;;
            "None" | *) echo "TurtleNeck" ;;
          esac
        )
        message="Buffer Type: $buffer_type"
        export message ;;
      Q) exit_afc_install ;;
      M) main_menu ;;
      I) install_afc ;;
      *) echo "Invalid selection" ;;
    esac
  done
}
