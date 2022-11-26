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

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime
from contextlib import contextmanager

Base = declarative_base()

@contextmanager
def db_select(engine):
    cl_session = sessionmaker(bind=engine, expire_on_commit=False)
    session = cl_session()
    try:
        yield session
    except:
        raise
    finally:
        session.close()


@contextmanager
def db_edit(engine):
    cl_session = sessionmaker(bind=engine, expire_on_commit=False)
    session = cl_session()
    try:
        yield session
        session.commit()
    except:
        raise
    finally:
        session.close()


class User(Base):
    """
    Таблица пользователей системой доступа

    uid: ID пользователя
    login: Логин пользователя
    full_name: Имя пользователя
    date_create: Дата регистрации
    disable: Флаг отключения пользователя
    date_disable: Дата отключения
    ip: IP адрес/сеть пользователя, для проверки подключения
    email: адрес электронной почты
    prefix: Префикс пользователя(не реализованный функционал)
    check: Флаг проверки пользователя
        0 - Новый пользователь, требуется проверка
        1 - Подтвержденный пользователь
    admin: Флаг определения пользователю прав администратора
    """
    __tablename__ = 'user'

    uid = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, unique=True)
    login = sqlalchemy.Column(sqlalchemy.String(256), unique=True)
    full_name = sqlalchemy.Column(sqlalchemy.String(256))
    date_create = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    disable = sqlalchemy.Column(sqlalchemy.BOOLEAN(), default=False)
    date_disable = sqlalchemy.Column(sqlalchemy.DateTime)
    ip = sqlalchemy.Column(sqlalchemy.String(256))
    email = sqlalchemy.Column(sqlalchemy.String(256), unique=True)
    prefix = sqlalchemy.Column(sqlalchemy.String(100))
    check = sqlalchemy.Column(sqlalchemy.Integer)
    admin = sqlalchemy.Column(sqlalchemy.BOOLEAN(), default=False)

    def __repr__(self):
        return "{0}".format(self.__dict__)

    def get_id(self):
        return int(self.login)


class Action(Base):
    """
    Логирование действий пользователей в системе

    id: ID события
    user: ID пользователя
    action_type: ID события
    date: Дата и время
    message: Комментарий
    """
    __tablename__ = 'action'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer)
    action_type = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    message = sqlalchemy.Column(sqlalchemy.Text())

    def __repr__(self):
        return "{0}".format(self.__dict__)


class ActionType(Base):
    """
    Типы событий

    id: ID события
    name: Название события
    """
    __tablename__ = 'action_type'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String(256))

    def __repr__(self):
        return "{0}".format(self.__dict__)


