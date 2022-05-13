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
import datetime

from pyrmalib import schema, error, parameters, applib, mail, template

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
    access_map = None

    def __init__(self, n_access: int):
        """
        Формируем мапинг правил доступа
        :param n_access: текущее значение доступа int
        """
        self.map = {}
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
    def __init__(self, n_access: int):
        self.access_map = user_access_map
        super().__init__(n_access)


class ConnectionAccess(Access):
    def __init__(self, n_access: int):
        self.access_map = connection_access_map
        super().__init__(n_access)


def get_user_access(param: parameters.Parameters, user, host):
    conn_acc = ConnectionAccess(0)
    user_acc = UserAccess(0)

    if check_access(param, 'ShowHostInformation', h_object=host, user=user):
        user_acc.change('ShowHostInformation', set_access=True)
    if check_access(param, 'EditHostInformation', h_object=host, user=user):
        user_acc.change('EditHostInformation', set_access=True)
    if check_access(param, 'EditDirectory', h_object=host, user=user):
        user_acc.change('EditDirectory', set_access=True)
    if check_access(param, 'EditPrefixHost', h_object=host, user=user):
        user_acc.change('EditPrefixHost', set_access=True)
    if check_access(param, 'ShowLogin', h_object=host, user=user):
        user_acc.change('ShowLogin', set_access=True)
    if check_access(param, 'ShowPassword', h_object=host, user=user):
        user_acc.change('ShowPassword', set_access=True)
    if check_access(param, 'ShowAllSession', h_object=host, user=user):
        user_acc.change('ShowAllSession', set_access=True)
    if check_access(param, 'AccessRequest', h_object=host, user=user):
        user_acc.change('AccessRequest', set_access=True)
    if check_access(param, 'Administrate', h_object=host, user=user):
        user_acc.change('Administrate', set_access=True)

    if check_access(param, 'Connection', h_object=host, user=user):
        conn_acc.change('Connection', set_access=True)
    if check_access(param, 'FileTransfer', h_object=host, user=user):
        conn_acc.change('FileTransfer', set_access=True)
    if check_access(param, 'ConnectionService', h_object=host, user=user):
        conn_acc.change('ConnectionService', set_access=True)
    if check_access(param, 'ConnectionOnlyService', h_object=host, user=user):
        conn_acc.change('ConnectionOnlyService', set_access=True)
    if check_access(param, 'ConnectionIlo', h_object=host, user=user):
        conn_acc.change('ConnectionIlo', set_access=True)

    return user_acc.get_int(), conn_acc.get_int()


def check_access(app_param: parameters.Parameters, access, h_object=None, check_permission=None, user=None):
    """
    Возвращает True|False по разрещенному доступу
    :param user: schema.User.login
    :param check_permission: Строка или Список schema.Permission
    :param app_param: Настроки приложения.
    :param access: Правило доступа из access_map
    :param h_object: хост schema.Host
    :return: bool
    """
    app_param.log.debug('check_access(param, {},{},{},{})'.format(access, h_object, check_permission, user))
    if not user:
        user = app_param.user_info.uid

    if check_permission:
        perm = check_permission
    elif h_object:
        user_access = applib.get_user_access(app_param, user, hid=h_object.id)
        if user_access:
            perm = {'conn_access': user_access.conn_access, 'user_access': user_access.user_access}
        else:
            user_group = applib.get_user_group(app_param, user)
            host_group = applib.get_host_group(app_param, h_object.id) + [0]
            access_list = applib.get_group_access(app_param, user_group, host_group)
            if not access_list:
                return False
            perm = applib.get_group_permission(app_param, [t.subject for t in access_list])
    else:
        perm = applib.get_user_permission(app_param, user)

    app_param.log.debug(perm)

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
            return ConnectionAccess(perm['conn_access']).get(access)
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


