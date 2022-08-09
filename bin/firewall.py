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
import os
import traceback
import signal
import time
from sqlalchemy import create_engine, table
import iptc
import shlex
import subprocess

__author__ = 'Sergey Utkin'
__email__ = 'utkins01@gmail.com'
__version__ = "1.1.3"
__status__ = "stable"
__maintainer__ = "Sergey Utkin"
__copyright__ = "Copyright 2016, Sergey Utkin"
__program__ = 'pyRMA'

interrupted = False
dump_traffic = []


class Capture():
    user_ip = None
    service_port = None
    filename = None
    connection_id = None
    
    def __init__(self, user_ip, acs_ip, service_port, filename, connection_id):
        self.user_ip = user_ip
        self.acs_ip = acs_ip
        self.service_port = service_port
        self.filename = filename
        self.connection_id = connection_id

    def run(self):
        cmd = "/usr/sbin/tcpdump -i any -w {filename} '(dst host {acs_ip}) and (dst port {service_port}) and (src host {user_ip})' -s 0 "
        args = shlex.split(cmd.format(
            filename=self.filename, user_ip=self.user_ip, service_port=self.service_port, acs_ip=self.acs_ip
        ))
        self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.pid = self.process.pid
        
    def kill(self):
        self.process.terminate()
        self.process.wait()

    def __eq__(self, other):
        if self.connection_id != other.connection_id:
            return False
        if self.user_ip != other.user_ip:
            return False
        if self.acs_ip != other.acs_ip:
            return False
        if self.service_port != other.service_port:
            return False
        return True

    def __str__(self) -> str:
        return "user ip: {user_ip}; dest ip: {acs_ip}; dest port: {service_port}; connection: {connection_id}".format(
            user_ip=self.user_ip, service_port=self.service_port, connection_id=self.connection_id, acs_ip=self.acs_ip
        )


def handle_sig_term(signum, frame):
    global interrupted
    if signum != 15:
        appParameters.log.debug('Получен сигнал на завершение приложения!!!({},{})'.format(signum, frame))
    interrupted = True


def app_exit(code):
    for v in dump_traffic:
        v.kill()
        appParameters.log.info('Остановка записи дампа: {}'.format(v))
    appParameters.log.info('Завершение работы приложения')
    sys.exit(code)


def connection(param: parameters.FirewallParameters):
    "Остановка активных подключений"
    pass


def capture_traffic(param: parameters.FirewallParameters, user_ip, acs_ip, service_port, connection_id, command):
    filename = os.path.join(appParameters.tcp_capture_folder, str(connection_id), "{}.pcap".format(service_port))
    if not os.path.isdir(os.path.join(appParameters.data_dir, appParameters.tcp_capture_folder, str(connection_id))):
        os.mkdir(os.path.join(appParameters.data_dir, appParameters.tcp_capture_folder, str(connection_id)))
    path = os.path.join(appParameters.data_dir, *os.path.split(filename))

    capture = Capture(user_ip, acs_ip, service_port, path, connection_id)
    
    if command == 'create':
        if capture not in dump_traffic:
            capture.run()
            dump_traffic.append(capture)
            applib.add_capture_traffic(param, connection_id, filename, service_port)
            param.log.info('Старт записи дампа: {}'.format(str(capture)))
    if command == 'close':
        dump_traffic.pop(dump_traffic.index(capture)).kill()
        param.log.info('Остановка записи дампа: {}'.format(str(capture)))

def tcp_forward(param: parameters.FirewallParameters):
    tcp_forwards = applib.get_tcp_forward_connection(param)
    for tcp_forward in tcp_forwards:
        rule = iptc.Rule()
        rule.protocol = "tcp"
        rule.src = "{user_ip}/255.255.255.255".format(user_ip=tcp_forward.user_ip)
        rule.dst = "{acs_ip}".format(acs_ip=tcp_forward.acs_ip)
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
                capture_traffic(param, tcp_forward.user_ip, tcp_forward.acs_ip, tcp_forward.local_port, tcp_forward.connection_id, 'close')
                iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_forward_table).delete_rule(rule)
                appParameters.log.info(
                    'deleted forward {tcp_forward.connection_id}: {tcp_forward.user_ip}:{tcp_forward.local_port}'.format(
                        tcp_forward=tcp_forward
                    )
                )
        elif tcp_forward.state == 1:
            capture_traffic(param, tcp_forward.user_ip, tcp_forward.acs_ip, tcp_forward.local_port, tcp_forward.connection_id, 'create')
            if rule not in iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_forward_table).rules:
                iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_forward_table).append_rule(rule)
                appParameters.log.info(
                    'append rule {tcp_forward.connection_id}: {tcp_forward.user_ip}:{tcp_forward.local_port}'.format(
                        tcp_forward=tcp_forward
                    )
                )


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

for chain in iptc.Table(iptc.Table.NAT).chains:
    forward = False
    ipmi = False
    if chain.name == 'PREROUTING':
        for rule in chain.rules:
            if rule.target.name == appParameters.firewall_forward_table:
                forward = True

        if not forward:
            rule = iptc.Rule()
            target = iptc.Target(rule, appParameters.firewall_forward_table)
            rule.target = target
            chain.insert_rule(rule)
            appParameters.log.info('Added rule: -A PREROUTING -j {}'.format(appParameters.firewall_forward_table))

    elif chain.name == 'POSTROUTING':
            ACCEPT = 0
            INSERT = 1
            for i in chain.rules:
                if i.target.name == 'ACCEPT':
                    ACCEPT = ACCEPT + 1
                elif i.target.name == 'MASQUERADE':
                    INSERT = 0
            if INSERT:
                rule = iptc.Rule()
                rule.out_interface = appParameters.tcp_forward_interface
                target = iptc.Target(rule, 'MASQUERADE')
                rule.target = target
                chain.insert_rule(rule, position=ACCEPT)


while True:
    try:
        tcp_forward(appParameters)
        connection(appParameters)
    except:
        appParameters.log.exception()
        iptc.Chain(iptc.Table(iptc.Table.NAT), appParameters.firewall_forward_table).flush()
        app_exit(1)

    time.sleep(0.5)
    if interrupted:
        app_exit(0)
