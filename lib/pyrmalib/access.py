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
from sqlalchemy import or_, and_

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


def get_permission(app_param: parameters.Parameters, subj):
    # select p.* from "permission" p
    # where
    #   (p.subject = subj and p.t_subject = 0)
    #   or (p.subject in (select gu."group" from group_user gu where gu."user" = subj) and p.t_subject = 1);
    with schema.db_select(app_param.engine) as db:
        try:
            user_groups = db.query(schema.GroupUser.group) \
                .filter(schema.GroupUser.user == subj) \
                .group_by(schema.GroupUser.group).subquery()

            permission = db.query(schema.Permission)\
                .filter(or_(
                            and_(schema.Permission.subject == subj, schema.Permission.t_subject == 0),
                            and_(schema.Permission.subject.in_(user_groups), schema.Permission.t_subject == 1)
                            )
                        ).all()
            return permission
        except NoResultFound:
            pass
        except MultipleResultsFound:
            pass

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

    if check_permission:
        perm = check_permission
    else:
        perm = get_permission(app_param, app_param.user_info.login)

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
    user = UserAccess(0)
    print(user)
    print(user.get_int())
    user.change('Administrate', set_access=True)
    print(user)
    print(user.get_int())
