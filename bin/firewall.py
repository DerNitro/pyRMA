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
from pyrmalib import parameters, applib
import sys
import traceback
import signal
import time
from sqlalchemy import create_engine, table
import iptc

__author__ = 'Sergey Utkin'
__email__ = 'utkins01@gmail.com'
__version__ = "0.0.1"
__status__ = "Development"
__maintainer__ = "Sergey Utkin"
__copyright__ = "Copyright 2016, Sergey Utkin"
__program__ = 'pyRMA'

interrupted = False


def handle_sig_term(signum, frame):
    global interrupted
    if signum != 15:
        appParameters.log.debug('Получен сигнал на завершение приложения!!!({},{})'.format(signum, frame))
    interrupted = True


def app_exit(code):
    appParameters.log.info('Завершение работы приложения')
    sys.exit(code)


def connection(param: parameters.FirewallParameters):
    pass


def tcp_forward(param: parameters.FirewallParameters):
    tcp_forwards = applib.get_tcp_forward_connection(param)
    for tcp_forward in tcp_forwards:
        rule = iptc.Rule()
        rule.protocol = "tcp"
        rule.src = "{user_ip}/255.255.255.255".format(user_ip=tcp_forward.user_ip)
        match = rule.create_match("tcp")
        match.dport = str(tcp_forward.local_port)
        comment = rule.create_match("comment")
        comment.comment = "\"Connection id: {id}\"".format(id=tcp_forward.connection_id)
        target = iptc.Target(rule, "DNAT")
        target.to_destination = "{ip}:{port}".format(ip=tcp_forward.forward_ip, port=tcp_forward.forward_port)
        rule.target = target
        
        if tcp_forward.state == 0:
            if rule not in iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_forward_table).rules:
                applib.del_tcp_forward_connection(param, tcp_forward)
                appParameters.log.info(
                    'deleted record {tcp_forward.connection_id}: {tcp_forward.user_ip}:{tcp_forward.local_port}'.format(
                        tcp_forward=tcp_forward
                    )
                )
            else:
                iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_forward_table).delete_rule(rule)
                appParameters.log.info(
                    'deleted forward {tcp_forward.connection_id}: {tcp_forward.user_ip}:{tcp_forward.local_port}'.format(
                        tcp_forward=tcp_forward
                    )
                )
        elif tcp_forward.state == 1:
            if rule not in iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_forward_table).rules:
                iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_forward_table).append_rule(rule)
                appParameters.log.info(
                    'append rule {tcp_forward.connection_id}: {tcp_forward.user_ip}:{tcp_forward.local_port}'.format(
                        tcp_forward=tcp_forward
                    )
                )

    pass


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

# создание цепочек.
if not iptc.Table(iptc.Table.NAT).is_chain(appParameters.firewall_forward_table):
    iptc.Table(iptc.Table.NAT).create_chain(appParameters.firewall_forward_table)
    appParameters.log.info('Create chains {} in table NAT.'.format(appParameters.firewall_forward_table))
else:
    iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_forward_table).flush()

if not iptc.Table(iptc.Table.NAT).is_chain(appParameters.firewall_ipmi_table):
    iptc.Table(iptc.Table.NAT).create_chain(appParameters.firewall_ipmi_table)
    appParameters.log.info('Create chains {} in table NAT.'.format(appParameters.firewall_ipmi_table))
else:
    iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_ipmi_table).flush()

for chain in iptc.Table(iptc.Table.NAT).chains:
    forward = False
    ipmi = False
    if chain.name == 'PREROUTING':
        for rule in chain.rules:
            if rule.target.name == appParameters.firewall_forward_table:
                forward = True
            if rule.target.name == appParameters.firewall_ipmi_table:
                ipmi = True

        if not forward:
            rule = iptc.Rule()
            target = iptc.Target(rule, appParameters.firewall_forward_table)
            rule.target = target
            chain.insert_rule(rule)
            appParameters.log.info('Added rule: -A PREROUTING -j {}'.format(appParameters.firewall_forward_table))

        if not ipmi:
            rule = iptc.Rule()
            target = iptc.Target(rule, appParameters.firewall_ipmi_table)
            rule.target = target
            chain.insert_rule(rule)
            appParameters.log.info('Added rule: -A PREROUTING -j {}'.format(appParameters.firewall_ipmi_table))


while True:
    tcp_forward(appParameters)
    connection(appParameters)
    time.sleep(0.5)
    if interrupted:
        app_exit(0)
