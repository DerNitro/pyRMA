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

from pyrmalib import schema, error, parameters
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

"""
Модуль контроля и проверки правил доступа.
Режимы(приоритет от наименьшего к наибольшему.):
    1.  Общий режим группы пользователей 
    2.  Общий режим группы хостов
    3.  Общий режим пользователя
    4.  Группа пользователей -> Група хостов
    5.  Группа пользователей -> Хост
    6.  Пользователь -> Группа хостов
    7.  Пользователь -> Хост
"""

user_access_map = {
    'ShowHostInformation': 0,       # Просмотр информации об узле
    'EditHostInformation': 1,       # Редактировать хосты
    'EditDirectory': 2,             # Создание|Редактирование директорий
    'EditPrefixHost': 3,            # Смена родителя для узлов
    'ShowLogin': 4,                 # Отображение логина
    'ShowPassword': 5,              # Отображение пароля
    'ShowAllSession': 6,            # Просмотр сессии пользователя
    'ShowAllGroupSession': 7,       # Просмотр сессии своей группы
    'Administrate': 8               # Режим "бога"
}

connection_access_map = {
    'Connection': 0,                # Подключение к узлу
    'FileTransfer': 1,              # Передача файлов
    'ConnectionService': 2,         # Подключение сервисов
    'ConnectionOnlyService': 3,     # Подключение только сервисов
    'ConnectionIlo': 4              # Подключение к интерфейсу управления сервером.
}


def get_permission(app_param: parameters.Parameters, subj, t_subj=0, obj=None, t_obj=None):
    # Пользователь -> Хост
    global permission
    if t_subj == 0 and t_obj == 2:
        with schema.db_select(app_param.engine) as db:
            try:
                permission = db.query(schema.Permission) \
                    .filter(schema.Permission.subject == subj) \
                    .filter(schema.Permission.t_subject == t_subj) \
                    .filter(schema.Permission.object == obj) \
                    .filter(schema.Permission.t_object == t_obj) \
                    .one()
                return permission
            except NoResultFound:
                pass
            except MultipleResultsFound:
                raise error.QueryError("Multiple Results Found schema.Permission: U: {0} H: {1}".format(subj, obj))

    # Пользователь -> Группа хостов
    if t_subj == 0 and (t_obj == 2 or t_obj == 1):
        with schema.db_select(app_param.engine) as db:
            try:
                host_groups = db.query(schema.GroupHost.group) \
                    .filter(schema.GroupHost.host == obj) \
                    .group_by(schema.GroupHost.group).subquery()

                permission = db.query(schema.Permission) \
                    .filter(schema.Permission.t_object == 2) \
                    .filter(schema.Permission.object.in_(host_groups)) \
                    .filter(schema.Permission.t_subject == t_subj) \
                    .filter(schema.Permission.subject == subj).all()
            except NoResultFound:
                pass

            if len(permission) != 0:
                return permission

    # Группа пользователей -> Хост
    if (t_subj == 0 or t_subj == 1) and t_obj == 2:
        with schema.db_select(app_param.engine) as db:
            try:
                user_groups = db.query(schema.GroupUser.group) \
                    .filter(schema.GroupUser.user == subj) \
                    .group_by(schema.GroupUser.group).subquery()

                permission = db.query(schema.Permission) \
                    .filter(schema.Permission.t_object == t_obj) \
                    .filter(schema.Permission.subject.in_(user_groups)) \
                    .filter(schema.Permission.t_subject == 1) \
                    .filter(schema.Permission.subject == subj).all()
            except NoResultFound:
                pass

            if len(permission) != 0:
                return permission
        pass
    # Группа пользователей -> Група хостов
    if (t_subj == 0 or t_subj == 1) and (t_obj == 2 or t_obj == 1):
        with schema.db_select(app_param.engine) as db:
            try:
                user_groups = db.query(schema.GroupUser.group) \
                    .filter(schema.GroupUser.user == subj) \
                    .group_by(schema.GroupUser.group).subquery()

                host_groups = db.query(schema.GroupHost.group) \
                    .filter(schema.GroupHost.host == obj) \
                    .group_by(schema.GroupHost.group).subquery()

                permission = db.query(schema.Permission) \
                    .filter(schema.Permission.t_object == 1) \
                    .filter(schema.Permission.t_subject == 1) \
                    .filter(schema.Permission.subject.in_(user_groups)) \
                    .filter(schema.Permission.object.in_(host_groups)) \
                    .filter(schema.Permission.subject == subj).all()
            except NoResultFound:
                pass

            if len(permission) != 0:
                return permission
        pass

    # Общий режим пользователя
    # Общий режим группы хостов
    # Общий режим группы пользователей
    with schema.db_select(app_param.engine) as db:
        try:
            permission = db.query(schema.Permission) \
                .filter(schema.Permission.subject == subj) \
                .filter(schema.Permission.t_subject == t_subj) \
                .filter(schema.Permission.t_object.is_(None)) \
                .filter(schema.Permission.object.is_(None)) \
                .one()
            return permission
        except NoResultFound:
            pass
        except MultipleResultsFound:
            raise error.QueryError("Multiple Results Found schema.Permission: U: {0}".format(subj))

    return False


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
        return int(s.lstrip('0')[::-1], 2)

    def __repr__(self):
        return "{0}".format(self.map)


class UserAccess(Access):
    access_map = user_access_map


class ConnectionAccess(Access):
    access_map = connection_access_map


def check_access(app_param: parameters.Parameters, access, h_object=None):
    """
    Возвращает True|False по разрещенному доступу
    :param app_param: Настроки приложения.
    :param access: Правило доступа из access_map
    :param h_object: группа/хост
    :return: bool
    """

    if h_object is None:
        obj = None
        t_obj = None
    elif isinstance(h_object, schema.Host):
        obj = h_object.id
        t_obj = 2
    elif isinstance(h_object, schema.GroupHost):
        obj = h_object.group
        t_obj = 1
    else:
        raise error.WTF('не корректно указан host_object!')

    perm = get_permission(app_param, app_param.user_info.login, obj=obj, t_obj=t_obj)

    if user_access_map.get(access) is not None:
        if isinstance(perm, list):
            for i in perm:
                if UserAccess(i.user_access).get(access):
                    return True
            return False
        elif isinstance(perm, schema.Permission):
            return UserAccess(perm.user_access).get(access)
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
        elif not perm:
            return False
        else:
            app_param.log.critical("user_check_access: value did not schema.Permission")
            raise TypeError('user_check_access: value did not schema.Permission')
    else:
        raise error.WTF("check_access - not user and not conn!")


def get_password(app_param: parameters.Parameters, user, host):
    """
    Возвращает schema.Password
    :param app_param: Настроки приложения.
    :param user: Идентификатор пользователя
    :param host: Идентификатор хоста
    :return: False or schema.Password
    """
    pass


if __name__ == '__main__':
    pass
