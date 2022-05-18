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
from pyrmalib import schema, parameters, applib, utils
import datetime
from sshtunnel import SSHTunnelForwarder

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
    HOST = None  # type: schema.Host
    CONNECTION_TYPE = None  # type:int
    ERROR = None
    SERVICE = None
    LOGIN = None
    PASSWORD = None
    JUMP = None

    def __init__(self, param: parameters.AppParameters, host: schema.Host):
        super().__init__()
        self.PARAMETERS = param
        self.HOST = host
        self.ERROR = None
        self.SERVICE = None
        self.LOGIN = None
        self.PASSWORD = None
        self.JUMP = None
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
            status=0,
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
        print('=================== PyRMA ===================')
        print('Подключение {name} к хосту {host.name}({host.ip})'.format(name=self.NAME, host=self.HOST))
        if self.SERVICE:
            print('Подключенные сервисы:')
            for i in self.SERVICE:
                print('\t[{name:15}] - {local_port} -> {remote_ip}:{remote_port}({describe})'.format(**i))
        print('=============================================')

        if self.JUMP and self.JUMP.id != self.HOST.id:
            self.jump = SSHTunnelForwarder(
                self.JUMP.ip,
                ssh_username=self.JUMP.default_login,
                ssh_password=utils.password(self.JUMP.default_password, self.JUMP.id, mask=False),
                remote_bind_address=(self.HOST.ip, self.HOST.tcp_port),
                local_bind_address=('127.0.0.1', )
            )
            self.jump.start()
            self.PARAMETERS.log.debug(
                'self.jump: {}'.format(self.jump)
            )
            self.PARAMETERS.log.info(
                'Подключение к Jump хосту: {}'.format(self.JUMP.name)
            )
            self.HOST.ip = '127.0.0.1'
            self.HOST.tcp_port = self.jump.local_bind_port
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
            self.jump.stop()
        
        with schema.db_edit(self.PARAMETERS.engine) as db:
            connection = db.query(schema.Connection).filter(schema.Connection.id == self.connection_id).one()
            connection.date_end = datetime.datetime.now()
            connection.status = 2
            connection.termination = 0
            db.flush()
            db.refresh(connection)
        pass

    def connection(self):
        """
        Инициирует логику подключения к удаленному хосту.
        :return: Возвращает код завершения
        """
        self.firewall()
        pass

    def firewall(self):
        """
        Формирует правила сетевого экрана.
        :return: Возвращает код завершения
        """
        pass
