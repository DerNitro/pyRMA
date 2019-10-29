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

# -*- coding: utf-8 -*-
# encoding: utf-8
import json
import psutil
import os
import random
from pyrmalib import schema, utils, email, template, parameters, error, access, forms
from functools import wraps
import hashlib
import sqlalchemy
import datetime
import string
from flask import request, redirect, session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import create_engine, func, or_


def authorization(web_session: session, req: request, param: parameters.WebParameters, ):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if 'username' in web_session:
                param.aaa_user, param.user_info = user_info(web_session['username'], param.engine)
                return function(*args, **kwargs)
            else:
                return redirect('/login')
        return wrapper
    return decorator


def login_access(username, password, ip, engine):
    with schema.db_select(engine) as db:
        try:
            aaa = db.query(schema.AAAUser).filter(schema.AAAUser.username == username).one()
            user = db.query(schema.User).filter(schema.User.login == aaa.uid).one()
            check_ip = db.query(schema.Parameter).filter(schema.Parameter.name == 'CHECK_IP').one()
        except NoResultFound:
            return False
        except MultipleResultsFound:
            return False

    if not aaa:
        return False

    if aaa.password != hashlib.md5(password.encode()).hexdigest():
        return False

    if not utils.check_ip(ip, user.ip) and check_ip.value == '1':
        return False

    if user.date_disable < datetime.datetime.now() or user.disable:
        return False

    with schema.db_select(engine) as db:
        auto_extension = db.query(schema.Parameter).filter(schema.Parameter.name == 'AUTO_EXTENSION').one()
        extension_days = db.query(schema.Parameter).filter(schema.Parameter.name == 'EXTENSION_DAYS').one()

    if auto_extension.value == '1' and user.date_disable < datetime.datetime.now() + datetime.timedelta(days=15):
        ex_days = int(extension_days.value)
        with schema.db_edit(engine) as db:
            db.query(schema.User).filter(schema.User.login == user.login). \
                update({schema.User.date_disable: datetime.datetime.now() + datetime.timedelta(days=ex_days)})

    return True


def check_ip_net(ip, network):
    return utils.check_ip_network(ip, network)


def get_access_request(engine, user):
    return []


def get_connection(engine, user):
    return []


def get_content_host(param: parameters.WebParameters, host_id):
    """
    Возвращает форматированную информацию о хосте.
    :param param: param: WebParameters
    :param host_id: schema.Host.id
    :return: dict
    """
    content = {}
    host = get_host(param, host_id)
    content['id'] = host_id
    content['proxy'] = host.proxy
    content['name'] = host.name
    content['ip'] = host.ip
    content['describe'] = host.describe
    content['ilo'] = host.ilo
    if access.check_access(param, 'ShowLogin', h_object=host) \
            or access.check_access(param, 'EditHostInformation', h_object=host)\
            or access.check_access(param, 'Administrate', h_object=host):
        content['default_login'] = host.default_login
        if host.default_login:
            content['default_login'] = host.default_login
        else:
            content['default_login'] = ''
    else:
        content['default_login'] = '*' * len(host.default_login)
    if access.check_access(param, 'ShowPassword', h_object=host) \
            or access.check_access(param, 'EditHostInformation', h_object=host) \
            or access.check_access(param, 'Administrate', h_object=host):
        if host.default_password:
            content['default_password'] = host.default_password
        else:
            content['default_password'] = ''
    else:
        content['default_password'] = '*' * len(host.default_password)
    content['tcp_port'] = host.tcp_port
    if not isinstance(host.note, dict) and host.note:
        content['note'] = json.loads(host.note)
    else:
        content['note'] = host.note

    with schema.db_select(param.engine) as db:
        content['services'] = db.query(schema.Service).filter(schema.Service.host == host_id).all()
        content['service_type'] = db.query(schema.ServiceType).all()

    with schema.db_select(param.engine) as db:
        content['connection_type'] = db.query(schema.ConnectionType).\
            filter(schema.ConnectionType.id == host.connection_type).one()
        content['file_transfer_type'] = db.query(schema.FileTransferType).\
            filter(schema.FileTransferType.id == host.file_transfer_type).one()
        try:
            content['parent'] = db.query(schema.Host).filter(schema.Host.id == host.parent).one().name
        except NoResultFound:
            content['parent'] = None
        try:
            content['ilo_type'] = db.query(schema.IloType).\
                filter(schema.IloType.id == host.ilo_type).one().name
        except NoResultFound:
            content['ilo_type'] = None

    return content


