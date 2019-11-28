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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Sequence
import datetime
from contextlib import contextmanager

Base = declarative_base()

action_type = {
    1: "Вход в систему доступа",
    10: "Создание директории",
    11: "Редактирование директории",
    12: "Удаление директории",
    20: "Создание хоста",
    21: "Редактирование хоста",
    22: "Удаление хоста",
    23: "Добавление сервиса",
    24: "Удаление сервиса",
    25: "Добавление маршрута",
    26: "Очистка маршрута",
    30: "Добавление правила доступа",
    31: "Удаление правила доступа",
    32: "Запрос доступа",
    33: "Подтверждение доступа",
    34: "От",
    50: "Восстановление пароля",
    51: "Изменение правил доступа",
    52: "Добавление группы",
    53: "Добавление группы к пользователю",
    54: "Добавление группы к хосту",
    55: "Удаление группы у пользователя",
    56: "Удаление группы у хоста",
    57: "Отключение пользователя",
    58: "Включение пользователя",
    59: "Смена пароля"
}


@contextmanager
def db_select(engine):
    cl_session = sessionmaker(bind=engine)
    session = cl_session()
    try:
        yield session
    except:
        raise
    finally:
        session.close()


@contextmanager
def db_edit(engine):
    cl_session = sessionmaker(bind=engine)
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
    Таблица пользователй системой доступа.
    check:
        0 - Новый пользователь, требуется проверка
        1 - Подтвержденный пользователь
    """
    __tablename__ = 'user'

    login = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, unique=True)
    full_name = sqlalchemy.Column(sqlalchemy.String(256))
    date_create = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    disable = sqlalchemy.Column(sqlalchemy.BOOLEAN(), default=False)
    date_disable = sqlalchemy.Column(sqlalchemy.DateTime)
    ip = sqlalchemy.Column(sqlalchemy.String(256))
    email = sqlalchemy.Column(sqlalchemy.String(256), unique=True)
    prefix = sqlalchemy.Column(sqlalchemy.String(100))
    check = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)

    def get_id(self):
        return int(self.login)


class AAAUser(Base):
    """
    Таблица для авторизации пользователей SSH PAM
    """
    __tablename__ = 'aaa_user'

    username = sqlalchemy.Column(sqlalchemy.String(16), unique=True)
    uid = sqlalchemy.Column(sqlalchemy.Integer, Sequence('aaa_user_uid_seq', start=5000, increment=1), primary_key=True)
    gid = sqlalchemy.Column(sqlalchemy.Integer, default=5000)
    gecos = sqlalchemy.Column(sqlalchemy.String(128))
    homedir = sqlalchemy.Column(sqlalchemy.String(255), default='/home/acs/')
    shell = sqlalchemy.Column(sqlalchemy.String(64), default='/bin/sh')
    password = sqlalchemy.Column(sqlalchemy.String(34))
    lstchg = sqlalchemy.Column(sqlalchemy.BIGINT)
    min = sqlalchemy.Column(sqlalchemy.BIGINT, default=0)
    max = sqlalchemy.Column(sqlalchemy.BIGINT, default=99999)
    warn = sqlalchemy.Column(sqlalchemy.BIGINT, default=0)
    inact = sqlalchemy.Column(sqlalchemy.BIGINT, default=0)
    expire = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    flag = sqlalchemy.Column(sqlalchemy.BIGINT)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class AAAGroup(Base):
    """
    Список групп PAM
    """
    __tablename__ = 'aaa_group'

    gid = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(16), default='', unique=True)
    password = sqlalchemy.Column(sqlalchemy.String(34))

    def __repr__(self):
        return "{0}".format(self.__dict__)


class AAAGroupList(Base):
    """
    Включение пользователей в группы PAM
    """
    __tablename__ = 'aaa_grouplist'

    rowid = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    gid = sqlalchemy.Column(sqlalchemy.Integer)
    username = sqlalchemy.Column(sqlalchemy.String(16))

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Action(Base):
    """
    Логирование действий пользователей в системе
    """
    __tablename__ = 'action'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    action_type = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    message = sqlalchemy.Column(sqlalchemy.Text())

    def __repr__(self):
        return "{0}".format(self.__dict__)


class ActionType(Base):
    """
    Типы событий
    """
    __tablename__ = 'action_type'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String(256))

    def __repr__(self):
        return "{0}".format(self.__dict__)


class RequestAccess(Base):
    """
    Табллица запросов доступа.
    status:
        0 - запрос доступа
        1 - Запрос согласован
        2 - запрос отменен
    """
    __tablename__ = 'request_access'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    host = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    date_request = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    date_access = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    status = sqlalchemy.Column(sqlalchemy.Integer)
    user_approve = sqlalchemy.Column(sqlalchemy.Integer)
    date_approve = sqlalchemy.Column(sqlalchemy.DateTime)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Parameter(Base):
    """
    Параметры приложения.
    """
    __tablename__ = 'parameter'
    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True, unique=True)
    value = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Host(Base):
    """
    Информация о узлах сети
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


