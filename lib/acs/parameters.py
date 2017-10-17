# -*- coding: utf-8 -*-
# encoding: utf-8

import getpass
from acs import log
import configparser
import os

pathConfigFile = './etc/acs/acs.conf'


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
        self.log_param = {'level': conf.get('Main', 'log_level', fallback='INFO'),
                          'facility': conf.get('Main', 'log_facility', fallback='local0')}

        self.log = log.Log(self.user_name, **self.log_param)

        self.dbase = conf.get('DataBase', 'provider', fallback='postgresql')
        self.dbase_param = [conf.get('DataBase', 'dbhost', fallback='localhost'),
                            conf.get('DataBase', 'dbport', fallback=5432),
                            conf.get('DataBase', 'dbuser', fallback='acs'),
                            conf.get('DataBase', 'dbpass', fallback='acs'),
                            conf.get('DataBase', 'dbname', fallback='acs')]

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
                            conf.get('DataBase', 'dbuser', fallback='acs'),
                            conf.get('DataBase', 'dbpass', fallback='acs'),
                            conf.get('DataBase', 'dbname', fallback='acs')]

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
                            conf.get('DataBase', 'dbuser', fallback='acs'),
                            conf.get('DataBase', 'dbpass', fallback='acs'),
                            conf.get('DataBase', 'dbname', fallback='acs')]
