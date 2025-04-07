# Uninstall the AFC-Klipper-Add-On 

While we are sad to see you go, uninstalling the AFC-Klipper-Add-On is a simple process.

## Uninstalling the AFC-Klipper-Add-On

1. Stop the `Klipper` service 
   - `sudo service klipper stop`

2. Navigate to the `AFC-Klipper-Add-On` directory
   - `cd ~/klipper_extras/AFC-Klipper-Add-On`

3. Uninstall the `AFC-Klipper-Add-On` using the installation script.
   - `./install-afc.sh`

When the installation script starts, on the main menu there is an option for `R. Remove AFC Klipper Add-On`.

Selecting this option will make a backup of your `~/printer_data/config/AFC` directory and then remove the symlinks 
that were installed as part of the installation process.

You can verify the uninstallation process was successful by running the following command:

```bash
ls -l ~/klipper/klippy/extras/AFC*.py
```

No files should be returned. If by some chance, files are present, you can remove them manually. 

The uninstallation process will also remove the `[include AFC/*.cfg]` from your `printer.cfg` file.

You may need to manually remove any configuration from your `moonraker.conf` file.

Once everything is removed, don't forget to restart the `Klipper` service:

```bash
sudo service klipper start
```

