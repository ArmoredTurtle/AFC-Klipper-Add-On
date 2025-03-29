#!/usr/bin/env bash
# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

utilities_menu() {
  local choice
  while true; do
    clear
printf "\e[49m           \e[38;5;239;49m▄\e[38;5;101;49m▄\e[38;5;242;49m▄\e[38;5;237;49m▄\e[49m                              \e[m
\e[49m        \e[38;5;240;49m▄\e[38;5;143;49m▄\e[38;5;185;48;5;240m▄\e[38;5;221;48;5;143m▄\e[38;5;221;48;5;221m▄▄\e[38;5;221;48;5;185m▄\e[38;5;221;48;5;101m▄\e[38;5;143;49m▄\e[38;5;101;49m▄\e[49m                    \e[38;5;231;48;5;16m╭─────────────────────────╮              \e[m
\e[49m      \e[38;5;101;49m▄\e[38;5;143;48;5;65m▄\e[38;5;227;48;5;143m▄\e[38;5;221;48;5;185m▄\e[38;5;221;48;5;227m▄\e[38;5;221;48;5;221m▄▄▄▄▄▄\e[38;5;221;48;5;179m▄\e[38;5;137;48;5;101m▄\e[49m                   \e[38;5;231;48;5;16m│ Lets change stuff up... │          \e[m
\e[49m    \e[38;5;101;49m▄\e[38;5;222;48;5;107m▄\e[38;5;227;48;5;185m▄\e[38;5;221;48;5;227m▄▄\e[38;5;221;48;5;221m▄▄▄▄▄▄\e[38;5;220;48;5;221m▄▄\e[38;5;220;48;5;220m▄\e[38;5;179;48;5;185m▄\e[38;5;94;48;5;241m▄\e[49m     \e[38;5;59;49m▄\e[38;5;143;48;5;59m▄\e[38;5;143;48;5;239m▄\e[38;5;107;49m▄\e[38;5;101;49m▄▄\e[38;5;242;49m▄\e[49m      \e[38;5;231;48;5;16m╰─────────────────────────╯        \e[m
\e[49m \e[38;5;238;49m▄\e[38;5;101;48;5;59m▄\e[38;5;179;48;5;143m▄\e[38;5;185;48;5;227m▄\e[38;5;221;48;5;221m▄▄▄▄▄▄▄\e[38;5;220;48;5;221m▄▄\e[38;5;220;48;5;220m▄\e[38;5;221;48;5;220m▄\e[38;5;172;48;5;221m▄\e[38;5;136;48;5;178m▄\e[38;5;130;48;5;136m▄\e[38;5;94;48;5;94m▄\e[49m   \e[38;5;241;49m▄\e[38;5;101;48;5;101m▄\e[38;5;101;48;5;3m▄\e[38;5;187;48;5;101m▄\e[38;5;101;48;5;101m▄\e[38;5;58;48;5;143m▄\e[38;5;143;48;5;143m▄\e[38;5;143;48;5;101m▄\e[38;5;101;48;5;242m▄\e[38;5;236;48;5;242m▄\e[49m            \e[m
\e[49m \e[38;5;94;48;5;94m▄\e[38;5;136;48;5;136m▄▄▄▄\e[38;5;136;48;5;221m▄\e[38;5;179;48;5;221m▄\e[38;5;221;48;5;221m▄\e[38;5;220;48;5;221m▄▄\e[38;5;214;48;5;220m▄▄\e[38;5;178;48;5;220m▄\e[38;5;136;48;5;214m▄\e[38;5;136;48;5;136m▄\e[38;5;130;48;5;136m▄\e[38;5;130;48;5;130m▄▄\e[38;5;239;48;5;94m▄\e[38;5;238;49m▄\e[49m \e[38;5;242;48;5;238m▄\e[38;5;3;48;5;101m▄\e[38;5;101;48;5;101m▄\e[38;5;3;48;5;101m▄\e[38;5;137;48;5;223m▄\e[38;5;137;48;5;240m▄\e[38;5;101;48;5;58m▄\e[38;5;101;48;5;137m▄\e[38;5;101;48;5;143m▄\e[38;5;143;48;5;143m▄\e[38;5;107;48;5;101m▄\e[49m            \e[m
\e[49m \e[38;5;237;48;5;58m▄\e[38;5;136;48;5;136m▄▄▄▄▄▄\e[38;5;136;48;5;178m▄\e[38;5;214;48;5;214m▄\e[38;5;214;48;5;220m▄\e[38;5;178;48;5;214m▄\e[38;5;136;48;5;178m▄\e[38;5;130;48;5;136m▄\e[38;5;58;48;5;130m▄\e[38;5;94;48;5;130m▄\e[38;5;130;48;5;130m▄\e[38;5;237;48;5;94m▄\e[38;5;238;48;5;58m▄▄\e[38;5;58;48;5;58m▄▄▄\e[38;5;242;48;5;242m▄\e[38;5;3;48;5;3m▄\e[38;5;3;48;5;101m▄\e[38;5;58;48;5;101m▄\e[38;5;101;48;5;101m▄▄▄\e[38;5;137;48;5;101m▄\e[38;5;137;48;5;143m▄\e[38;5;143;48;5;143m▄\e[38;5;123;48;5;117m▄\e[49m           \e[m
\e[49m  \e[38;5;238;48;5;58m▄\e[38;5;94;48;5;136m▄\e[38;5;136;48;5;136m▄\e[48;5;136m   \e[38;5;136;48;5;136m▄▄\e[38;5;130;48;5;178m▄\e[38;5;136;48;5;136m▄\e[38;5;130;48;5;136m▄\e[38;5;94;48;5;94m▄\e[38;5;52;48;5;58m▄\e[38;5;58;48;5;94m▄\e[38;5;130;48;5;136m▄\e[38;5;136;48;5;58m▄\e[38;5;58;48;5;236m▄\e[38;5;236;48;5;238m▄\e[38;5;238;48;5;238m▄\e[38;5;237;48;5;239m▄\e[38;5;236;48;5;238m▄\e[38;5;238;48;5;58m▄\e[38;5;3;48;5;101m▄\e[38;5;101;48;5;101m▄\e[38;5;101;48;5;58m▄\e[38;5;3;48;5;237m▄\e[38;5;95;48;5;238m▄\e[38;5;236;48;5;238m▄\e[38;5;235;48;5;58m▄\e[38;5;58;48;5;101m▄\e[38;5;242;48;5;101m▄\e[49m            \e[m
\e[49m   \e[38;5;237;48;5;94m▄\e[38;5;58;48;5;136m▄\e[38;5;136;48;5;136m▄▄\e[38;5;130;48;5;136m▄▄\e[38;5;130;48;5;130m▄▄▄\e[38;5;94;48;5;130m▄\e[38;5;235;48;5;58m▄\e[38;5;235;48;5;235m▄▄\e[38;5;235;48;5;58m▄\e[38;5;58;48;5;94m▄\e[38;5;94;48;5;136m▄\e[38;5;130;48;5;94m▄\e[38;5;94;48;5;237m▄\e[38;5;236;48;5;235m▄\e[38;5;237;48;5;235m▄\e[38;5;58;48;5;238m▄\e[38;5;3;48;5;3m▄\e[38;5;3;48;5;101m▄\e[38;5;58;48;5;242m▄\e[38;5;237;48;5;3m▄\e[38;5;238;48;5;101m▄\e[38;5;239;48;5;3m▄\e[38;5;240;48;5;58m▄\e[38;5;239;48;5;65m▄\e[49m             \e[m
\e[49m     \e[49;38;5;58m▀\e[38;5;58;48;5;130m▄\e[38;5;94;48;5;130m▄▄\e[38;5;130;48;5;130m▄\e[38;5;58;48;5;94m▄\e[38;5;235;48;5;94m▄\e[38;5;236;48;5;235m▄▄\e[38;5;235;48;5;236m▄\e[38;5;236;48;5;235m▄▄\e[38;5;234;48;5;235m▄\e[38;5;235;48;5;52m▄\e[38;5;52;48;5;94m▄\e[38;5;58;48;5;130m▄\e[38;5;94;48;5;94m▄\e[38;5;58;48;5;238m▄\e[38;5;237;48;5;58m▄\e[38;5;239;48;5;242m▄\e[38;5;58;48;5;242m▄\e[38;5;239;48;5;58m▄\e[38;5;237;48;5;58m▄\e[38;5;240;49m▄\e[49m                \e[m
\e[49m        \e[49;38;5;235m▀\e[38;5;239;48;5;233m▄\e[38;5;237;48;5;236m▄\e[48;5;236m \e[38;5;236;48;5;236m▄\e[38;5;235;48;5;236m▄\e[38;5;237;48;5;235m▄\e[38;5;235;48;5;236m▄\e[38;5;235;48;5;234m▄\e[38;5;58;48;5;235m▄\e[38;5;242;48;5;238m▄\e[38;5;58;48;5;236m▄\e[38;5;94;48;5;52m▄\e[38;5;58;48;5;58m▄\e[38;5;58;48;5;94m▄\e[38;5;58;48;5;58m▄\e[38;5;3;48;5;237m▄\e[38;5;143;48;5;238m▄\e[38;5;137;48;5;58m▄\e[38;5;143;48;5;58m▄\e[38;5;3;48;5;240m▄\e[38;5;242;49m▄\e[49m               \e[m
\e[49m         \e[38;5;237;48;5;237m▄\e[38;5;236;48;5;237m▄\e[38;5;236;48;5;236m▄\e[38;5;235;48;5;236m▄\e[38;5;235;48;5;235m▄\e[38;5;235;48;5;236m▄\e[38;5;234;48;5;234m▄\e[38;5;58;48;5;238m▄\e[38;5;3;48;5;242m▄\e[38;5;101;48;5;3m▄\e[38;5;58;48;5;58m▄\e[38;5;131;48;5;131m▄\e[38;5;94;48;5;94m▄\e[38;5;101;48;5;58m▄\e[38;5;101;48;5;101m▄▄\e[38;5;101;48;5;107m▄\e[38;5;101;48;5;143m▄\e[38;5;107;48;5;101m▄\e[38;5;58;48;5;101m▄\e[38;5;101;48;5;107m▄\e[38;5;143;48;5;107m▄\e[38;5;143;48;5;240m▄\e[38;5;101;49m▄\e[38;5;239;49m▄\e[49m           \e[m
\e[49m         \e[38;5;236;48;5;237m▄\e[38;5;236;48;5;236m▄▄\e[38;5;235;48;5;235m▄\e[38;5;235;48;5;236m▄\e[38;5;234;48;5;234m▄\e[38;5;236;48;5;236m▄\e[38;5;58;48;5;58m▄\e[48;5;3m \e[38;5;101;48;5;101m▄\e[38;5;101;48;5;3m▄\e[38;5;101;48;5;101m▄▄▄\e[38;5;3;48;5;101m▄\e[38;5;242;48;5;3m▄\e[38;5;58;48;5;3m▄▄▄\e[38;5;95;48;5;94m▄\e[38;5;101;48;5;3m▄\e[38;5;101;48;5;143m▄\e[38;5;143;48;5;143m▄▄\e[38;5;107;48;5;243m▄\e[38;5;238;49m▄\e[49m          \e[m
\e[49m         \e[38;5;236;48;5;237m▄\e[38;5;235;48;5;235m▄▄▄▄\e[38;5;234;48;5;234m▄\e[38;5;58;48;5;58m▄\e[38;5;237;48;5;238m▄\e[38;5;239;48;5;242m▄\e[38;5;58;48;5;101m▄\e[38;5;58;48;5;3m▄▄▄\e[38;5;58;48;5;242m▄\e[38;5;239;48;5;58m▄\e[38;5;58;48;5;58m▄\e[38;5;94;48;5;58m▄\e[38;5;137;48;5;58m▄\e[38;5;94;48;5;236m▄\e[38;5;239;48;5;101m▄\e[38;5;101;48;5;95m▄\e[38;5;240;48;5;101m▄\e[38;5;3;48;5;107m▄\e[38;5;101;48;5;143m▄\e[38;5;242;48;5;101m▄\e[38;5;238;48;5;59m▄\e[49m          \e[m
\e[49m         \e[38;5;236;48;5;235m▄\e[38;5;234;48;5;235m▄\e[38;5;234;48;5;234m▄▄▄▄\e[38;5;94;48;5;94m▄\e[38;5;94;48;5;58m▄\e[38;5;58;48;5;237m▄\e[38;5;236;48;5;238m▄\e[38;5;237;48;5;238m▄\e[38;5;237;48;5;239m▄\e[38;5;238;48;5;239m▄\e[38;5;94;48;5;238m▄\e[38;5;131;48;5;58m▄\e[38;5;137;48;5;131m▄\e[38;5;137;48;5;137m▄▄\e[38;5;3;48;5;94m▄\e[49;38;5;237m▀\e[38;5;237;48;5;238m▄\e[38;5;241;48;5;95m▄\e[38;5;237;48;5;59m▄\e[38;5;58;48;5;238m▄\e[38;5;136;48;5;238m▄\e[38;5;136;49m▄\e[38;5;58;49m▄\e[49m         \e[m
\e[49m          \e[38;5;234;48;5;234m▄▄\e[38;5;235;48;5;234m▄\e[38;5;234;48;5;234m▄\e[38;5;236;48;5;235m▄\e[38;5;94;48;5;94m▄▄▄▄\e[38;5;94;48;5;58m▄\e[38;5;94;48;5;94m▄▄\e[38;5;131;48;5;131m▄\e[38;5;131;48;5;137m▄\e[38;5;137;48;5;137m▄▄\e[38;5;3;48;5;137m▄\e[38;5;237;48;5;58m▄\e[49m   \e[49;38;5;235m▀\e[38;5;235;48;5;58m▄\e[38;5;52;48;5;94m▄\e[38;5;94;48;5;130m▄\e[38;5;58;48;5;136m▄\e[38;5;236;48;5;58m▄\e[49m        \e[m
\e[49m          \e[38;5;236;48;5;235m▄\e[38;5;235;48;5;235m▄\e[38;5;235;48;5;234m▄\e[38;5;238;48;5;235m▄\e[38;5;58;48;5;237m▄\e[38;5;58;48;5;238m▄\e[38;5;237;48;5;58m▄\e[38;5;94;48;5;94m▄▄▄▄▄\e[48;5;94m \e[38;5;131;48;5;94m▄\e[38;5;94;48;5;137m▄\e[38;5;3;48;5;101m▄\e[38;5;143;48;5;101m▄\e[38;5;101;48;5;64m▄\e[49m     \e[49;38;5;235m▀\e[38;5;235;48;5;52m▄\e[38;5;236;48;5;52m▄\e[49;38;5;236m▀\e[49m        \e[m
\e[49m         \e[49;38;5;238m▀\e[38;5;237;48;5;58m▄\e[38;5;235;48;5;236m▄\e[38;5;239;48;5;237m▄\e[38;5;58;48;5;58m▄\e[38;5;242;48;5;242m▄▄\e[38;5;58;48;5;239m▄\e[38;5;236;48;5;58m▄\e[38;5;237;48;5;94m▄▄\e[38;5;58;48;5;94m▄\e[38;5;237;48;5;94m▄▄\e[38;5;237;48;5;58m▄\e[38;5;58;48;5;239m▄\e[38;5;3;48;5;3m▄\e[38;5;101;48;5;143m▄\e[38;5;107;48;5;101m▄\e[38;5;58;49m▄\e[49m                \e[m
\e[49m          \e[38;5;236;49m▄\e[38;5;237;48;5;237m▄\e[38;5;58;48;5;239m▄\e[38;5;58;48;5;242m▄\e[38;5;242;48;5;3m▄\e[38;5;3;48;5;3m▄\e[38;5;58;48;5;58m▄\e[38;5;237;48;5;237m▄\e[38;5;238;48;5;238m▄\e[49;38;5;236m▀\e[49m  \e[38;5;236;48;5;236m▄\e[38;5;237;48;5;237m▄\e[38;5;239;48;5;58m▄\e[38;5;58;48;5;3m▄\e[38;5;101;48;5;101m▄\e[38;5;101;48;5;107m▄\e[38;5;3;48;5;58m▄\e[38;5;58;49m▄\e[49m               \e[m
\e[49m          \e[38;5;236;48;5;237m▄\e[38;5;238;48;5;238m▄\e[38;5;58;48;5;58m▄\e[38;5;241;48;5;58m▄\e[38;5;101;48;5;242m▄\e[38;5;101;48;5;101m▄\e[38;5;58;48;5;58m▄\e[49m     \e[49;38;5;235m▀\e[38;5;235;48;5;237m▄\e[38;5;237;48;5;238m▄\e[38;5;238;48;5;58m▄\e[38;5;240;48;5;242m▄\e[38;5;101;48;5;242m▄\e[38;5;137;48;5;143m▄\e[38;5;101;48;5;101m▄\e[49m               \e[m
\e[49m          \e[38;5;237;48;5;236m▄\e[38;5;101;48;5;101m▄\e[38;5;59;48;5;59m▄\e[38;5;101;48;5;101m▄\e[38;5;95;48;5;101m▄\e[38;5;101;48;5;101m▄\e[38;5;242;48;5;101m▄\e[49m        \e[49;38;5;233m▀\e[49;38;5;236m▀\e[49;38;5;240m▀\e[49;38;5;235m▀\e[49m                \e[m
\e[49m             \e[49;38;5;234m▀\e[49m                               \e[m
\e[49m                                             \e[m
";
    printf "%b▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ \n" "$MENU_GREEN"
    printf "█%b                                 System Utilities Menu    %b                           █\n" "$RESET" "$MENU_GREEN"
    printf "█%b                                    AFC Script Help      %b                            █\n" "$RESET" "$MENU_GREEN"
    printf "%b▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀%b \n" "$MENU_GREEN" "$RESET"
    printf "%b\n" "$unit_message"
    printf "%b▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ \n" "$MENU_GREEN"
    printf "█%b            Please review the following options to update your system%b                █\n" "$RESET" "$MENU_GREEN"
    printf "█%b        Use the provided option selection to cycle through available choices%b         █\n" "$RESET" "$MENU_GREEN"
    printf "%b▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀%b \n" "$MENU_GREEN" "$RESET"
    echo ""
    printf "R. Rename existing unit\n"
    echo ""
    printf "M. Return to Main Menu\n"
    printf "Q. Quit\n"
    echo ""
    read -p "Enter your choice: " choice

    choice="${choice^^}"

    case $choice in
      R)
        rename_unit_prompt ;;
      M)
        main_menu ;;
      Q)
        exit_afc_install ;;
      *)
        message="Invalid selection, please try again."
        ;;
    esac
  done
}