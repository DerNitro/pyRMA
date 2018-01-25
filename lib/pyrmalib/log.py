# -*- coding: utf-8 -*-
# encoding: utf-8

"""
       Copyright 2016 Sergey Utkin utkins01@gmail.com

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

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
