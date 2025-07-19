# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

# File is used to hold common functions that can be called from anywhere and don't belong to a class
import traceback
import json

from datetime import datetime
from urllib.request import (
    Request,
    urlopen
)
from urllib.parse import (
    urlencode,
    urljoin,
    quote
)

ERROR_STR = "Error trying to import {import_lib}, please rerun install-afc.sh script in your AFC-Klipper-Add-On directory then restart klipper\n\n{trace}"

def add_filament_switch( switch_name, switch_pin, printer ):
    """
    Helper function to register pins as filament switch sensor so it will show up in web guis

    :param switch_name: Name of switch to register, should be in the following format: `filament_switch_sensor <name>`
    :param switch_pin: Pin to add to config for switch
    :param printer: printer object

    :return returns filament_switch_sensor object
    """
    import configparser
    import configfile
    ppins = printer.lookup_object('pins')
    ppins.allow_multi_use_pin(switch_pin.strip("!^"))
    filament_switch_config = configparser.RawConfigParser()
    filament_switch_config.add_section( switch_name )
    filament_switch_config.set( switch_name, 'switch_pin', switch_pin)
    filament_switch_config.set( switch_name, 'pause_on_runout', 'False')

    cfg_wrap = configfile.ConfigWrapper( printer, filament_switch_config, {}, switch_name)

    fila = printer.load_object(cfg_wrap, switch_name)
    fila.runout_helper.sensor_enabled = False
    fila.runout_helper.runout_pause = False

    return fila

def check_and_return( value_str:str, data_values:dict ) -> str:
    """
    Common function to check if value exists in dictionary and returns value if it does.

    :param value_str: Key string to check if value exists in dictionary
    :param data_values: Dictionary of values to check for key

    :return: Returns string of value if found in dictionary
    """
    value = "0"
    if value_str in data_values:
        value = data_values[value_str]

    return value

