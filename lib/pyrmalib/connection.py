#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Filename : ssh
    Date: 28.09.2018 06:38
    Project: pyRMA
    AUTHOR : Sergey Utkin

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
import os
import shlex
import subprocess
import datetime
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError

from pyrmalib import modules, dict, applib, parameters, schema, access, error, utils


class SSH(modules.ConnectionModules):
    """
    Модуль подключения к удаленному узлу по SSH.
    """

    def __init__(self, param: parameters.AppParameters, host: schema.Host):
        super().__init__(param, host)
        self.NAME = 'SSH'
        self.DESCRIPTION = 'Модуль подключения по протоколу SSH'
        self.CONNECTION_TYPE = dict.conn_type_dict['Connection']

        services = applib.get_service(self.PARAMETERS, host=self.HOST.id)
        if len(services) > 0 and access.check_access(self.PARAMETERS, 'ConnectionService', h_object=self.HOST):
            self.SERVICE = []  # type: dict
            for service in services:
                service_type = applib.get_service_type(self.PARAMETERS, service_type_id=service.type)
                self.SERVICE.append(
                    {
                        'name': service_type.name,
                        'local_port': service.local_port,
                        'remote_port': service.remote_port,
                        'remote_ip': service.remote_ip,
                        'describe': service.describe
                    }
                )

    def connection(self):
        super().connection()
        ssh_options = '-o "StrictHostKeyChecking=no"'
        ssh = '/usr/bin/ssh {options} -p {port} {login}@{ip}'
        sshpass = '/usr/bin/sshpass -e ssh {options} -p {port} {login}@{ip}'
        if self.PASSWORD:
            os.environ["SSHPASS"] = self.PASSWORD
            cmd = sshpass
        else:
            cmd = ssh
        args = shlex.split(cmd.format(login=self.LOGIN, ip=self.HOST.ip, port=self.HOST.tcp_port, options=ssh_options))
        proc = subprocess.Popen(args)
        stdout, stderr = proc.communicate('through stdin to stdout')
        if proc.returncode > 0:
            self.TERMINATION = 2
            self.ERROR = "Error {0}: {1}; run command: {2}".format(proc.returncode, stderr, cmd)
            self.PARAMETERS.log.error(
                self.ERROR,
                pr=True
            )
        if proc.returncode == 5:
            self.TERMINATION = 2
            self.ERROR = "Неверно указан пароль для подключения!!!"
            self.PARAMETERS.log.error(
                self.ERROR,
                pr=True
            )


class SFTP(modules.ConnectionModules):
    """
    Модуль передачи файлов по SSH.
    """
    JUMP = None
    ft_bin = None

    def __init__(self, param: parameters.AppParameters, host: schema.Host):
        super().__init__(param, host)
        self.NAME = 'SFTP'
        self.DESCRIPTION = 'Модуль передачи файлов по SFTP'
        self.CONNECTION_TYPE = dict.conn_type_dict['File Transfer']

    def connection(self):
        super().connection()
        cmd = '/usr/bin/python3 {bin} --host {host} --port {port} --user {user} --password {password} --id {id}'
        args = shlex.split(
            cmd.format(
                bin=self.ft_bin, 
                user=self.LOGIN, 
                password=self.PASSWORD,
                host=self.HOST.ip, 
                port=self.HOST.tcp_port, 
                id=self.connection_id
            )
        )
        proc = subprocess.Popen(args)
        stdout, stderr = proc.communicate('through stdin to stdout')
        if proc.returncode > 0:
            self.TERMINATION = 2
            self.ERROR = "Error {0}: {1}".format(proc.returncode, stderr)
            self.PARAMETERS.log.error(
                self.ERROR,
                pr=True
            )
        


class TELNET(modules.ConnectionModules):
    """
    Модуль подключения к удаленному узлу по telnet
    """

    def __init__(self, param: parameters.AppParameters, host: schema.Host):
        super().__init__(param, host)
        self.NAME = 'Telnet'
        self.DESCRIPTION = 'Модуль подключения по протоколу Telnet'
        self.CONNECTION_TYPE = dict.conn_type_dict['Connection']


    def connection(self):
        super().connection()

        cmd = "/usr/bin/telnet {ip} {port}"
        
        args = shlex.split(cmd.format(ip=self.HOST.ip, port=self.HOST.tcp_port))
        proc = subprocess.Popen(args)
        stdout, stderr = proc.communicate('through stdin to stdout')

        if proc.returncode > 0:
            print("Error {0}: {1}; run command: {2}".format(proc.returncode, stderr, cmd))

        pass


class SERVICE(modules.ConnectionModules):
    """
    Модуль формирования подключения только сервисов.
    """

    def __init__(self, param: parameters.AppParameters, host: schema.Host):
        super().__init__(param, host)
        self.NAME = 'OnlyServices'
        self.DESCRIPTION = 'Модуль подключения только сервисов'
        self.CONNECTION_TYPE = dict.conn_type_dict['Service']

        services = applib.get_service(self.PARAMETERS, host=self.HOST.id)
        if len(services) > 0:
            self.SERVICE = []  # type: dict
            for service in services:
                service_type = applib.get_service_type(self.PARAMETERS, service_type_id=service.type)
                self.SERVICE.append(
                    {
                        'name': service_type.name,
                        'local_port': service.local_port,
                        'remote_port': service.remote_port,
                        'remote_ip': service.remote_ip,
                        'describe': service.describe
                    }
                )

    def connection(self):
        super().connection()
        user_input = ''
        while user_input.lower() != 'exit'.lower():
            user_input = input('Для завершения сессии введите "exit": ')

