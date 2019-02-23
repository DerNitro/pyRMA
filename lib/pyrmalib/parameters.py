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

import getpass
from pyrmalib import log
import configparser
import os

pathConfigFile = '/home/sergey/PycharmProjects/pyRMA/etc/pyrma/pyrma.conf'


def check_config(config):
    if not config.has_section('Main'):
        raise CheckConfigError('Отсутсвует секция Main - {0}'.format(pathConfigFile))
    if not config.has_section('DataBase'):
        raise CheckConfigError('Отсутсвует секция DataBase - {0}'.format(pathConfigFile))
    return True


class CheckConfigError(Exception):
    pass


class Parameters:
    dbase = ''
    dbase_param = []
    engine = None
    program = None
    version = None
    aaa_user = None
    user_info = None
    log_param = {}

    def __init__(self):
        if not os.path.isfile(pathConfigFile):
            raise FileNotFoundError('Отсутствует кофигурационный файл: {0}'.format(pathConfigFile))

        self.conf = configparser.ConfigParser()
        self.conf.read(pathConfigFile)
        check_config(self.conf)

        self.dbase = self.conf.get('DataBase', 'provider', fallback='postgresql')
        self.dbase_param = [self.conf.get('DataBase', 'dbhost', fallback='localhost'),
                            self.conf.get('DataBase', 'dbport', fallback=5432),
                            self.conf.get('DataBase', 'dbuser', fallback='pyrmalib'),
                            self.conf.get('DataBase', 'dbpass', fallback='pyrmalib'),
                            self.conf.get('DataBase', 'dbname', fallback='pyrmalib')]

    def check_user(self):
        if not self.user_info:
            return False
        return True

    def __repr__(self):
        return "{0}".format(self.__dict__)


class AppParameters(Parameters):
    rec_file = ''
    rec_folder = ''
    license = None
    table_parameter = {}
    modules = ''

    def __init__(self):
        super().__init__()
        self.user_name = getpass.getuser()

        self.rec_file = self.conf.get('Main', 'file_env', fallback='filerec')
        self.rec_folder = self.conf.get('Main', 'path_env', fallback='filerecord')
        self.license = self.conf.get('Main', 'license', fallback=None)
        self.modules = self.conf.get('Main', 'modules', fallback='/etc/pyrma/mod.d')
        self.log_param = {'level': self.conf.get('Main', 'log_level', fallback='INFO'),
                          'facility': self.conf.get('Main', 'log_facility', fallback='local0')}
        self.log = log.Log(self.user_name, **self.log_param)


class WebParameters(Parameters):
    ip = 'localhost'
    port = 8080
    template = None

    def __init__(self):
        super().__init__()
        self.ip = self.conf.get('Web', 'ip')
        self.port = self.conf.get('Web', 'port')
        self.log_param = {'level': self.conf.get('Web', 'log_level', fallback='INFO'),
                          'facility': self.conf.get('Web', 'log_facility', fallback='local0')}
        self.template = self.conf.get('Web', 'template')


class PamParameters(Parameters):
    pass
