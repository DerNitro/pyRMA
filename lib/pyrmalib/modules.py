#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Filename : Modules
    Date: 28.09.2018 06:43
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
import sys
from pyrmalib import schema, parameters, applib, utils, error
import datetime
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError


class Modules:
    NAME = ''
    DESCRIPTION = ''
    PARAMETERS = None

    def __init__(self):
        self.PARAMETERS = None
        self.NAME = None
        self.DESCRIPTION = None
        pass

    def __repr__(self):
        return "{0}".format(self.__dict__)


class ConnectionModules(Modules):
    HOST = None             # type: schema.Host
    CONNECTION_TYPE = None  # type:int
    ERROR = None
    SERVICE = None
    LOGIN = None
    PASSWORD = None
    JUMP = None
    TCP_FORWARD = None
    TERMINATION = 0
    ERROR = ''

    def __init__(self, param: parameters.AppParameters, host: schema.Host):
        super().__init__()
        self.PARAMETERS = param
        self.HOST = host
        self.ERROR = None
        self.SERVICE = None
        self.LOGIN = None
        self.PASSWORD = None
        self.JUMP = None
        self.TCP_FORWARD = []
        self.connection_id = None

    def run(self):
        """
        Запуск подключения
        :return: Возвращает код завершения
        """
        self.PARAMETERS.log.info(
            'Подключение {name} к хосту {host.name}({host.ip})'.format(name=self.NAME, host=self.HOST)
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

        # Строка информации о подключении
        print('=================== pyRMA ===================')
        print('Подключение {name} к хосту {host.name}({host.ip}:{host.tcp_port})'.format(
            name=self.NAME, host=self.HOST)
        )
        if self.SERVICE:
            print('Подключенные сервисы:')
            for i in self.SERVICE:
                print('\t[{name:15}] - {acs_ip}:{local_port} -> {remote_ip}:{remote_port}({describe})'.format(
                    **i, acs_ip=self.PARAMETERS.app_ip_address
                    )
                )
        print('=============================================')

        self.jump = None
        self.services = None

        if self.JUMP and self.JUMP.id != self.HOST.id:
            self.jump = SSHTunnelForwarder(
                (self.JUMP.ip, self.JUMP.tcp_port),
                ssh_username=self.JUMP.default_login,
                ssh_password=utils.password(self.JUMP.default_password, self.JUMP.id, mask=False),
                remote_bind_address=(self.HOST.ip, self.HOST.tcp_port),
                local_bind_address=('127.0.0.1', )
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
            self.HOST.ip = '127.0.0.1'
            self.HOST.tcp_port = self.jump.local_bind_port

        if self.SERVICE:
            services = [(i['remote_ip'], i['remote_port']) for i in self.SERVICE]
            self.PARAMETERS.log.debug('ConnectionModules(run) services: {}'.format(services))
            self.services = SSHTunnelForwarder(
                (self.HOST.ip, self.HOST.tcp_port),
                ssh_username=self.LOGIN,
                ssh_password=self.PASSWORD,
                remote_bind_addresses=services,
                local_bind_addresses=[('127.0.0.1', ) for i in self.SERVICE]
            )
            try:
                self.services.start()
            except BaseSSHTunnelForwarderError as e:
                self.PARAMETERS.log.warning(
                    'Ошибка подключения сервисов: {}'.format(e.value)
                )
                return

            self.PARAMETERS.log.debug(
                'self.services: {}'.format(self.services)
            )
            self.PARAMETERS.log.info(
                'Подключение сервисов к хосту: {}'.format(", ".join([i['name'] for i in self.SERVICE]))
            )

            for service in self.SERVICE:
                ip, port = self.services.tunnel_bindings[(service['remote_ip'],service['remote_port'])]
                self.TCP_FORWARD.append(
                    {
                        'connection_id': self.connection_id,
                        'acs_ip': self.PARAMETERS.app_ip_address,
                        'user_ip': self.PARAMETERS.ssh_client_ip,
                        'local_port': service['local_port'],
                        'forward_ip': ip,
                        'forward_port': port
                    }
                )
        pass

    def close(self):
        """
        Закрывает подключение
        :return: Возвращает код завершения
        """
        self.PARAMETERS.log.info(
            'Отключение {name} от хоста {host.name}'.format(name=self.NAME, host=self.HOST)
        )
        
        if self.JUMP and self.JUMP.id != self.HOST.id:
            if self.jump.is_active:
                self.jump.stop()

        if self.SERVICE:
            if self.services and self.services.is_active:
                self.services.stop()

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
        """
        Инициирует логику подключения к удаленному хосту.
        :return: Возвращает код завершения
        """
        if not applib.tcp_forward_connection_is_active(self.PARAMETERS, self.TCP_FORWARD):
            self.firewall('open')
        
        print(f'\33]0;{self.HOST.name}\a', end='', flush=True)


    def firewall(self, state):
        """
        Формирует правила сетевого экрана.
        :return: Возвращает код завершения
        """
        if len(self.TCP_FORWARD) > 0:
            applib.tcp_forward_connection(self.PARAMETERS, self.TCP_FORWARD, state)
        pass