def get_admin_content_dashboard(param: parameters.WebParameters):
    """
    content - dict включает:
        access_request  - список запросов доступа.
        new_users       - новые пользователи
        connection      - список активных подключений
    :param param: WebParameters
    :return: dict
    """
    with schema.db_select(param.engine) as db:
        connection_count = db.query(schema.Connection).filter(schema.Connection.status == 1).count()
        storage_dir = db.query(schema.Parameter).filter(schema.Parameter.name == 'STORAGE_DIR').one()
    content = {'access_request': get_access_request(param.engine, param.user_info),
               'connection': get_connection(param.engine, param.user_info),
               'connection_count': connection_count,
               'la': os.getloadavg()[2],
               'free': psutil.virtual_memory().percent,
               'disk': psutil.disk_usage(storage_dir.value).percent}
    return content


def get_user_content_dashboard(param: parameters.WebParameters):
    """
    content - dict включает:
    :param param: WebParameters
    :return: dict
    """
    content = {}
    return content


def get_host(param: parameters.WebParameters, host_id=None, name=None,  parent=0):
    """
    Возвращает объект Host, поиск по schema.Host.id или schema.Host.name и schema.Host.parent
    :param host_id: schema.Host.id
    :param param: WebParameters
    :param name: schema.Host.name
    :param parent: schema.Host.parent
    :return: schema.Host
    """
    if host_id:
        with schema.db_select(param.engine) as db:
            try:
                host = db.query(schema.Host).filter(schema.Host.id == host_id, schema.Host.remove.is_(False)).one()
            except NoResultFound:
                return None
            except MultipleResultsFound:
                raise error.WTF("Дубли Host.id в таблице Host!!!")
        if host.default_password and len(host.default_password) > 0:
            host.default_password = utils.password(host.default_password, host.id, False)
        return host
    if name:
        with schema.db_select(param.engine) as db:
            try:
                host = db.query(schema.Host).filter(schema.Host.name == name,
                                                    schema.Host.parent == parent,
                                                    schema.Host.remove.is_(False)).one()
            except NoResultFound:
                return None
            except MultipleResultsFound:
                raise error.WTF("Дубли Host.name в таблице Host!!!")
        if host.default_password and len(host.default_password) > 0:
            host.default_password = utils.password(host.default_password, host.id, False)
        return host
    else:
        raise error.WTF("Ошибка работы weblib.get_host!!!")


def get_host_list(param: parameters.WebParameters, level=None):
    """
    Возвращает список хостов.
    :param level: вхождение директории
    :param param: WebParameters
    :return: list
    """
    with schema.db_select(param.engine) as db:
        host_list = db.query(schema.Host)\
            .filter(schema.Host.parent == level,
                    schema.Host.prefix == param.user_info.prefix,
                    schema.Host.remove.is_(False))\
            .order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
    return host_list


def get_service(param: parameters.WebParameters, host=None, service=None):
    """
    Запрос сервисов
    :param param: WebParameters
    :param host: Service.host
    :param service: Service.id
    :return: list Service or Service
    """
    if not host and not service:
        return None

    if host:
        with schema.db_select(param.engine) as db:
            s = db.query(schema.Service).filter(schema.Service.host == host).all()
    if service:
        with schema.db_select(param.engine) as db:
            s = db.query(schema.Service).filter(schema.Service.id == service).one()
    return s