class IloType(Base):
    """
    Типы подключений удаленного управления серверами
    Например:
        HP ILO
        Microsystem IPMI
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
    """
    __tablename__ = 'service'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    type = sqlalchemy.Column(sqlalchemy.Integer)
    host = sqlalchemy.Column(sqlalchemy.Integer)
    local_port = sqlalchemy.Column(sqlalchemy.Integer)
    remote_port = sqlalchemy.Column(sqlalchemy.Integer)
    remote_ip = sqlalchemy.Column(sqlalchemy.String)
    internal = sqlalchemy.Column(sqlalchemy.Boolean, server_default='f', default=False)
    describe = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class ServiceType(Base):
    """
    Список доступных подключений к сервисов
    """
    __tablename__ = 'service_type'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(20))
    default_port = sqlalchemy.Column(sqlalchemy.Integer)
    plugin = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class RouteMap(Base):
    """
    Дополнительный маршрут до узлов
    """
    __tablename__ = 'route'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    sequence = sqlalchemy.Column(sqlalchemy.Integer)
    host = sqlalchemy.Column(sqlalchemy.Integer)
    route = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Connection(Base):
    """
    Список подключений
    status:
        0 - Создание подключения
        1 - Подключен
        2 - Отключен
    termination:
        0 - Нормальное завершение
        1 - Принудительное завершение
        2 - Ошибка
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

    def __repr__(self):
        return "{0}".format(self.__dict__)


class ConnectionType(Base):
    """
    Информация о способах подключения
    """
    __tablename__ = 'connection_type'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(20), unique=True)
    default_port = sqlalchemy.Column(sqlalchemy.Integer)
    plugin = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class FileTransferType(Base):
    """
    Информация о способах подключения
    """
    __tablename__ = 'file_transfer_type'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(20), unique=True)
    default_port = sqlalchemy.Column(sqlalchemy.Integer)
    plugin = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Prefix(Base):
    """
    Список префиксов
    """
    __tablename__ = 'prefix'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    note = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class RestorePassword(Base):
    """
    Таблица запросов восстановления паролей.
    status:
    0 - Отклонен
    1 - Запрос смены пароля
    2 - Запрос выполнен
    """
    # TODO: в демон добавить контроль активных запросов.

    __tablename__ = 'restore_password'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, primary_key=True)
    status = sqlalchemy.Column(sqlalchemy.Integer)
    date = sqlalchemy.Column(sqlalchemy.DateTime)
    date_complete = sqlalchemy.Column(sqlalchemy.DateTime)
    key = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Group(Base):
    """
    Таблица определения групп для пользователей, хостов, сервисов.
    type:
        0 - Users
        1 - Hosts
        2 - Services
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
    t_*:
        0 - User
        1 - Group
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
    Таблица разрешеных доступов
    """
    __tablename__ = 'access_list'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    t_subject = sqlalchemy.Column(sqlalchemy.Integer)
    subject = sqlalchemy.Column(sqlalchemy.Integer)
    t_object = sqlalchemy.Column(sqlalchemy.Integer)
    object = sqlalchemy.Column(sqlalchemy.Integer)
    date_disable = sqlalchemy.Column(sqlalchemy.DateTime)
    note = sqlalchemy.Column(sqlalchemy.Text)


class PasswordList(Base):
    """
    Таблица замаскированных паролей.
    """
    __tablename__ = 'password'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer)
    host = sqlalchemy.Column(sqlalchemy.Integer)
    login = sqlalchemy.Column(sqlalchemy.String)
    password = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "{0}".format(self.__dict__)


if __name__ == '__main__':
    engine = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format('postgresql',
                                                              'acs',
                                                              'acs',
                                                              'localhost',
                                                              '5432',
                                                              'acs'
                                                              ))
    # AccessList.__table__.create(bind=engine)
    # for key, value in action_type.items():
    #     with db_edit(engine) as db:
    #         db.add(ActionType(id=key, name=value))
    # with db_edit(engine) as db:
    #     db.add(AAAUser(username='administrator', password='e10adc3949ba59abbe56e057f20f883e'))
    #     db.add(AAAUser(username='sergey', password='298b5acec4518ad08d53fee1d3f413e7'))
