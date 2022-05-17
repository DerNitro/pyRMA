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
from this import s
from pyrmalib import log, schema
import configparser
import os

pathConfigFile = '/etc/pyrma/pyrma.conf'


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
    user_info = None    # type: schema.User
    data_dir = None
    log_param = {}
    log = None

    def __init__(self):
        if not os.path.isfile(pathConfigFile):
            raise FileNotFoundError('Отсутствует кофигурационный файл: {0}'.format(pathConfigFile))

        self.conf = configparser.ConfigParser()
        self.conf.read(pathConfigFile)
        check_config(self.conf)

        self.dbase = self.conf.get('DataBase', 'provider', fallback='postgresql')
        self.dbase_param = {
            "host":     self.conf.get('DataBase', 'dbhost', fallback='localhost'),
            "port":     self.conf.get('DataBase', 'dbport', fallback=5432),
            "user":     self.conf.get('DataBase', 'dbuser', fallback='acs'),
            "password": self.conf.get('DataBase', 'dbpass', fallback='acs'),
            "database": self.conf.get('DataBase', 'dbname', fallback='acs')
        }
        self.data_dir = self.conf.get('Main', 'data_dir', fallback='/data/pyRMA')
        self.auto_extension = int(self.conf.get('Main', 'auto_extension', fallback='1'))
        self.extension_days = int(self.conf.get('Main', 'extension_days', fallback='21'))
        self.check_source_ip = int(self.conf.get('Main', 'check_source_ip', fallback='0'))
        self.email = {
            "domain_name": self.conf.get('Email', 'domain_name', fallback='localhost'),
            "type": self.conf.get('Email', 'type', fallback='smtp'),
            "host": self.conf.get('Email', 'host', fallback='localhost'),
            "port": int(self.conf.get('Email', 'port', fallback='25')),
            "from": self.conf.get('Email', 'from', fallback='acs@localhost')
        }
        self.forward_tcp_port_range = range(
            int(self.conf.get('Main', 'forward_tcp_port_range', fallback='10000:15000').split(':')[0]),
            int(self.conf.get('Main', 'forward_tcp_port_range', fallback='10000:15000').split(':')[1]),
        )

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
    modules = ''
    session = None

    def __init__(self):
        super().__init__()
        self.user_name = getpass.getuser()

        self.rec_file = self.conf.get('Main', 'file_env', fallback='filerec')
        self.rec_folder = self.conf.get('Main', 'path_env', fallback='filerecord')
        self.modules = self.conf.get('Main', 'modules', fallback='/etc/pyrma/mod.d')
        self.log_param = {
            'level': self.conf.get('Main', 'log_level', fallback='INFO'),
            'filename': 'pyrma_' + self.user_name + '.log'
        }
        self.log = log.Log(self.user_name, **self.log_param)


class WebParameters(Parameters):
    ip = 'localhost'
    port = 8080
    template = None

    def __init__(self):
        super().__init__()
        self.ip = self.conf.get('Web', 'ip')
        self.port = self.conf.get('Web', 'port')
        self.log_param = {
            'level': self.conf.get('Web', 'log_level', fallback='INFO'),
            'filename': 'pyrma_web.log'
        }
        self.template = self.conf.get('Web', 'template')
        self.log = log.Log('pyrma_web', **self.log_param)


class FirewallParameters(Parameters):

    def __init__(self):
        super().__init__()
        self.log_param = {
            'level': self.conf.get('Main', 'log_level', fallback='INFO'),
            'filename': 'pyrma_firewall.log'
        }
        self.log = log.Log('pyrma_firewall', **self.log_param)
