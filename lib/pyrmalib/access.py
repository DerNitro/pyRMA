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


"""
Модуль контроля и проверки правил доступа.
"""
from pyrmalib import schema
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

user_access_map = {'ShowHostInformation': 0,            # Просмотр информации об узле, автоматом отключает
                                                        # DisableShowLoginPassword и DisableShowPassword
                   'EditHostInformation': 1,            # Редактировать хосты
                   'EditDirectory': 2,                  # Создание|Редактирование директорий
                   'EditPrefixHost': 3,                 # Смена родителя для узлов
                   'DisableShowLoginPassword': 4,       # Отключение видимости логина и пароля
                   'DisableShowPassword': 5,            # Отключение видимости пароля
                   'ShowAllSession': 6,                 # Просмотр сессии пользователя
                   'ShowAllGroupSession': 7,            # Просмотр сессии своей группы
                   'Administrate': 8}                   # Режим "бога"


connection_access_map = {
    'Connection': 1,                # Подключение к узлу
    'FileTransfer': 2,              # Передача файлов
    'ConnectionService': 3,         # Подключение сервисов
    'ConnectionOnlyService': 4,     # Подключение только сервисов
    'ConnectionIlo': 5              # Подключение к интерфейсу управления сервером.
}


class Access:
    map = {}
    access_map = None

    def __init__(self, n_access):
        """
        Формируем мапинг правил доступа
        :param n_access: текущее значение доступа int
        """
        bin_str = '{0:b}'.format(n_access)[::-1].zfill(len(self.access_map))
        for access, n in self.access_map.items():
            self.map[access] = bin_str[n]

    def change(self, access, set_access=False):
        """
        Установка правила для доступа
        :param access: Правило доступа из access_map
        :param set_access: Статус правила, по умолчанию запрещен
        """
        self.map[access] = str(int(set_access))

    def get(self, access):
        """
        Возвращает значение правила доступа.
        :param access: Правило доступа из access_map
        :return: bool
        """
        return bool(int(self.map[access]))

    def get_int(self):
        """
        Воззвращает десятичное представление мапинга правил доступа
        :return: int
        """
        bin_str = []
        for i in sorted(self.access_map, key=self.access_map.get):
            bin_str.append(self.map[i])
        s = ''.join(bin_str)
        return int(s.lstrip('0')[::-1], 2)


class UserAccess(Access):
    access_map = user_access_map


class ConnectionAccess(Access):
    access_map = connection_access_map


def user_check_access(engine, perm_type,  object_id, access):
    """
    Возвращает True|False по разрещенному доступу
    :param engine: Подключение к BD в формате sqlalchemy create_engine
    :param perm_type: значение из schema.Permission.type
    :param object_id: ID пользователя в СУБД
    :param access: Правило доступа из access_map
    :return: bool
    """
    with schema.db_select(engine) as db:
        try:
            permission = db.query(schema.Permission)\
                .filter(schema.Permission.object == object_id)\
                .filter(schema.Permission.type == perm_type)\
                .one()
        except NoResultFound:
            return False
        except MultipleResultsFound:
            return False

    return UserAccess(permission.user_access).get(access)


def connection_check_access(engine, perm_type,  object_id, access):
    """
    Возвращает True|False по разрещенному доступу
    :param engine: Подключение к BD в формате sqlalchemy create_engine
    :param perm_type: значение из schema.Permission.type
    :param object_id: ID пользователя в СУБД
    :param access: Правило доступа из access_map
    :return: bool
    """
    with schema.db_select(engine) as db:
        try:
            permission = db.query(schema.Permission)\
                .filter(schema.Permission.object == object_id)\
                .filter(schema.Permission.type == perm_type)\
                .one()
        except NoResultFound:
            return False
        except MultipleResultsFound:
            return False

    return ConnectionAccess(permission.conn_access).get(access)


def change_access(engine, user_id, access, set_access=False):
    # TODO: Переписать
    """
    Установка правила доступа с записью в СУБД
    :param set_access: bool(), по умолчанию запретить
    :param engine: Подключение к BD в формате sqlalchemy create_engine
    :param user_id: ID пользователя в СУБД
    :param access: Правило доступа из access_map
    """
    try:
        with schema.db_select(engine) as db:
            user = db.query(schema.User).filter(schema.User.login == user_id).one()
    except NoResultFound:
        return False
    except MultipleResultsFound:
        return False

    change = UserAccess(user.permissions)
    change.change(access, set_access=set_access)
    with schema.db_edit(engine) as db:
        db.query(schema.User).filter(schema.User.login == user_id).update({schema.User.permissions: change.get_int()})
