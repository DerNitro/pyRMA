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
import os
from logging import handlers, Formatter


class Log:
    def __init__(self, name, level='INFO', filename='pyrma.log'):
        self.log = logging.getLogger(name)
        if not self.log.handlers:
            self.log.setLevel(level)
            self.handler = handlers.RotatingFileHandler(
                '/var/log/pyRMA/' + filename,
                maxBytes=1024*1024*1024,
                backupCount=10)
            log_format = Formatter('[%(process)d] [%(levelname)-8s] [%(asctime)s] - %(message)s')
            self.handler.setFormatter(log_format)
            self.log.addHandler(self.handler)

    def error(self, text, pr=False):
        if pr:
            print(text)
        self.log.error(text)

    def info(self, text):
        self.log.info(text)

    def warning(self, text):
        self.log.warning(text)

    def debug(self, text):
        self.log.debug(text)

    def critical(self, text):
        self.log.critical(text)