class AFC_moonraker:
    """
    This class is used to communicate with moonraker to look up information and post
    data into moonrakers database

    Parameters
    ----------------
    port: String
        Port to connect to moonrakers localhost
    logger: AFC_logger
        AFC logger object to log and print to console
    """
    ERROR_STRING = "Error getting data from moonraker, check AFC.log for more information"
    def __init__(self, host:str, port:str, logger:object):
        self.port           = port
        self.logger         = logger
        self.host           = f'{host.rstrip("/")}:{port}'
        self.database_url   = urljoin(self.host, "server/database/item")
        self.afc_stats_key  = "afc_stats"
        self.afc_stats      = None
        self.last_stats_time= None
        self.logger.debug(f"Moonraker url: {self.host}")

    def _get_results(self, url_string, print_error=True):
        """
        Helper function to get results, check for errors and return data if successful

        :param url_string: URL encoded string to fetch/post data to moonraker
        :param print_error: Set to True for error to be displayed in console/mainsail panel, setting
                            to False will still write error to log via debug message

        :returns: Returns result dictionary if data is valid, returns None if and error occurred
        """
        data = None
        # Only print error to console when set, else still print errors bug with debug
        # logger so that messages are still written to log for debugging purposes
        if print_error:
            logger = self.logger.error
        else:
            logger = self.logger.debug

        try:
            resp = urlopen(url_string)
            if resp.status >= 200 and resp.status <= 300:
                data = json.load(resp)
            else:
                logger(self.ERROR_STRING)
                logger(f"Response: {resp.status} Reason: {resp.reason}")
        except:
            logger(self.ERROR_STRING, traceback=traceback.format_exc())
            data = None
        return data['result'] if data is not None else data

    def wait_for_moonraker(self, toolhead, timeout:int=30):
        """
        Function to wait for moonraker to start, times out after passed in timeout value

        :param toolhead: Toolhead object so that non blocking waits can happen
        :param timeout: Timeout out trying after this many seconds

        :return: Returns True if connected to moonraker and a timeout did no occur, returns False if
                 not connected after waiting max timeout value
        """
        self.logger.info(f"Waiting max {timeout}s for moonraker to connect")
        for i in range(0,timeout):
            resp = self._get_results(urljoin(self.host, 'server/info'), print_error=False)
            if resp is not None:
                self.logger.debug(f"Connected to moonraker after {i} tries")
                return True
            else:
                toolhead.dwell(1)
        self.logger.info(f"Failed to connect to moonraker after {timeout} seconds, check AFC.log for more information")
        return False

    def get_spoolman_server(self)->str:
        """
        Queries moonraker to see if spoolman is configured, returns True when
        spoolman is configured

        :returns: Returns string for spoolmans IP, returns None if its not configured
        """
        resp = self._get_results(urljoin(self.host, 'server/config'))
        # Check to make sure response is valid and spoolman exists in dictionary
        if resp is not None and 'orig' in resp and 'spoolman' in resp['orig']:
            return resp['orig']['spoolman']['server']     # check for spoolman and grab url
        else:
            self.logger.debug("Spoolman server is not defined")
            return None

    def get_file_filament_change_count(self, filename:str ):
        """
        Queries moonraker for files metadata and returns filament change count

        :param filename: Filename to query moonraker and pull metadata
        :return: Returns number of filament change counts if `filament_change_count` is in metadata.
                 Returns zero if not found in metadata.
        """
        change_count = 0
        resp = self._get_results(urljoin(self.host,
                                    'server/files/metadata?filename={}'.format(quote(filename))))
        if resp is not None and 'filament_change_count' in resp:
            change_count =  resp['filament_change_count']
        else:
            self.logger.debug(f"Filament change count metadata not found for file:{filename}")
        return change_count

    def get_afc_stats(self):
        """
        Queries moonraker database for all `afc_stats` entries and returns results if afc_stats exist.
        Function also caches results and refetches data if cache is older than 60s. This is done to help
        cut down on how much data is fetched from moonraker.

        :return: Dictionary of afc_stats entries, None if afc_stats entry does not exist
        """
        resp = None
        # Initially set to True since first time data always needs to be fetched
        refetch_data = True
        current_time = datetime.now()

        # Check to see if data is older than 60 seconds and refreshes
        if self.last_stats_time is not None:
            refetch_data = False
            delta = current_time - self.last_stats_time
            if delta.seconds > 60:
                refetch_data = True
                self.last_stats_time = current_time
        else:
            self.last_stats_time = datetime.now()

        # Cache results to keep queries to moonraker down
        if self.afc_stats is None or refetch_data:
            resp = self._get_results(urljoin(self.database_url, f"?namespace={self.afc_stats_key}"))
            if resp is not None:
                self.afc_stats = resp
            else:
                self.logger.debug("AFC_stats not in database")

        return self.afc_stats

    def update_afc_stats(self, key, value):
        """
        Updates afc_stats in moonrakers database with key, value pair

        :param key: The key indicating the field where the value should be inserted
        :param value: The value to insert into the database
        """
        resp = None
        post_payload = {
            "request_method": "POST",
            "namespace": self.afc_stats_key,
            "key": key,
            "value": value
        }
        req = Request(self.database_url, urlencode(post_payload).encode())

        resp = self._get_results(req)
        if resp is None:
            self.logger.error(f"Error when trying to update {key} in moonraker, see AFC.log for more info")

    def get_spool(self, id:int):
        """
        Uses moonrakers proxy to query spoolID from spoolman

        :param id: SpoolID to lookup and fetch data from spoolman
        :return: Returns dictionary of spoolID, returns None if error occurred or ID does not exist
        """
        resp = None
        request_payload = {
            "request_method": "GET",
            "path": f"/v1/spool/{id}"
        }
        spool_url = urljoin(self.host, 'server/spoolman/proxy')
        req = Request( spool_url, urlencode(request_payload).encode() )

        resp = self._get_results(req)
        if resp is not None:
            resp = resp
        else:
            self.logger.info(f"SpoolID: {id} not found")
        return resp