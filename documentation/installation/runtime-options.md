## Usage

Usage instructions for the `install-afc.sh` script can be shown at any time by running the following command:

```bash
./install-afc.sh -h
```

An example output is shown below:

```bash
Usage: install-afc.sh [options]

Options:
  -a <moonraker address>      Specify the address of the Moonraker server (default: http://localhost)
  -k <path>                   Specify the path to the Klipper directory
  -m <moonraker config path>  Specify the path to the Moonraker config file (default: ~/printer_data/config/moonraker.conf)
  -n <moonraker port>         Specify the port of the Moonraker server (default: 7125)
  -s <klipper service name>   Specify the name of the Klipper service (default: klipper)
  -p <printer config dir>     Specify the path to the printer config directory (default: ~/printer_data/config)
  -b <branch>                 Specify the branch to use (default: main)
  -y <klipper venv dir>       Specify the klipper python venv dir (default: ~/klippy-env/bin)
  -h                          Display this help message

Example:
 ./install-afc.sh [-a <moonraker address>] [-k <klipper_path>] [-s <klipper_service_name>] [-m <moonraker_config_path>] [-n <moonraker_port>] [-p <printer_config_dir>] [-b <branch>] [-y <klipper venv dir>] [-h]
```

Each of these runtime options is explained in further detail below:

## Runtime / Command-Line Options

### `-a <moonraker address>`
=== "Description"  
    Specify the address of the Moonraker server. The default value is `http://localhost`.

=== "More information"  
    This option allows you to specify the address of the Moonraker server. If you are running Moonraker on a different 
    machine, you can specify the address here. Another common use case is if your Moonraker instance requires `https` 
    instead of `http` to connect.

### `-k <path>`
=== "Description"  
    Specify the path to the Klipper directory. The default value is `"$HOME/klipper"`.

=== "More information"
    This option allows you to specify the path to the Klipper directory. If you have installed Klipper in a non-standard 
    location, you can specify the path here.

### `-p <printer config dir>`
=== "Description"  
    Specify the path to the printer config directory. The default value is `"$HOME/printer_data/config"`.

=== "More information"
    This option allows you to specify the path to the printer config directory. If you have your printer configuration files 
    in a non-standard location, you can specify the path here. This is a common option for less common installations such as 
    when you are running multiple printers on a single system or have a non-standard configuration / Klipper installation for some
    printers such as Qidi.

### `-m <moonraker config path>`
=== "Description"  
    Specify the path to the Moonraker config file. The default value is `"$printer_config_dir/moonraker.conf"`.

=== "More information"
    This option allows you to specify the path to the Moonraker config file. If you have your Moonraker configuration file 
    in a non-standard location, you can specify the path here.

### `-n <moonraker port>`
=== "Description"  
    Specify the port of the Moonraker server. The default value is `7125`.

=== "More information"
    This option allows you to specify the port of the Moonraker server. If you have configured Moonraker to run on a 
    non-standard port, you can specify the port here.

### `-s <klipper service name>`
=== "Description"  
    Specify the name of the Klipper service. The default value is `klipper`.

=== "More information"
    This option allows you to specify the name of the Klipper service. If you have configured Klipper to run as a 
    different service name, you can specify the service name here. If you have multiple klipper instances running on a 
    single system, you may have configured them to run as different services. This option allows you to specify the
    service name for the Klipper instance you want to use with AFC. Common installation tools such as [Kiauh](https://github.com/dw-0/kiauh) allow
    you to configure multiple Klipper instances on a single system and will oftentimes use service names such as `klipper-1`
    or `klipper-2` if multiple instances are running. 

    !!! note
        If you are unsure of the service name, you can check the service name by running the following command:
        ```bash
        systemctl list-units --type=service | grep klipper
        ```
        This service name is also used for alternative firmware such as Kalico or Danger Klipper (deprecated), unless you
        have configured them to run as a different service name.

### `-b <branch>`
=== "Description"  
    Specify the branch to use. The default value is `main`.

=== "More information"
    This option allows you to specify the branch to use when using the `install-afc.sh` installation script. If you want to use a 
    specific branch, you can specify the branch name here. This is useful if you want to test new features or bug fixes before 
    they are merged into the main branch and is commonly used for development work or testing. Normal users should not need to
    specify this option.

### `-y <klipper venv dir>`
=== "Description"  
    Specify the klipper python venv dir. The default value is `"$HOME/klippy-env/bin"`.

=== "More information"
    This option allows you to specify the path to the Klipper python virtual environment directory. If you have installed Klipper
    in a python virtual environment and have installed it in a non-standard location, you can specify the path here. On the large
    majority of use-cases, this setting should not need to be changed, but the option is provided for users who have installed 
    the virtual environment in a non-standard location.

### `-h | Help`
=== "Description"  
    Display the help message.

=== "More information"
    This option displays the help message for the `install-afc.sh` script. This message provides a summary of the available 
    runtime options and how to use them. If you are unsure of how to use the script or need a reminder of the available options, 
    you can use this option to display the help message.

## Examples

### Example 1: Specifying the Moonraker address
```bash
./install-afc.sh -a https://192.168.1.120
```

This would use a Moonraker connection running at https://192.168.1.120

### Example 2: Specifying multiple options
```bash
./install-afc.sh -a https://192.168.1.120 -p 7126 -k /home/pi/klipper
```

You can specify multiple options, however, you cannot use the same option more than a single time.
