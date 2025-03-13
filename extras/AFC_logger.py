# Armored Turtle Automated Filament Control
#
# Copyright (C) 2024 Armored Turtle
#
# This file may be distributed under the terms of the GNU GPLv3 license.

try:
    from .. import APP_NAME
except:
    APP_NAME = "Klipper"
import logging
import re
import os
from queuelogger import QueueListener, QueueHandler
from pathlib import Path
from webhooks import GCodeHelper

class AFC_QueueListener(QueueListener):
    def __init__(self, filename):
        if APP_NAME == "Kalico":
            super().__init__(filename, False)
        else:
            super().__init__(filename)

        logging.handlers.TimedRotatingFileHandler.__init__(
            self, filename, when="S", interval=60 * 60 * 24, backupCount=5
        )

        logging.handlers.TimedRotatingFileHandler.doRollover(self)

class AFC_logger:
    def __init__(self, printer, afc_obj):
        self.reactor = printer.reactor
        self.AFC     = afc_obj
        self.gcode   = printer.lookup_object('gcode')
        self.webhooks = printer.lookup_object('webhooks')

        log_path = printer.start_args['log_file']
        dirname = Path(log_path).parent
        log_file = Path(dirname).joinpath("AFC.log")
        logger_name = os.path.splitext(os.path.basename(log_file))[0]

        self.afc_ql = AFC_QueueListener(log_file)
        self.afc_ql.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S'))
        self.afc_queue_handler = QueueHandler(self.afc_ql.bg_queue)
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False               # Stops logs from going into klippy.log
        self.logger.addHandler(self.afc_queue_handler)
        self.logger.setLevel(logging.DEBUG)
        self.print_debug_console = False

    def _add_monotonic(self, message):
        return "{:10.3f} {}".format(self.reactor.monotonic(), message)

    def _remove_tags(self, message):
        return re.sub("<.*?>", "", message)

    def _format(self, message):
        s = self._remove_tags(message.lstrip())
        return self._add_monotonic(s)

    def send_callback(self, msg):
        for cb in self.gcode.output_callbacks:
            if isinstance(cb.__self__, GCodeHelper): cb(msg.lstrip())

    def raw(self, message):
        for line in message.lstrip().rstrip().split("\n"):
            self.logger.info(self._format(line))
        self.send_callback(message)

    def info(self, message, console_only=False):
        if not console_only:
            for line in message.lstrip().split("\n"):
                self.logger.info(self._format(line))
        self.send_callback(message)

    def debug(self, message, only_debug=False):
        for line in message.lstrip().rstrip().split("\n"):
            self.logger.debug(self._format("DEBUG: {}".format(line)))

        if self.print_debug_console and not only_debug:
            self.send_callback(message)

    def error(self, message):
        for line in message.lstrip().rstrip().split("\n"):
            self.logger.error( self._format("ERROR: {}".format(line)))
        self.send_callback( "!! {}".format(message) )

        self.AFC.message_queue.append( (message, "error") )

    def set_debug(self, debug ):
        self.print_debug_console = debug