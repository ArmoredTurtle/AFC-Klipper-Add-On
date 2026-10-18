# AFCProject Automated Filament Changer Software
#
# Copyright (C) 2024-2025 Armored Turtle
# Copyright (C) 2026 AFCProject
#
# This file may be distributed under the terms of the GNU GPLv3 license.
from __future__ import annotations

import traceback

from configparser import Error as error

from typing import TYPE_CHECKING

try: from extras.AFC_utils import ERROR_STR
except:
    trace = traceback.format_exc()
    err_str = f"Error when trying to import AFC_utils.ERROR_STR\n{trace}"
    raise error(err_str)

try: from extras.AFC_BoxTurtle import afcBoxTurtle
except: raise error(ERROR_STR.format(import_lib="AFC_BoxTurtle", trace=traceback.format_exc()))

if TYPE_CHECKING:
    from configfile import ConfigWrapper

class afcNightOwl(afcBoxTurtle):
    def __init__(self, config: ConfigWrapper) -> None:
        """
        Initialize the Night Owl unit, reading its type from config.

        :param config: Klipper config wrapper for the AFC_NightOwl section
        """
        super().__init__(config)
        self.type: str = config.get('type', 'Night_Owl')

    def handle_connect(self) -> None:
        """
        Handle the connection event.
        This function is called when the printer connects. It looks up AFC info
        and assigns it to the instance variable `self.AFC`.
        """
        super().handle_connect()

        self.logo = '<span class=success--text>Night Owl Ready</span>'
        self.logo ='<span class=success--text>R  ,     ,\n'
        self.logo+='E  )\\___/(\n'
        self.logo+='A {(@)v(@)}\n'
        self.logo+='D  {|~~~|}\n'
        self.logo+='Y  {/^^^\\}\n'
        self.logo+='!   `m-m`</span>\n'

        self.logo_error = '<span class=error--text>Night Owl Not Ready</span>\n'

def load_config_prefix(config: ConfigWrapper) -> afcNightOwl:
    """
    Klipper config entry point for AFC_NightOwl <name> sections.

    :param config: Klipper config wrapper for the AFC_NightOwl section
    :return afcNightOwl: constructed Night Owl unit
    """
    return afcNightOwl(config)
