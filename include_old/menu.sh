printer_config_dir="$HOME/printer_data/config"
klipper_dir="$HOME/klipper"
afc_path="$HOME/AFC-Klipper-Add-On"
moonraker_config_file="$printer_config_dir/moonraker.conf"
klipper_service="klipper"
branch="main"
prior_installation="False"
installation_type="BoxTurtle"
park_macro="True"
poop_macro="True"

main() {
  while true; do
    clear
    echo "AFC Klipper Add-On Installation / Configuration Menu"
    printf "Prior AFC-Klipper-Add-On installation detected: %s\n" $prior_installation
    echo "------------------------------------------------------------------------------------------------"
    echo "|                                   System Variables                                           |"
    echo "------------------------------------------------------------------------------------------------"
    printf "1. Printer Config Directory : %s \n" $printer_config_dir
    printf "2. Klipper Directory        : %s \n" $klipper_dir
    printf "3. Moonraker Config File    : %s \n" $moonraker_config_file
    printf "4. AFC Path                 : %s \n" $afc_path
    printf "5. Klipper Service          : %s \n" $klipper_service
    printf "6. Branch                   : %s \n" $branch
    echo "------------------------------------------------------------------------------------------------"
    echo "|                                   AFC Configuration                                          |"
    echo "------------------------------------------------------------------------------------------------"
    printf "A. Installation Type  : %s\n" $installation_type
    printf "B. Enable Park Macro? : %s\n" $park_macro
    printf "C. Enable Poop Macro? : %s\n" $poop_macro
    echo "X. Exit"

    read -p "Enter your choice: " choice

    choice="${choice^^}"
    case $choice in
      1)
        read -p "Enter Printer Config Directory: " printer_config_dir
        ;;
      2)
        read -p "Enter Klipper Directory: " klipper_dir
        ;;
      3)
        read -p "Enter Moonraker Config File: " moonraker_config_file
        ;;
      4)
        read -p "Enter AFC Path: " afc_path
        ;;
      5)
        read -p "Enter Klipper Service: " klipper_service
        ;;
      6)
        read -p "Enter Branch: " branch
        ;;
      A)
        read -p "Enter Installation Type: " installation_type
        ;;
      B)
        read -p "Enable Park Macro? (True/False): " park_macro
        ;;
      C)
        read -p "Enable Poop Macro? (True/False): " poop_macro
        ;;
      X)
        break
        ;;
      *)
        echo "Invalid option"
        ;;
    esac

  done
}

main