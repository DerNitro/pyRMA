#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Filename : firewall
    Date: 11.08.2020 06:57
    Project: pyRMA
    AUTHOR : Sergey Utkin
    
    Copyright 2020 Sergey Utkin utkins01@gmail.com

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

from pyrmalib import parameters
import sys
import traceback
import signal
import time
from sqlalchemy import create_engine
import iptc

__version__ = 0.1

interrupted = False
firewall_filter_table = 'pyrma_input'
firewall_forward_table = 'pyrma_forward'
firewall_ipmi = 'pyrma_ipmi'


def handle_sig_term(signum, frame):
    global interrupted
    if signum != 15:
        appParameters.log.debug('Получен сигнал на завершение приложения!!!({},{})'.format(signum, frame))
    interrupted = True


def app_exit(code):
    appParameters.log.info('Завершение приложения')
    sys.exit(code)


try:
    appParameters = parameters.FirewallParameters()
except FileNotFoundError:
    print('Ошибка инициализации приложения!!!')
    print(traceback.print_exc(limit=1))
    sys.exit(1)
except parameters.CheckConfigError:
    print('Ошибка инициализации приложения!!!')
    print(traceback.print_exc(limit=1))
    sys.exit(2)

appParameters.log.info('Запуск приложения {}'.format(__version__))

signal.signal(signal.SIGTERM, handle_sig_term)
signal.signal(signal.SIGINT, handle_sig_term)

if appParameters.dbase in ['postgresql']:
    engine = create_engine(
        '{0}://{1}:{2}@{3}:{4}/{5}'.format(
            appParameters.dbase,
            appParameters.dbase_param["user"],
            appParameters.dbase_param["password"],
            appParameters.dbase_param["host"],
            appParameters.dbase_param["port"],
            appParameters.dbase_param["database"]
        )
    )
else:
    appParameters.log.error('Некорректные параметры подключения к БД.', pr=True)
    sys.exit(12)

appParameters.engine = engine

table_filter = iptc.Table(iptc.Table.FILTER)
table_nat = iptc.Table(iptc.Table.NAT)

# создание цепочек.
# if firewall_filter_table not in table_filter.chains:
#     table_filter.create_chain(firewall_filter_table)
#     appParameters.log.info('Create chains {} in table Filter.'.format(firewall_filter_table))
#
# if firewall_forward_table not in table_nat.chains:
#     table_nat.create_chain(firewall_filter_table)
#     appParameters.log.info('Create chains {} in table NAT.'.format(firewall_forward_table))


while True:
    time.sleep(1)
    if interrupted:
        app_exit(0)
