---
title: AFC-Klipper-Add-On Software Installation Guide
---

# AFC-Klipper-Add-On Software Installation Guide

This Klipper plugin is for use with modern filament control systems such as BoxTurtle, NightOwl etc.

More information about BoxTurtle can be found [here](https://github.com/ArmoredTurtle/BoxTurtle)

!!! note

    All examples in this section assume that you are running the command on your SBC that the `AFC-Klipper-Add-On` software
    is installed on.


## Installation

### Step 1: Prerequisites

The `AFC-Klipper-Add-On` has the following pre-requisites:

- Klipper
- Moonraker
- WebUI (Mainsail or Fluidd)
- Python3 >= 3.8

The following software prerequisites should also be available on your system: 

- jq
- crudini
- git

With a Debian based system, you can install these prerequisites with the following command:

```bash
sudo apt-get install jq crudini git
```

### Step 2: Clone the git repository

The `AFC-Klipper-Add-On` software is available on GitHub. You can clone the repository with the following command:

=== "Command Line"
    ```bash
    cd ~
    git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
    cd AFC-Klipper-Add-On
    ```
=== "Explanation"

    Running these commands will clone the `AFC-Klipper-Add-On` repository to your home directory and change to the directory.

### Step 3: Start the installation process

From within the `AFC-Klipper-Add-On` directory, you can start the installation process with the following command:

```bash
./install-afc.sh
```

Running this script will start the installation process and walk you through a guided series of prompts to help you 
configure the software on your system.

### Runtime Options

If you need to configure your system for a non-standard installation, various run-time options are available. Further information
on these runtime options is available [here](./runtime-options.md)