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
    program = None
    version = None
    aaa_user = None
    user_info = None
    engine = None
    rec_file = ''
    rec_folder = ''
    log_param = []
    license = None
    dbase = ''
    dbase_param = []
    table_parameter = {}
    modules = ''

    def __init__(self):
        if not os.path.isfile(pathConfigFile):
            raise FileNotFoundError('Отсутствует кофигурационный файл: {0}'.format(pathConfigFile))

        self.user_name = getpass.getuser()
        conf = configparser.ConfigParser()
        conf.read(pathConfigFile)
        check_config(conf)
        self.rec_file = conf.get('Main', 'file_env', fallback='filerec')
        self.rec_folder = conf.get('Main', 'path_env', fallback='filerecord')
        self.license = conf.get('Main', 'license', fallback=None)
        self.modules = conf.get('Main', 'modules', fallback='/etc/pyrma/mod.d')
        self.log_param = {'level': conf.get('Main', 'log_level', fallback='INFO'),
                          'facility': conf.get('Main', 'log_facility', fallback='local0')}

        self.log = log.Log(self.user_name, **self.log_param)

        self.dbase = conf.get('DataBase', 'provider', fallback='postgresql')
        self.dbase_param = [conf.get('DataBase', 'dbhost', fallback='localhost'),
                            conf.get('DataBase', 'dbport', fallback=5432),
                            conf.get('DataBase', 'dbuser', fallback='pyrmalib'),
                            conf.get('DataBase', 'dbpass', fallback='pyrmalib'),
                            conf.get('DataBase', 'dbname', fallback='pyrmalib')]

    def __repr__(self):
        return "{0}".format(self.__dict__)


class WebParameters:
    ip = 'localhost'
    port = 8080
    log_level = None
    template = None
    engine = None
    dbase = ''
    dbase_param = []

    def __init__(self):
        if not os.path.isfile(pathConfigFile):
            raise FileNotFoundError('Отсутствует кофигурационный файл: {0}'.format(pathConfigFile))

        conf = configparser.ConfigParser()
        conf.read(pathConfigFile)

        self.ip = conf.get('Web', 'ip')
        self.port = conf.get('Web', 'port')
        self.log_facility = conf.get('Web', 'log_facility', fallback='local0')
        self.log_level = conf.get('Main', 'log_level', fallback='INFO')
        self.template = conf.get('Web', 'template')
        self.dbase = conf.get('DataBase', 'provider', fallback='postgresql')
        self.dbase_param = [conf.get('DataBase', 'dbhost', fallback='localhost'),
                            conf.get('DataBase', 'dbport', fallback=5432),
                            conf.get('DataBase', 'dbuser', fallback='pyrmalib'),
                            conf.get('DataBase', 'dbpass', fallback='pyrmalib'),
                            conf.get('DataBase', 'dbname', fallback='pyrmalib')]

    def __repr__(self):
        return "{0}".format(self.__dict__)


class PamParameters:
    def __init__(self):
        if not os.path.isfile(pathConfigFile):
            raise FileNotFoundError('Отсутствует кофигурационный файл: {0}'.format(pathConfigFile))

        conf = configparser.ConfigParser()
        conf.read(pathConfigFile)
        self.dbase = conf.get('DataBase', 'provider', fallback='postgresql')
        self.dbase_param = [conf.get('DataBase', 'dbhost', fallback='localhost'),
                            conf.get('DataBase', 'dbport', fallback=5432),
                            conf.get('DataBase', 'dbuser', fallback='pyrmalib'),
                            conf.get('DataBase', 'dbpass', fallback='pyrmalib'),
                            conf.get('DataBase', 'dbname', fallback='pyrmalib')]