class IPMI:
    HOST = None
    CONNECTION_TYPE = 4
    JUMP = None
    NAME = None
    TERMINATION = 0

    def __init__(self, param: parameters.AppParameters, host: schema.Host):
        super().__init__()
        self.PARAMETERS = param
        self.HOST = host
        self.JUMP = None
        self.TCP_FORWARD = []
        self.connection_id = None
        self.NAME = 'IPMI'
        self.ERROR = None

    def run(self):
        self.PARAMETERS.log.info(
            'Подключение {name} к хосту {host.name}({host.ilo})'.format(name=self.NAME, host=self.HOST)
        )
        connection = schema.Connection(
            status=1,
            user=self.PARAMETERS.user_info.uid,
            host=self.HOST.id,
            connection_type=self.CONNECTION_TYPE,
            date_start=datetime.datetime.now(),
            session=self.PARAMETERS.session
        )
        with schema.db_edit(self.PARAMETERS.engine) as db:
            db.add(connection)
            db.flush()
            db.refresh(connection)
            self.connection_id = connection.id

        self.JUMP = applib.get_jump_host(self.PARAMETERS, self.HOST.id) \
            if applib.get_jump_host(self.PARAMETERS, self.HOST.id) \
                else applib.get_jump_host(self.PARAMETERS, self.HOST.parent)

        self.ilo_type = applib.get_ilo_type(self.PARAMETERS, ipmi_id=self.HOST.ilo_type)
        tcp_forwards = applib.get_tcp_forward_connection(self.PARAMETERS)
        acs_ips = []
        for tcp_forward in tcp_forwards:
            if tcp_forward.user_ip == self.PARAMETERS.ssh_client_ip:
                acs_ips.append(tcp_forward.acs_ip)

        self.local_ip_ipmi = None
        for ip in self.PARAMETERS.ipmi_local_ip_list:
            if ip not in acs_ips:
                self.local_ip_ipmi = ip
                break
        
        if not self.local_ip_ipmi:
            raise error.ErrorConectionIPMI('Нет свободных IP адресов для подключения по IPMI!')

    def close(self):
        self.PARAMETERS.log.info(
            'Отключение {name} от хоста {host.name}'.format(name=self.NAME, host=self.HOST)
        )
        
        if self.JUMP and self.JUMP.id != self.HOST.id:
            if getattr(self, 'jump', False) and self.jump.is_active:
                self.jump.stop()

        self.firewall('close')
        
        with schema.db_edit(self.PARAMETERS.engine) as db:
            connection = db.query(schema.Connection).filter(schema.Connection.id == self.connection_id).one()
            connection.date_end = datetime.datetime.now()
            connection.status = 2
            connection.termination = self.TERMINATION,
            connection.error = self.ERROR
            db.flush()
            db.refresh(connection)
        pass

    def connection(self):
        if self.JUMP and self.JUMP.id != self.HOST.id:
            ipmi = [(self.HOST.ilo, int(i)) for i in str(self.ilo_type.ports).split(',')]
            self.PARAMETERS.log.debug('IPMI(connection) ipmi: {}'.format(ipmi))
            self.jump = SSHTunnelForwarder(
                (self.JUMP.ip, self.JUMP.tcp_port),
                ssh_username=self.JUMP.default_login,
                ssh_password=utils.password(self.JUMP.default_password, self.JUMP.id, mask=False),
                remote_bind_addresses=ipmi,
                local_bind_addresses=[('127.0.0.1', ) for i in str(self.ilo_type.ports).split(',')]
            )
            try:
                self.jump.start()
            except BaseSSHTunnelForwarderError as e:
                self.PARAMETERS.log.error(
                    'Ошибка подключения к Jump хосту({}): {}'.format(self.JUMP.name, e.value),
                    pr=True
                )
                self.TERMINATION = 2
                self.ERROR = 'Ошибка подключения к Jump хосту({}): {}'.format(self.JUMP.name, e.value)
                raise error.ErrorConnectionJump('Ошибка подключения к Jump хосту({}): {}'.format(self.JUMP.name, e.value))
            self.PARAMETERS.log.debug(
                'self.jump: {}'.format(self.jump)
            )
            self.PARAMETERS.log.info(
                'Подключение к Jump хосту: {}'.format(self.JUMP.name)
            )

            for ipmi_port in str(self.ilo_type.ports).split(','):
                ip, port = self.jump.tunnel_bindings[(self.HOST.ilo, int(ipmi_port))]
                self.TCP_FORWARD.append(
                    {
                        'connection_id': self.connection_id,
                        'acs_ip': self.local_ip_ipmi,
                        'user_ip': self.PARAMETERS.ssh_client_ip,
                        'local_port': ipmi_port,
                        'forward_ip': ip,
                        'forward_port': port
                    }
                )

        else:
            for ipmi_port in str(self.ilo_type.ports).split(','):
                self.TCP_FORWARD.append(
                    {
                        'connection_id': self.connection_id,
                        'acs_ip': self.local_ip_ipmi,
                        'user_ip': self.PARAMETERS.ssh_client_ip,
                        'local_port': ipmi_port,
                        'forward_ip': self.HOST.ilo,
                        'forward_port': ipmi_port
                    }
                )

        if not applib.tcp_forward_connection_is_active(self.PARAMETERS, self.TCP_FORWARD):
            self.firewall('open')
        
        user_input = ''
        while user_input.lower() != 'exit'.lower():
            user_input = input('Для завершения сессии введите "exit": ')

    def firewall(self, state):
        if len(self.TCP_FORWARD) > 0:
            applib.tcp_forward_connection(self.PARAMETERS, self.TCP_FORWARD, state)
        pass
