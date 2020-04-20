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

from pyrmalib import schema, error, parameters, applib, mail
from sqlalchemy import create_engine

user_access_map = {
    'ShowHostInformation': 0,       # Просмотр информации об узле
    'EditHostInformation': 1,       # Редактировать хосты
    'EditDirectory': 2,             # Создание|Редактирование директорий
    'EditPrefixHost': 3,            # Смена родителя для узлов
    'ShowLogin': 4,                 # Отображение логина
    'ShowPassword': 5,              # Отображение пароля
    'ShowAllSession': 6,            # Просмотр сессии пользователя
    'AccessRequest': 7,             # Согласование доступов
    'Administrate': 8               # Режим "бога"
}

connection_access_map = {
    'Connection': 0,                # Подключение к узлу
    'FileTransfer': 1,              # Передача файлов
    'ConnectionService': 2,         # Подключение сервисов
    'ConnectionOnlyService': 3,     # Подключение только сервисов
    'ConnectionIlo': 4              # Подключение к интерфейсу управления сервером.
}


class Access:
    map = {}
    access_map = None

    def __init__(self, n_access: int):
        """
        Формируем мапинг правил доступа
        :param n_access: текущее значение доступа int
        """
        bin_str = '{0:b}'.format(n_access).zfill(len(self.access_map))
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
        return int(s, 2)

    def __repr__(self):
        return "{0}".format(self.map)


class UserAccess(Access):
    access_map = user_access_map


class ConnectionAccess(Access):
    access_map = connection_access_map


def check_access(app_param: parameters.Parameters, access, h_object=None, check_permission=None):
    """
    Возвращает True|False по разрещенному доступу
    :param check_permission: Строка или Список schema.Permission
    :param app_param: Настроки приложения.
    :param access: Правило доступа из access_map
    :param h_object: хост schema.Host
    :return: bool
    """
    if check_permission:
        perm = check_permission
    elif h_object:
        user_access = applib.get_user_access(app_param, app_param.user_info.login, hid=h_object.id)
        if user_access:
            perm = {'conn_access': user_access.conn_access, 'user_access': user_access.user_access}
        else:
            user_group = applib.get_user_group(app_param, app_param.user_info.login)
            host_group = applib.get_host_group(app_param, h_object.id) + [0]
            access_list = applib.get_group_access(app_param, user_group, host_group)
            if not access_list:
                return False
            perm = applib.get_group_permission(app_param, [t.subject for t in access_list])
    else:
        perm = applib.get_user_permission(app_param, app_param.user_info.login)

    if user_access_map.get(access) is not None:
        if isinstance(perm, list):
            for i in perm:
                if UserAccess(i.user_access).get(access):
                    return True
            return False
        elif isinstance(perm, schema.Permission):
            return UserAccess(perm.user_access).get(access)
        elif isinstance(perm, dict):
            return UserAccess(perm['user_access']).get(access)
        elif not perm:
            return False
        else:
            app_param.log.critical("user_check_access: value did not schema.Permission")
            raise TypeError('user_check_access: value did not schema.Permission')
    elif connection_access_map.get(access) is not None:
        if isinstance(perm, list):
            for i in perm:
                if ConnectionAccess(i.conn_access).get(access):
                    return True
            return False
        elif isinstance(perm, schema.Permission):
            return ConnectionAccess(perm.conn_access).get(access)
        elif isinstance(perm, dict):
            return UserAccess(perm['conn_access']).get(access)
        elif not perm:
            return False
        else:
            app_param.log.critical("user_check_access: value did not schema.Permission")
            raise TypeError('user_check_access: value did not schema.Permission')
    else:
        raise error.WTF("check_access - not user and not conn!")


def users_access_list(param: parameters.Parameters, access, group_host=None, group_user=None):
    """
    Получение списка пользователей с правом доступа
    :param group_user: Группа пользоватлей
    :param group_host: Группа хостов
    :param param: Настройки приложения
    :param access: Правило доступа из access_map
    :return: list
    """
    group_list = []
    user_list = []

    if group_host and group_user:
        with schema.db_select(param.engine) as db:
            access_list = db.query(schema.AccessList).filter(
                schema.AccessList.t_subject == 1,
                schema.AccessList.t_object == 1,
                schema.AccessList.subject == group_user,
                schema.AccessList.object == group_host
            ).all()
        if len(access_list) > 0:
            for i in access_list:
                group_list.append(i.subject)
        else:
            return None
    elif group_user:
        group_list.append(group_user)
    elif group_host:
        with schema.db_select(param.engine) as db:
            access_list = db.query(schema.AccessList).filter(
                schema.AccessList.t_object == 1,
                schema.AccessList.object == group_host
            ).all()
        if len(access_list) > 0:
            for i in access_list:
                group_list.append(i.subject)
        else:
            return None
    else:
        with schema.db_select(param.engine) as db:
            access_list = db.query(schema.AccessList).filter(
                schema.AccessList.t_object == 1,
                schema.AccessList.object == 0
            ).all()
        if len(access_list) > 0:
            for i in access_list:
                group_list.append(i.subject)
        else:
            return None
    for group in group_list:
        with schema.db_select(param.engine) as db:
            perm = db.query(schema.Permission).filter(
                schema.Permission.t_subject == 1,
                schema.Permission.subject == group
            ).all()
            if check_access(param, access, check_permission=perm):
                users = db.query(schema.GroupUser).filter(schema.GroupUser.group == group).all()
                for u in users:
                    user_list.append(applib.get_user(param, u.user)['user'])

    return user_list


if __name__ == '__main__':
    p = parameters.AppParameters()
    p.engine = engine = create_engine(
        '{0}://{1}:{2}@{3}:{4}/{5}'.format(
            p.dbase,
            p.dbase_param["user"],
            p.dbase_param["password"],
            p.dbase_param["host"],
            p.dbase_param["port"],
            p.dbase_param["database"]
        )
    )
    print(users_access_list(p, 'Administrate'))
