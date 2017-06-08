# -*- coding: utf-8 -*-
# encoding: utf-8

import logging
from logging import handlers, Formatter


class Log:
    def __init__(self, logfile, log_level, backup_count, max_bytes):
        self.logger = logging.getLogger('mainLog')
        self.logger.setLevel(log_level)
        h = handlers.RotatingFileHandler(logfile, backupCount=backup_count, maxBytes=max_bytes)
        log_format = Formatter('[%(asctime)s] [%(levelname)-8s] - %(message)s')
        h.setFormatter(log_format)
        self.logger.addHandler(h)

    def error(self, text, pr=False):
        if pr:
            print(text)
        self.logger.error(text)

    def info(self, text):
        self.logger.info(text)

    def warning(self, text):
        self.logger.warning(text)

    def debug(self, text):
        self.logger.debug(text)
