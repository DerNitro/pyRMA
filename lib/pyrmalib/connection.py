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

from pyrmalib import modules, dict, applib, parameters, schema, access


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

    def __init__(self, param: parameters.AppParameters, host: schema.Host):
        super().__init__(param, host)
        self.NAME = 'SFTP'
        self.DESCRIPTION = 'Модуль передачи файлов по SFTP'
        self.CONNECTION_TYPE = dict.conn_type_dict['File Transfer']

    def connection(self):
        super().connection()
        


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
