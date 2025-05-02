# Armored Turtle Automated Filament Changer
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

# File is used to hold common functions that can be called from anywhere and don't belong to a class
import json
try:
    from urllib.request import urlopen
    import urllib.request as request
    import urllib.parse as urlparse
except:
    # Python 2.7 support
    from urllib2 import urlopen
    import urlparse


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

class AFC_moonraker:
    def __init__(self, port, logger):
        self.port = port
        self.logger = logger
        self.local_host = 'http://localhost{port}'.format( port=port )
        self.database_url = urlparse.urljoin(self.local_host, "server/database/item")
        self.data_array = {"namespace":"afc_stats", "key":"", "value":""}

    def _get_results(self, url_string):
        try:
            resp = json.load(urlopen(url_string))
        except:
            resp = None
        return resp        

    def get_spoolman_server(self):
        resp = self._get_results(urlparse.urljoin(self.local_host, 'server/config'))
        if resp is not None:
            return resp['result']['orig']['spoolman']['server']     # check for spoolman and grab url
        else:
            return None

    def get_file_filament_change_count(self, filename ):
        change_count = 0
        resp = self._get_results(urlparse.urljoin(self.local_host, 'server/files/metadata?filename={}'.format(filename)))
        if resp is not None and 'filament_change_count' in resp['result']:
            change_count =  resp['result']['filament_change_count']
        return change_count
    
    def get_afc_stats(self):

        req = request.Request(self.database_url)
        resp = self._get_results(urlparse.urljoin(self.database_url, "?namespace=afc_stats"))
        if resp is None:
            self.logger.info("AFC_stats not in database")

# toolchange_count
#   total
#   tool_load
#   tool_unload
# cut_count
#   total
#   cut_count_since_changed
# last_blade_changed
# n20_runtime_per_lane
#   lane1
#   lane2
#   etc....
# average_toolchange_time
#   tool_load
#   tool_unload
# change_count_per_lane
#   lane1
#   lane2
#   etc....