def request_access(param: parameters.Parameters, request: schema.RequestAccess):
    ticket = request.ticket
    note = request.note
    with schema.db_select(param.engine) as db:
        host = db.query(schema.Host).filter(schema.Host.id == request.host).one()
        host_group = db.query(schema.GroupHost).filter(schema.GroupHost.host == request.host).all()
    with schema.db_edit(param.engine) as db:
        db.add(request)
        db.flush()
        db.refresh(request)
        action = schema.Action(
            user=param.user_info.login,
            action_type=32,
            date=datetime.datetime.now(),
            message="Запрос доступа до узла {host.name}({request})".format(host=host, request=request)
        )
        db.add(action)
        db.flush()
    user_list = []
    for group in host_group:
        user_list += users_access_list(param, 'AccessRequest', group_host=group.group)
    return mail.send_mail(
        param,
        "Запрос доступа до узла - {host.name} ({user})".format(host=host, user=param.user_info.full_name),
        template.request_access(),
        user_list,
        {
            'host': host.name,
            'ticket': ticket,
            'note': note,
            'user': param.user_info.full_name
        },
        admin_cc=True
    )


def access_request(param: parameters.Parameters, access):
    with schema.db_select(param.engine) as db:
        request = db.query(schema.RequestAccess).filter(schema.RequestAccess.id == access['access'].id).one()
        request_user = db.query(schema.User).filter(schema.User.login == request.user).one()
    with schema.db_edit(param.engine) as db:
        db.query(schema.RequestAccess).filter(
            schema.RequestAccess.id == access['access'].id
        ).update(
            {
                schema.RequestAccess.status: 1,
                schema.RequestAccess.user_approve: param.user_info.login,
                schema.RequestAccess.date_approve: datetime.datetime.now()
            }
        )
        action = schema.Action(
            user=param.user_info.login,
            action_type=33,
            date=datetime.datetime.now(),
            message="Запрос доступа {user.full_name} до узла {host.name} - согласован".format(
                host=access['host'], user=access['user']
            )
        )
        db.add(action)
        u_access, c_access = get_user_access(param, access['user'].login, access['host'])
        conn_access = ConnectionAccess(c_access)
        user_access = UserAccess(u_access)

        if access['access'].connection:
            conn_access.change('Connection', set_access=True)
        if access['access'].file_transfer:
            conn_access.change('FileTransfer', set_access=True)
        if access['access'].ipmi:
            conn_access.change('ConnectionIlo', set_access=True)

        acc = schema.AccessList(
            t_subject=0,
            subject=access['user'].login,
            t_object=0,
            object=access['host'].id,
            date_disable=access['access'].date_access,
            note="Запрос доступа согласован - {}({})".format(param.user_info.full_name, datetime.datetime.now()),
            conn_access=conn_access.get_int(),
            user_access=user_access.get_int(),
            status=1
        )
        db.add(acc)
        db.flush()
        mail.send_mail(
            param,
            "Запрос доступа до узла - {host.name} ({user.full_name}) - разрешен".format(
                host=access['host'], user=access['user']
            ),
            template.access_request(),
            request_user,
            {
                'host': access['host'].name,
                'user_approve': param.user_info.full_name
            },
            admin_cc=True
        )


def deny_request(param: parameters.Parameters, access):
    with schema.db_select(param.engine) as db:
        request = db.query(schema.RequestAccess).filter(schema.RequestAccess.id == access['access'].id).one()
        request_user = db.query(schema.User).filter(schema.User.login == request.user).one()
    with schema.db_edit(param.engine) as db:
        db.query(schema.RequestAccess).filter(
            schema.RequestAccess.id == access['access'].id
        ).update(
            {
                schema.RequestAccess.status: 2,
                schema.RequestAccess.user_approve: param.user_info.login,
                schema.RequestAccess.date_approve: datetime.datetime.now()
            }
        )
        action = schema.Action(
            user=param.user_info.login,
            action_type=34,
            date=datetime.datetime.now(),
            message="Запрос доступа {user.full_name} до узла {host.name} - отклонен".format(
                host=access['host'], user=access['user']
            )
        )
        db.add(action)
        db.flush()
    mail.send_mail(
        param,
        "Запрос доступа до узла - {host.name} ({user.full_name}) - отклонен".format(
            host=access['host'], user=access['user']
        ),
        template.deny_request(),
        request_user,
        {
            'host': access['host'].name,
            'user_approve': param.user_info.full_name
        },
        admin_cc=True
    )


if __name__ == '__main__':
    u = UserAccess(474)
    print(u)