class RequestAccess(Base):
    """
    Таблица запросов доступа.

    id: ID запроса доступа
    user: ID пользователя
    host: ID узла подключения
    date_request: Дата запроса доступа
    date_access: Дата действия запроса доступа
    status:
        0 - запрос доступа
        1 - Запрос согласован
        2 - запрос отменен
    user_approve: ID пользователя согласовавшего доступ
    date_approve: Дата согласования
    ticket: Номер заявки
    note: Дополнительное описание
    connection: Флаг запроса на подключение
    file_transfer: Флаг запроса на передачу файлов
    ipmi: : Флаг запроса на подключение к интерфейсу управления
    """
    __tablename__ = 'request_access'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    host = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    date_request = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, default=datetime.datetime.now())
    date_access = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    status = sqlalchemy.Column(sqlalchemy.Integer)
    user_approve = sqlalchemy.Column(sqlalchemy.Integer)
    date_approve = sqlalchemy.Column(sqlalchemy.DateTime)
    ticket = sqlalchemy.Column(sqlalchemy.String)
    note = sqlalchemy.Column(sqlalchemy.Text)
    connection = sqlalchemy.Column(sqlalchemy.Boolean)
    file_transfer = sqlalchemy.Column(sqlalchemy.Boolean)
    ipmi = sqlalchemy.Column(sqlalchemy.Boolean)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Host(Base):
    """
    Информация о узлах сети

    id: ID узла
    name: Название узла
    ip: IP адрес
    type: Тип записи
        1 - Хост
        2 - Директория
    connection_type: ID протокола подключения
    file_transfer_type: ID протокола передачи файлов
    describe: Краткое описание узла
    ilo: IP адрес интерфейса управления
    ilo_type: ID типа интерфейса подключения
    parent: ID родительского узла
    remove: Флаг удаления узла
    default_login: Логин подключения по умолчанию
    default_password: Пароль подключения по умолчанию
    tcp_port: TCP порт подключения
    prefix: Префикс узла(Не реализованный функционал)
    proxy: Флаг что узел является Jump
    note: Описание узла
    """
    __tablename__ = 'host'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(50))
    ip = sqlalchemy.Column(sqlalchemy.String())
    # type:
    # 1 - Хост
    # 2 - Директория
    type = sqlalchemy.Column(sqlalchemy.Integer)
    connection_type = sqlalchemy.Column(sqlalchemy.Integer)
    file_transfer_type = sqlalchemy.Column(sqlalchemy.Integer)
    describe = sqlalchemy.Column(sqlalchemy.String(256))
    ilo = sqlalchemy.Column(sqlalchemy.String)
    ilo_type = sqlalchemy.Column(sqlalchemy.Integer)
    parent = sqlalchemy.Column(sqlalchemy.Integer)
    remove = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    default_login = sqlalchemy.Column(sqlalchemy.String)
    default_password = sqlalchemy.Column(sqlalchemy.String)
    tcp_port = sqlalchemy.Column(sqlalchemy.Integer)
    prefix = sqlalchemy.Column(sqlalchemy.String)
    proxy = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    note = sqlalchemy.Column(sqlalchemy.Text)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class IPMIType(Base):
    """
    Типы подключений удаленного управления серверами
    Например:
        HP ILO
        Microsystem IPMI

    id: ID типа интерфейса подключения
    name: Название
    vendor: Вендор интерфейса управления
    ports: Список портов
    """
    __tablename__ = 'ilo_type'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(10))
    vendor = sqlalchemy.Column(sqlalchemy.String(256))
    ports = sqlalchemy.Column(sqlalchemy.String(256))

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Service(Base):
    """
    Дополнительные подключения к сервисам

    id: ID
    type: TCP порт сервиса
    host: ID узла для которого подключен сервис
    local_port: TCP порт на системе доступа
    remote_port: TCP порт назначения
    remote_ip: IP адрес назначения
    describe: Дополнительное описание
    """
    __tablename__ = 'service'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    type = sqlalchemy.Column(sqlalchemy.Integer)
    host = sqlalchemy.Column(sqlalchemy.Integer)
    local_port = sqlalchemy.Column(sqlalchemy.Integer)
    remote_port = sqlalchemy.Column(sqlalchemy.Integer)
    remote_ip = sqlalchemy.Column(sqlalchemy.String, default='127.0.0.1')
    describe = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class ServiceType(Base):
    """
    Список доступных подключений к сервисов

    name: Название сервиса
    default_port: TCP порт сервиса
    """
    __tablename__ = 'service_type'
    name = sqlalchemy.Column(sqlalchemy.String(), unique=True)
    default_port = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, unique=True)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class JumpHost(Base):
    """
    Назначенные Jump хосты

    id: ID
    host: ID узла
    jump: ID Jump узла
    """
    __tablename__ = 'jump'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    host = sqlalchemy.Column(sqlalchemy.Integer)
    jump = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Connection(Base):
    """
    Список подключений

    id: ID
    status: Статус подключения
        1 - Подключен
        2 - Отключен
        3 - Требуется отключить
    user: ID пользователя
    host: ID узла
    connection_type: Тип подключения
        1 - Терминальное подключение
        2 - Передача файлов
        3 - Подключение к интерфейсу управления
        4 - Подключение только сервисов
    date_start: Дата начала подключения
    date_end: Дата завершения подключения
    error: Ошибка подключения
    termination: Тип завершения подключения
        0 - Нормальное завершение
        1 - Принудительное завершение
        2 - Ошибка
    session: ID пользовательской сессии
    """
    __tablename__ = 'connection'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    status = sqlalchemy.Column(sqlalchemy.Integer)
    user = sqlalchemy.Column(sqlalchemy.Integer)
    host = sqlalchemy.Column(sqlalchemy.Integer)
    connection_type = sqlalchemy.Column(sqlalchemy.Integer)
    date_start = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    date_end = sqlalchemy.Column(sqlalchemy.DateTime)
    error = sqlalchemy.Column(sqlalchemy.String)
    termination = sqlalchemy.Column(sqlalchemy.Integer)
    session = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Session(Base):
    """
    Таблица подключений к pyRMA

    id: ID пользовательской сессии
    user: ID пользователя
    date_start: Дата начала сессии
    date_end: Дата завершения сессии
    pid: PID сессии
    ppid: PPID сессии
    ip: IP пользователя
    status: Статус сессии
        0 - Подключен
        1 - Отключен
    termination: Причина завершения
        0 - Нормальное завершение
    ttyrec: Расположение файла записи сессии
    """
    __tablename__ = 'session'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer)
    date_start = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    date_end = sqlalchemy.Column(sqlalchemy.DateTime)
    pid = sqlalchemy.Column(sqlalchemy.Integer)
    ppid = sqlalchemy.Column(sqlalchemy.Integer)
    ip = sqlalchemy.Column(sqlalchemy.String)
    status = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    termination = sqlalchemy.Column(sqlalchemy.Integer)
    ttyrec = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class ConnectionType(Base):
    """
    Информация о способах подключения

    id: ID протокола подключения
    name: Название протокола
    """
    __tablename__ = 'connection_type'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(20), unique=True)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class FileTransferType(Base):
    """
    Информация о способах подключения

    id: ID протокола передачи данных
    name: Название протокола
    """
    __tablename__ = 'file_transfer_type'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(20), unique=True)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Prefix(Base):
    """
    Список префиксов(Не реализованный функционал)

    id: ID
    name: Название
    note: Описание
    """
    __tablename__ = 'prefix'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    note = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Group(Base):
    """
    Таблица определения групп для пользователей, хостов.

    id: ID группы
    name: Название
    type: Тип группы
        0 - Пользователи
        1 - Узлы
    """
    __tablename__ = 'group'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    type = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class GroupHost(Base):
    """
    Таблица соотношения хостов с группами

    id: ID
    host: ID узла
    group: ID группы
    """
    __tablename__ = 'group_host'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    host = sqlalchemy.Column(sqlalchemy.Integer)
    group = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class GroupUser(Base):
    """
    Таблица соотношения пользователей с группами

    id: ID
    user: ID пользователя
    group: ID группы
    """
    __tablename__ = 'group_user'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer)
    group = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Permission(Base):
    """
    Таблица разрешений для пользователей, групп, хостов...
    id: ID
    t_subject: Тип разрешения
        0 - Пользователь
        1 - Группа
    subject: ID пользователя/группы
    conn_access: Значение разрешений подключений
    user_access: Значение пользовательских разрешений
    """
    __tablename__ = 'permission'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    t_subject = sqlalchemy.Column(sqlalchemy.Integer)
    subject = sqlalchemy.Column(sqlalchemy.Integer)
    conn_access = sqlalchemy.Column(sqlalchemy.Integer)
    user_access = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class AccessList(Base):
    """
    Таблица разрешенных доступов

    id: ID
    t_subject: Тип субъекта запроса доступа
        0 - Пользователь
        1 - Группа пользователей
    subject: ID пользователя/группы
    t_object: Тип объекта доступа
        0 - Узел
        1 - Группа узлов
    object: ID узла/группы
    date_disable: Дата действия доступа
    note: Описание
    conn_access: Значение разрешений подключений 
    user_access: Значение пользовательских разрешений
    status: Статус подтверждения доступа
        0 - Не подтверждено
        1 - Подтверждено
    """
    __tablename__ = 'access_list'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    t_subject = sqlalchemy.Column(sqlalchemy.Integer)
    subject = sqlalchemy.Column(sqlalchemy.Integer)
    t_object = sqlalchemy.Column(sqlalchemy.Integer)
    object = sqlalchemy.Column(sqlalchemy.Integer)
    date_disable = sqlalchemy.Column(sqlalchemy.DateTime)
    note = sqlalchemy.Column(sqlalchemy.Text)
    conn_access = sqlalchemy.Column(sqlalchemy.Integer)
    user_access = sqlalchemy.Column(sqlalchemy.Integer)
    status = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class PasswordList(Base):
    """
    Таблица замаскированных пользовательских паролей.

    id: ID
    user: ID пользователя
    host: ID узла
    login: Логин подключения
    password: Пароль подключения
    """
    __tablename__ = 'password'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer)
    host = sqlalchemy.Column(sqlalchemy.Integer)
    login = sqlalchemy.Column(sqlalchemy.String)
    password = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class ForwardTCP(Base):
    """
    Таблица активных пробросов портов

    id: ID
    connection_id: ID подключения
    user_ip: IP адрес пользователя
    acs_ip: IP адрес системы доступа
    local_port: TCP порт системы доступа для организации проброса
    forward_ip: IP адрес назначения
    forward_port: TCP порт назначения
    state:
        0 - Завешено 
        1 - Активно
    """
    __tablename__ = 'tcp_port_forward'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    connection_id = sqlalchemy.Column(sqlalchemy.Integer)
    user_ip = sqlalchemy.Column(sqlalchemy.String(20))
    acs_ip = sqlalchemy.Column(sqlalchemy.String(20))
    local_port = sqlalchemy.Column(sqlalchemy.Integer)
    forward_ip = sqlalchemy.Column(sqlalchemy.String(20))
    forward_port = sqlalchemy.Column(sqlalchemy.Integer)
    state = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class FileTransfer(Base):
    """
    Таблица регистрации переданных файлов

    id: ID
    connection_id: ID подключения
    file_name: Название переданного файла
    file_name_tgz: Путь хранения копии файла
    date_transfer: Дата передачи файла
    md5: MD5 сумма переданного файла
    direction: Направление передачи
    """
    __tablename__ = 'file_transfer'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    connection_id = sqlalchemy.Column(sqlalchemy.Integer)
    file_name = sqlalchemy.Column(sqlalchemy.String)
    file_name_tgz = sqlalchemy.Column(sqlalchemy.String)
    date_transfer = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    md5 = sqlalchemy.Column(sqlalchemy.String)
    direction = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class CaptureTraffic(Base):
    """
    Таблица хранения данных о tcp дампах

    id: ID
    connection_id: ID подключения
    file_name: Расположения файла дампа
    service_port: ID сервиса
    """
    __tablename__ = 'capture_traffic'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    connection_id = sqlalchemy.Column(sqlalchemy.Integer)
    file_name = sqlalchemy.Column(sqlalchemy.String)
    service_port = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


if __name__ == '__main__':
    pass