def get_connection_type(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        connection_type = db.query(schema.ConnectionType).all()

    return [(t.id, t.name) for t in connection_type]


def get_file_transfer_type(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        file_transfer_type = db.query(schema.FileTransferType).all()

    return [(t.id, t.name) for t in file_transfer_type]


def get_ilo_type(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        ilo_type = db.query(schema.IloType).all()

    return [(t.id, t.name) for t in ilo_type]


def get_service_type(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        service_type = db.query(schema.ServiceType).all()

    return [(t.id, t.name) for t in service_type]


def get_local_port(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        local_port = db.query(schema.Service).all()
        ports = db.query(schema.Parameter).filter(schema.Parameter.name == 'FORWARD_TCP_PORT_RANGE').first()

    l = [t.local_port for t in local_port]
    for i in range(int(str(ports.value).split(';')[0]), int(str(ports.value).split(';')[1])):
        if i not in l:
            return i


def get_route_host(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        route_host = db.query(schema.Host).filter(schema.Host.proxy.is_(True)).all()

    return [(t.id, t.name) for t in route_host]


def get_routes(param: parameters.WebParameters, host_id):
    with schema.db_select(param.engine) as db:
        routes = db.query(schema.RouteMap, schema.Host).join(schema.Host, schema.Host.id == schema.RouteMap.route).\
            filter(schema.RouteMap.host == host_id).\
            order_by(schema.RouteMap.sequence).all()

    if len(routes) == 0:
        routes = None
    return routes


def get_group(param: parameters.WebParameters, group_id):
    content = {}
    with schema.db_select(param.engine) as db:
        try:
            group = db.query(schema.Group).filter(schema.Group.id == group_id).one()    # type: schema.Group
            content['group'] = group
        except NoResultFound:
            return False
        except MultipleResultsFound:
            raise error.WTF("Дубли Group.id в таблице Group!!!")

    if group.type == 0:
        with schema.db_select(param.engine) as db:
            users = db.query(schema.GroupUser, schema.User)\
                .join(schema.User, schema.GroupUser.user == schema.User.login)\
                .filter(schema.GroupUser.group == group_id).all()
            content['users'] = users

    if group.type == 1:
        with schema.db_select(param.engine) as db:
            hosts = db.query(schema.GroupHost, schema.Host)\
                .join(schema.Host, schema.GroupHost.host == schema.Host.id)\
                .filter(schema.GroupHost.group == group_id).all()
            content['hosts'] = hosts

    with schema.db_select(param.engine) as db:
        try:
            permission = db.query(schema.Permission).filter(
                schema.Permission.t_subject == 1,
                schema.Permission.subject == group_id,
                schema.Permission.object.is_(None)
            ).one()
            content['permission'] = permission
        except NoResultFound:
            content['permission'] = None
        except MultipleResultsFound:
            raise error.WTF("Дубли default Permission в таблице Permission!!!")
    return content


def get_group_user(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        group = db.query(schema.Group).filter(schema.Group.type == 0).all()

    if len(group) == 0:
        group = None
    return group


def get_group_host(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        group = db.query(schema.Group).filter(schema.Group.type == 1).all()

    if len(group) == 0:
        group = None
    return group


def get_users(param: parameters.WebParameters):
    content = {}
    with schema.db_select(param.engine) as db:
        users = db.query(schema.AAAUser, schema.User)\
            .join(schema.User, schema.AAAUser.uid == schema.User.login)\
            .order_by(schema.User.full_name).all()
        content['users'] = users
    return content


def get_user(param: parameters.WebParameters, uid):
    content = {}
    with schema.db_select(param.engine) as db:
        content['aaa_user'], content['user'] = db.query(schema.AAAUser, schema.User)\
            .join(schema.User, schema.AAAUser.uid == schema.User.login)\
            .order_by(schema.User.full_name)\
            .filter(schema.AAAUser.uid == uid)\
            .one()
        content['action'] = db.query(schema.Action)\
            .filter(schema.Action.user == uid)\
            .order_by(schema.Action.date.desc()).limit(10).all()
        content['connection'] = db.query(schema.Connection, schema.Host, schema.ConnectionType) \
            .join(schema.Host, schema.Host.id == schema.Connection.host) \
            .join(schema.ConnectionType, schema.ConnectionType.id == schema.Connection.connection_type) \
            .filter(schema.Connection.user == uid) \
            .order_by(schema.Connection.date_start.desc()).limit(10).all()
        group = db.query(schema.GroupUser, schema.Group)\
            .join(schema.Group, schema.Group.id == schema.GroupUser.group)\
            .filter(schema.GroupUser.user == uid).all()
        content['group'] = ", ".join([t.name for i, t in group])
    return content


def add_user_group(param: parameters.WebParameters, uid, gid):
    with schema.db_select(param.engine) as db:
        user_group = db.query(schema.GroupUser)\
            .filter(schema.GroupUser.user == uid, schema.GroupUser.group == gid).all()
        if len(user_group) > 0:
            return False
    with schema.db_edit(param.engine) as db:
        r = schema.GroupUser(
            user=uid,
            group=gid
        )
        db.add(r)
        db.flush()
        db.refresh(r)

        action = schema.Action(
            user=param.user_info.login,
            action_type=53,
            date=datetime.datetime.now(),
            message="Добавлена группа: {group.group} - user={group.user}({group})".format(group=r)
        )
        db.add(action)
        db.flush()
    return True


def set_group_permission(param: parameters.WebParameters, group_id, form: forms.ChangePermission):
    user_access = access.UserAccess(0)
    user_access.change('ShowHostInformation', set_access=form.ShowHostInformation.data)
    user_access.change('EditHostInformation', set_access=form.EditHostInformation.data)
    user_access.change('EditDirectory', set_access=form.EditDirectory.data)
    user_access.change('EditPrefixHost', set_access=form.EditPrefixHost.data)
    user_access.change('ShowLogin', set_access=form.ShowLogin.data)
    user_access.change('ShowPassword', set_access=form.ShowPassword.data)
    user_access.change('ShowAllSession', set_access=form.ShowAllSession.data)
    user_access.change('ShowAllGroupSession', set_access=form.ShowAllGroupSession.data)
    user_access.change('Administrate', set_access=form.Administrate.data)
    print(user_access)

    connection_access = access.ConnectionAccess(0)
    connection_access.change('Connection', set_access=form.Connection.data)
    connection_access.change('FileTransfer', set_access=form.FileTransfer.data)
    connection_access.change('ConnectionService', set_access=form.ConnectionService.data)
    connection_access.change('ConnectionOnlyService', set_access=form.ConnectionOnlyService.data)
    connection_access.change('ConnectionIlo', set_access=form.ConnectionIlo.data)
    print(connection_access)
    with schema.db_edit(param.engine) as db:
        try:
            perm = db.query(schema.Permission).filter(
                schema.Permission.t_subject == 1,
                schema.Permission.subject == group_id,
                schema.Permission.object.is_(None)
            ).one()
            perm.conn_access = connection_access.get_int()
            perm.user_access = user_access.get_int()
            db.flush()
        except NoResultFound:
            perm = schema.Permission(
                t_subject=1,
                subject=group_id,
                conn_access=connection_access.get_int(),
                user_access=user_access.get_int()
            )
            db.add(perm)
        except MultipleResultsFound:
            raise error.WTF("Дубли default Permission в таблице Permission!!!")


def search(param: parameters.WebParameters, query):
    """
    Возвращает список хостов подходящих под условие.
    :param param: WebParameters
    :param query: string
    :return: list
    """
    with schema.db_select(param.engine) as db:
        host_list = db.query(schema.Host)\
            .filter(or_(schema.Host.name.like("%" + query + "%"),
                        schema.Host.ilo == query,
                        schema.Host.ip == query,
                        schema.Host.describe.like("%" + query + "%"),
                        schema.Host.note.like("%" + query + "%")))\
            .filter(schema.Host.remove.is_(False))\
            .order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
    return host_list


def user_info(username, engine):
    with schema.db_select(engine) as db:
        try:
            aaa = db.query(schema.AAAUser).filter(schema.AAAUser.username == username).one()
            user = db.query(schema.User).filter(schema.User.login == aaa.uid).one()
        except NoResultFound:
            return False
        except MultipleResultsFound:
            return False

    return aaa, user


def restore_password(username, engine, request):
    with schema.db_select(engine) as db:
        user_id = db.query(schema.User.login).join(schema.AAAUser, schema.User.login == schema.AAAUser.uid). \
            filter(sqlalchemy.or_(schema.AAAUser.username == username, schema.User.email == username)).all()

    if len(user_id) != 1:
        return False

    # TODO: добавить отключение старых запросов.

    key = ''.join(random.choice(string.ascii_letters + string.punctuation + string.digits) for _ in range(256))
    key = hashlib.md5(key.encode()).hexdigest()
    user_id = user_id[0][0]

    with schema.db_edit(engine) as db:
        db.add(schema.RestorePassword(user=user_id,
                                      status=1,
                                      date=datetime.datetime.now(),
                                      key=key))
        db.add(schema.Action(user=user_id,
                             action_type=50,
                             date=datetime.datetime.now()))
    host = request.host_url
    email.send_mail(engine,
                    template.restore_password(),
                    user_id,
                    {
                        'username': 'Test User',
                        'url_recovery': '{0}{1}'.format(host, "restore/" + key),
                        'url_deny': '{0}{1}'.format(host, "restore/deny/" + key),
                        'user': user_id
                    })

    return True


def reset_password(key, engine, password=False, check=False):
    with schema.db_select(engine) as db:
        try:
            restore = db.query(schema.RestorePassword).filter(sqlalchemy.and_(schema.RestorePassword.key == key,
                                                                              schema.RestorePassword.status == 1)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return False

    if check and restore:
        return True

    with schema.db_select(engine) as db:
        try:
            aaa_user = db.query(schema.AAAUser).filter(schema.AAAUser.uid == restore.user).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return False

    with schema.db_edit(engine) as db:
        db.query(schema.RestorePassword). \
            filter(sqlalchemy.and_(schema.RestorePassword.key == key,
                                   schema.RestorePassword.status == 1)). \
            update({schema.RestorePassword.status: 2,
                    schema.RestorePassword.date_complete: datetime.datetime.now()})
        db.query(schema.AAAUser). \
            filter(schema.AAAUser.uid == restore.user). \
            update({schema.AAAUser.password: hashlib.md5(str(password).encode()).hexdigest()})
    email.send_mail(engine, template.restore_password_access(), aaa_user.uid, {'login': aaa_user.username})
    return True


def user_registration(reg_data, engine):
    with schema.db_edit(engine) as db:
        aaa = schema.AAAUser(username=reg_data['username'],
                             password=hashlib.md5(reg_data['password'].encode()).hexdigest())
        db.add(aaa)
        db.flush()
        db.refresh(aaa)
        user = schema.User(login=aaa.uid,
                           full_name=reg_data['full_name'],
                           date_create=datetime.datetime.now(),
                           disable=False,
                           date_disable=datetime.datetime.now() + datetime.timedelta(days=365),
                           ip=reg_data['ip'],
                           email=reg_data['email'],
                           check=0)
        db.add(user)
        db.flush()
    return True


def add_folder(param: parameters.WebParameters, folder):
    with schema.db_edit(param.engine) as db:
        folder = schema.Host(
            name=folder['name'],
            describe=folder['describe'],
            parent=folder['parent'],
            type=2,
            prefix=folder['prefix'],
            note=folder['note']
        )
        db.add(folder)
        db.flush()
        db.refresh(folder)
        action = schema.Action(
            user=param.user_info.login,
            action_type=10,
            date=datetime.datetime.now(),
            message="Создание директории: {folder.name} - id={folder.id}({folder})".format(folder=folder)
        )
        db.add(action)
        db.flush()

    return True


def add_host(param: parameters.WebParameters, host: schema.Host, parent=0, password=None):
    with schema.db_edit(param.engine) as db:
        host.prefix = param.user_info.prefix
        host.parent = parent
        db.add(host)
        db.flush()
        db.refresh(host)
        if password:
            host.default_password = utils.password(password, host.id, True)
        action = schema.Action(
            user=param.user_info.login,
            action_type=20,
            date=datetime.datetime.now(),
            message="Создание хоста: {host.name} - id={host.id}({host})".format(host=host)
        )
        db.add(action)
        db.flush()
        return True


def add_service(param: parameters.WebParameters, service: schema.Service):
    with schema.db_edit(param.engine) as db:
        db.add(service)
        db.flush()
        db.refresh(service)
        action = schema.Action(
            user=param.user_info.login,
            action_type=23,
            date=datetime.datetime.now(),
            message="Добавление сервиса: {service.host} - id={service.id}({service})".format(service=service)
        )
        db.add(action)
        db.flush()
        return True


def add_hosts_file(param: parameters.WebParameters, filepath: str, parent=0):
    if not os.path.isfile(filepath):
        raise error.WTF("Отсутсвует файл на загрузку")
    f = open(filepath, 'r')
    header = f.readline().strip().split(',')
    hosts = []
    for line in f:
        hosts.append(dict(zip(header, line.strip().split(','))))
    f.close()
    for h in hosts:
        password = None
        n_host = schema.Host()
        n_host.note = {}
        n_host.type = 1
        n_host.remove = False
        for i in h:
            if str(i).upper() == 'Name'.upper():
                n_host.name = h[i]
            elif str(i).upper() == 'IP'.upper():
                n_host.ip = h[i]
            elif str(i).upper() == 'Password'.upper():
                password = h[i]
            elif str(i).upper() == 'Login'.upper():
                n_host.default_login = h[i]
            elif str(i).upper() == 'IPMI'.upper():
                n_host.ilo = h[i]
            elif str(i).upper() == 'Protocol'.upper():
                with schema.db_select(param.engine) as db:
                    try:
                        n_host.connection_type = db.query(schema.ConnectionType).\
                            filter(func.upper(schema.ConnectionType.name) == func.upper(h[i])).one().id
                    except sqlalchemy.orm.exc.NoResultFound:
                        n_host.connection_type = None
            elif str(i).upper() == 'Vendor'.upper():
                with schema.db_select(param.engine) as db:
                    try:
                        n_host.ilo_type = db.query(schema.IloType).\
                            filter(func.upper(schema.IloType.vendor) == func.upper(h[i])).one().id
                    except sqlalchemy.orm.exc.NoResultFound:
                        n_host.ilo_type = None
            elif str(i).split(':')[0].upper() == 'Note'.upper():
                n_host.note[str(i).split(':')[1]] = h[i]
        n_host.note = json.dumps(n_host.note, ensure_ascii=False)
        if not n_host.connection_type:
            with schema.db_select(param.engine) as db:
                n_host.connection_type = db.query(schema.ConnectionType).\
                    order_by(schema.ConnectionType.id).first().id
        if not n_host.file_transfer_type:
            with schema.db_select(param.engine) as db:
                n_host.file_transfer_type = db.query(schema.FileTransferType).\
                    order_by(schema.FileTransferType.id).first().id
        if not n_host.ilo_type:
            with schema.db_select(param.engine) as db:
                n_host.ilo_type = db.query(schema.IloType).\
                    order_by(schema.IloType.id).first().id
        add_host(param, n_host, password=password, parent=parent)
        del n_host
    return True


def add_route(param: parameters.WebParameters, r):
    with schema.db_edit(param.engine) as db:
        routes = db.query(schema.RouteMap).filter(schema.RouteMap.host == r['host']).all()

        route = schema.RouteMap(
            sequence=len(routes)+1,
            host=r['host'],
            route=r['route']
        )
        db.add(route)
        db.flush()
        db.refresh(route)

        action = schema.Action(
            user=param.user_info.login,
            action_type=25,
            date=datetime.datetime.now(),
            message="Добавлен маршрут: {route.host} - id={route.id}({route})".format(route=route)
        )
        db.add(action)
        db.flush()
    return True


def add_group(param: parameters.WebParameters, g):
    with schema.db_edit(param.engine) as db:
        group = schema.Group(
            name=g['name'],
            type=g['type']
        )
        db.add(group)
        db.flush()
        db.refresh(group)

        action = schema.Action(
            user=param.user_info.login,
            action_type=52,
            date=datetime.datetime.now(),
            message="Добавлена группа: {group.name} - id={group.id}({group})".format(group=group)
        )
        db.add(action)
        db.flush()
    return True


def edit_folder(param: parameters.WebParameters, folder, folder_id):
    with schema.db_edit(param.engine) as db:
        host = db.query(schema.Host).filter(schema.Host.id == folder_id).one()
        host.name = folder['name']
        host.describe = folder['describe']
        host.note = folder['note']

        action = schema.Action(
            user=param.user_info.login,
            action_type=11,
            date=datetime.datetime.now(),
            message="Редактирование директории: {folder.name} - id={folder.id}({folder})".format(folder=host)
        )
        db.add(action)
        db.flush()

    return True


def edit_host(param: parameters.WebParameters, d, host_id):
    with schema.db_edit(param.engine) as db:
        host = db.query(schema.Host).filter(schema.Host.id == host_id).one()
        host.name = d['name']
        host.ip = d['ip']
        host.connection_type = d['connection_type']
        host.file_transfer_type = d['file_transfer_type']
        host.describe = d['describe']
        host.ilo = d['ilo']
        host.ilo_type = d['ilo_type']
        host.default_login = d['default_login']
        host.tcp_port = d['port']
        host.note = d['note']
        host.proxy = d['proxy']

        action = schema.Action(
            user=param.user_info.login,
            action_type=21,
            date=datetime.datetime.now(),
            message="Редактирование хоста: {folder.name} - id={folder.id}({folder})".format(folder=host)
        )
        db.add(action)
        db.flush()

    return True


def delete_folder(param: parameters.WebParameters, host_id):
    with schema.db_edit(param.engine) as db:
        d_host = db.query(schema.Host).filter(schema.Host.id == host_id).one()
        d_host.remove = True
        action = schema.Action(
            user=param.user_info.login,
            action_type=12,
            date=datetime.datetime.now(),
            message="Удаление директории: {folder.name} - id={folder.id}".format(folder=d_host)
        )
        db.add(action)
        db.flush()

    return True


def delete_host(param: parameters.WebParameters, host_id):
    with schema.db_edit(param.engine) as db:
        d_host = db.query(schema.Host).filter(schema.Host.id == host_id).one()
        d_host.remove = True
        action = schema.Action(
            user=param.user_info.login,
            action_type=22,
            date=datetime.datetime.now(),
            message="Удаление хоста: {folder.name} - id={folder.id}".format(folder=d_host)
        )
        db.add(action)
        db.flush()

    return True


def del_group(param: parameters.WebParameters, group=None):
    """
    Удаление групп
    :param param: WebParameters
    :param group: schema.Group.id
    :return: True
    """
    with schema.db_edit(param.engine) as db:
        db.query(schema.Group).filter(schema.Group.id == group).delete()
        action = schema.Action(
            user=param.user_info.login,
            action_type=24,
            date=datetime.datetime.now(),
            message="Удаление группы: id={}".format(group)
        )
        db.add(action)
        db.flush()

    return True


def del_service(param: parameters.WebParameters, host=None, service=None):
    """
        Удаление сервисов
        :param param: WebParameters
        :param host: Service.host
        :param service: Service.id
        :return: true or false
        """
    if not host and not service:
        return False

    if host:
        with schema.db_edit(param.engine) as db:
            db.query(schema.Service).filter(schema.Service.host == host).delete()
            action = schema.Action(
                user=param.user_info.login,
                action_type=24,
                date=datetime.datetime.now(),
                message="Удаление сервиса: host={}".format(host)
            )
            db.add(action)
            db.flush()
    if service:
        with schema.db_edit(param.engine) as db:
            db.query(schema.Service).filter(schema.Service.id == service).delete()
            action = schema.Action(
                user=param.user_info.login,
                action_type=24,
                date=datetime.datetime.now(),
                message="Удаление сервиса: id={}".format(service)
            )
            db.add(action)
            db.flush()
    return True


def clear_routes(param: parameters.WebParameters, host_id):
    with schema.db_edit(param.engine) as db:
        db.query(schema.RouteMap).filter(schema.RouteMap.host == host_id).delete()
        action = schema.Action(
            user=param.user_info.login,
            action_type=26,
            date=datetime.datetime.now(),
            message="Очистка маршрутов: host={}".format(host_id)
        )
        db.add(action)
        db.flush()

    return True


if __name__ == '__main__':
    e = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format('postgresql',
                                                         'acs',
                                                         'acs',
                                                         'localhost',
                                                         '5432',
                                                         'acs'
                                                         ))
    pass
