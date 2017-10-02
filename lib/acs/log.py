# -*- coding: utf-8 -*-
# encoding: utf-8

import logging
from logging import handlers, Formatter


class Log:
    def __init__(self, name, level='INFO', facility='local0'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        h = handlers.SysLogHandler(address='/dev/log', facility=facility)
        log_format = Formatter('[{0:<10}] [%(levelname)-8s] - %(message)s'.format(name))
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

    def critical(self, text):
        self.logger.critical(text)
