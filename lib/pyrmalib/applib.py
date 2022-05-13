# -*- coding: utf-8 -*-
# encoding: utf-8
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

import json
import psutil
import os
import random
import pam

from sqlalchemy.orm import aliased

from pyrmalib import schema, utils, mail, template, parameters, error, access, forms
from functools import wraps
import hashlib
import sqlalchemy
import datetime
import string
from flask import request, redirect, session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import create_engine, func, or_, and_, sql


def authorization(web_session: session, req: request, param: parameters.WebParameters, ):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if 'username' in web_session:
                param.user_info = user_info(web_session['username'], param.engine)
                return function(*args, **kwargs)
            else:
                return redirect('/login')

        return wrapper

    return decorator


def login_access(username, password, ip, engine):
    if not pam.authenticate(username=username, password=password):
        return False

    with schema.db_select(engine) as db:
        try:
            user = db.query(schema.User).filter(schema.User.login == username).one()
            check_ip = db.query(schema.Parameter).filter(schema.Parameter.name == 'CHECK_IP').one()
        except NoResultFound:
            return False
        except MultipleResultsFound:
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


def change_ipmi(param: parameters.WebParameters, ipmi_id, data):
    with schema.db_edit(param.engine) as db:
        try:
            ipmi = db.query(schema.IPMIType).filter(schema.IPMIType.id == ipmi_id).one()
        except NoResultFound:
            raise error.WTF('Данные не найдены')
        except MultipleResultsFound:
            raise error.WTF('Данные не найдены')
        ipmi.name = data['name']
        ipmi.vendor = data['vendor']
        ipmi.ports = data['ports']
        db.flush()
        db.refresh(ipmi)

        action = schema.Action(
            user=param.user_info.uid,
            action_type=6,
            date=datetime.datetime.now(),
            message="Изменение IPMI{ipmi}".format(ipmi=ipmi)
        )
        db.add(action)
        db.flush()


def check_host(param: parameters.WebParameters, hid):
    with schema.db_select(param.engine) as db:
        try:
            host = db.query(schema.Host).filter(schema.Host.id == hid).one()
        except NoResultFound:
            raise error.WTF('Данные не найдены')
        except MultipleResultsFound:
            raise error.WTF('Данные не найдены')

        if host.type == 1:
            return True
        else:
            return False


def get_access_list(param: parameters.WebParameters):
    """
    select
        al.id as id,
        al.date_disable as date_disable,
        al.note as note,
        gu."name" as subject,
        gu.id as subject_id,
        al.t_subject as t_subject,
        gh."name" as "object",
        gh.id as object_id,
        al.t_object as t_object
    from access_list al
    left join "group" as gu on al.subject = gu.id
    left join "group" as gh on al.object = gh.id
    where t_subject = 1 and t_object = 1
    UNION
    select
        al.id as id,
        al.date_disable as date_disable,
        al.note as note,
        gu.full_name as subject,
        gu.uid as subject_id,
        al.t_subject as t_subject,
        gh."name" as "object",
        gh.id as object_id,
        al.t_object as t_object
    from access_list al
    left join "user" as gu on al.subject = gu.uid
    left join host as gh on al.object = gh.id
    where t_subject = 0 and t_object = 0;
    """
    with schema.db_select(param.engine) as db:
        group_user = aliased(schema.Group)
        group_host = aliased(schema.Group)
        group_access = db.query(
            schema.AccessList.id,
            schema.AccessList.date_disable,
            schema.AccessList.note,
            group_user.name,
            group_user.id,
            schema.AccessList.t_subject,
            group_host.name,
            group_host.id,
            schema.AccessList.t_object
        ). \
            join(group_user, schema.AccessList.subject == group_user.id). \
            join(group_host, schema.AccessList.object == group_host.id). \
            filter(schema.AccessList.t_object == 1, schema.AccessList.t_subject == 1, schema.AccessList.status != 2)
        user_access = db.query(
            schema.AccessList.id,
            schema.AccessList.date_disable,
            schema.AccessList.note,
            schema.User.full_name,
            schema.User.uid,
            schema.AccessList.t_subject,
            schema.Host.name,
            schema.Host.id,
            schema.AccessList.t_object
        ). \
            join(schema.User, schema.AccessList.subject == schema.User.uid). \
            join(schema.Host, schema.AccessList.object == schema.Host.id). \
            filter(schema.AccessList.t_object == 0, schema.AccessList.t_subject == 0, schema.AccessList.status != 2)
        access_list = group_access.union(user_access).all()

    return access_list


def get_access_request(param: parameters.WebParameters, acc_id=None):
    result = []
    if acc_id:
        with schema.db_select(param.engine) as db:
            access_list = db.query(schema.Host, schema.User, schema.RequestAccess).filter(
                schema.RequestAccess.host == schema.Host.id,
                schema.RequestAccess.user == schema.User.uid,
                schema.RequestAccess.id == acc_id
            ).all()
    else:
        with schema.db_select(param.engine) as db:
            access_list = db.query(schema.Host, schema.User, schema.RequestAccess).filter(
                schema.RequestAccess.host == schema.Host.id,
                schema.RequestAccess.user == schema.User.uid,
                schema.RequestAccess.status == 0,
                schema.RequestAccess.date_access > datetime.datetime.now()
            ).all()

    for host, user, acc in access_list:
        if access.check_access(param, 'AccessRequest', h_object=host) or access.check_access(param, 'Administrate'):
            result.append(
                {
                    'user': user,
                    'host': host,
                    'access': acc
                }
            )

    return result


def get_connection(param: parameters.WebParameters):
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
    content['group'] = ", ".join([t.name for i, t in get_group_list(param, host=host_id)])
    content['parent_group'] = ", ".join([t.name for i, t in get_group_list(param, host=host.parent)])
    if access.check_access(param, 'ShowLogin', h_object=host) \
            or access.check_access(param, 'Administrate', h_object=host):
        content['default_login'] = host.default_login
        if host.default_login:
            content['default_login'] = host.default_login
        else:
            content['default_login'] = ''
    else:
        content['default_login'] = '*' * len(host.default_login)
    if access.check_access(param, 'ShowPassword', h_object=host) \
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
        try:
            content['connection_type'] = db.query(schema.ConnectionType). \
                filter(schema.ConnectionType.id == host.connection_type).one()
        except NoResultFound:
            raise error.WTF('Не указан тип подклчюения')
        try:
            content['file_transfer_type'] = db.query(schema.FileTransferType). \
                filter(schema.FileTransferType.id == host.file_transfer_type).one()
        except NoResultFound:
            content['file_transfer_type'] = None
        try:
            content['parent'] = db.query(schema.Host).filter(schema.Host.id == host.parent).one().name
        except NoResultFound:
            content['parent'] = None
        try:
            content['ilo_type'] = db.query(schema.IPMIType). \
                filter(schema.IPMIType.id == host.ilo_type).one().name
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
    content = {
        'access_request': get_access_request(param),
        'connection': get_connection(param),
        'connection_count': connection_count,
        'la': os.getloadavg()[2],
        'free': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage(param.data_dir).percent,
        'new_user': get_new_user(param)
    }
    return content


def get_user_content_dashboard(param: parameters.WebParameters):
    """
    content - dict включает:
    :param param: WebParameters
    :return: dict
    """
    content = {
        'access_request': get_access_request(param),
    }
    return content


def get_host(param: parameters.WebParameters, host_id=None, name=None, parent=0):
    """
    Возвращает объект Host, поиск по schema.Host.id или schema.Host.name и schema.Host.parent
    :param host_id: schema.Host.id
    :param param: WebParameters
    :param name: schema.Host.name
    :param parent: schema.Host.parent
    :return: type: schema.Host
    """
    if host_id or host_id == int(0):
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
        host_list = db.query(schema.Host) \
            .filter(schema.Host.parent == level,
                    schema.Host.prefix == param.user_info.prefix,
                    schema.Host.remove.is_(False)) \
            .order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
    return host_list


def get_service(param: parameters.Parameters, host=None, service=None):
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


def get_connection_type(param: parameters.Parameters):
    with schema.db_select(param.engine) as db:
        connection_type = db.query(schema.ConnectionType).all()

    return [(t.id, t.name) for t in connection_type]


def get_file_transfer_type(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        file_transfer_type = db.query(schema.FileTransferType).all()

    return [(None, 'Нет')] + [(t.id, t.name) for t in file_transfer_type]


def get_ilo_type(param: parameters.WebParameters, ipmi_id=None, raw=False):
    with schema.db_select(param.engine) as db:
        if ipmi_id:
            ilo_type = db.query(schema.IPMIType).filter(schema.IPMIType.id == ipmi_id).one()
        else:
            ilo_type = db.query(schema.IPMIType).all()

    if raw or ipmi_id:
        return ilo_type
    else:
        return [(None, 'Нет')] + [(t.id, t.name) for t in ilo_type]


def get_service_type(param: parameters.Parameters, service_type_id=None, raw=False):
    with schema.db_select(param.engine) as db:
        if service_type_id:
            service_type = db.query(schema.ServiceType).filter(schema.ServiceType.id == service_type_id).one()
        else:
            service_type = db.query(schema.ServiceType).all()

    if raw or service_type_id:
        return service_type
    else:
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
        routes = db.query(schema.RouteMap, schema.Host).join(schema.Host, schema.Host.id == schema.RouteMap.route). \
            filter(schema.RouteMap.host == host_id). \
            order_by(schema.RouteMap.sequence).all()

    if len(routes) == 0:
        routes = None
    return routes


def get_group(param: parameters.WebParameters, group_id):
    content = {}
    with schema.db_select(param.engine) as db:
        try:
            group = db.query(schema.Group).filter(schema.Group.id == group_id).one()  # type: schema.Group
            content['group'] = group
        except NoResultFound:
            return False
        except MultipleResultsFound:
            raise error.WTF("Дубли Group.id в таблице Group!!!")

    if group.type == 0:
        with schema.db_select(param.engine) as db:
            users = db.query(schema.GroupUser, schema.User) \
                .join(schema.User, schema.GroupUser.user == schema.User.uid) \
                .filter(schema.GroupUser.group == group_id).all()
            content['users'] = users

    if group.type == 1:
        with schema.db_select(param.engine) as db:
            hosts = db.query(schema.GroupHost, schema.Host) \
                .join(schema.Host, schema.GroupHost.host == schema.Host.id) \
                .filter(schema.GroupHost.group == group_id).all()
            content['hosts'] = hosts

    with schema.db_select(param.engine) as db:
        try:
            permission = db.query(schema.Permission).filter(
                schema.Permission.t_subject == 1,
                schema.Permission.subject == group_id
            ).one()
            content['permission'] = permission
        except NoResultFound:
            content['permission'] = None
        except MultipleResultsFound:
            raise error.WTF("Дубли default Permission в таблице Permission!!!")
    return content


def get_group_user(param: parameters.Parameters):
    with schema.db_select(param.engine) as db:
        group = db.query(schema.Group).filter(schema.Group.type == 0, schema.Group.id != 0).all()

    if len(group) == 0:
        group = None
    return group


def get_group_host(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        group = db.query(schema.Group).filter(schema.Group.type == 1, schema.Group.id != 0).all()

    if len(group) == 0:
        group = None
    return group


def get_group_list(param: parameters.Parameters, host=False, user=False):
    if host:
        with schema.db_select(param.engine) as db:
            group = db.query(schema.GroupHost, schema.Group) \
                .join(schema.Group, schema.Group.id == schema.GroupHost.group) \
                .filter(schema.GroupHost.host == host).all()
    elif user:
        with schema.db_select(param.engine) as db:
            group = db.query(schema.GroupUser, schema.Group) \
                .join(schema.Group, schema.Group.id == schema.GroupUser.group) \
                .filter(schema.GroupUser.user == user).all()
    else:
        group = []
    return group


def get_users(param: parameters.WebParameters):
    content = {}
    with schema.db_select(param.engine) as db:
        users = db.query(schema.User) \
            .order_by(schema.User.full_name).all()
        content['users'] = users
    return content


def get_parameters(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        p = db.query(schema.Parameter).all()

    return p


def get_user(param: parameters.Parameters, uid):
    content = {}
    with schema.db_select(param.engine) as db:
        content['user'] = db.query(schema.User) \
            .order_by(schema.User.full_name) \
            .filter(schema.User.uid == uid) \
            .one()
        content['action'] = db.query(schema.Action) \
            .filter(schema.Action.user == uid) \
            .order_by(schema.Action.date.desc()).limit(10).all()
        content['connection'] = db.query(schema.Connection, schema.Host, schema.ConnectionType) \
            .join(schema.Host, schema.Host.id == schema.Connection.host) \
            .join(schema.ConnectionType, schema.ConnectionType.id == schema.Connection.connection_type) \
            .filter(schema.Connection.user == uid) \
            .order_by(schema.Connection.date_start.desc()).limit(10).all()
    content['group'] = ", ".join([t.name for i, t in get_group_list(param, user=uid)])
    return content


def get_user_group(param: parameters.Parameters, uid):
    with schema.db_select(param.engine) as db:
        group = db.query(schema.GroupUser).filter(schema.GroupUser.user == uid).all()
    return [t.group for t in group]


def get_user_access(param: parameters.Parameters, uid, hid=None):
    with schema.db_select(param.engine) as db:
        if hid:
            try:
                user_access = db.query(schema.AccessList).filter(
                    schema.AccessList.status == 1,
                    schema.AccessList.t_subject == 0,
                    schema.AccessList.subject == uid,
                    schema.AccessList.t_object == 0,
                    schema.AccessList.object == hid,
                    schema.AccessList.date_disable > datetime.datetime.now(),
                    schema.AccessList.status != 2
                ).one()
            except NoResultFound:
                return None
            except MultipleResultsFound:
                raise error.WTF('Дубли в аксес листах!!!')
        else:
            user_access = db.query(schema.AccessList).filter(
                schema.AccessList.status == 1,
                schema.AccessList.t_subject == 0,
                schema.AccessList.subject == uid,
                schema.AccessList.date_disable > datetime.datetime.now(),
                schema.AccessList.status != 2
            ).all()
            if len(user_access) == 0:
                return None
    return user_access


def get_group_access(param: parameters.Parameters, u_gid: list, h_gid: list):
    with schema.db_select(param.engine) as db:
        group_access = db.query(schema.AccessList).filter(
            schema.AccessList.date_disable > datetime.datetime.now(),
            schema.AccessList.status == 1,
            schema.AccessList.t_object == 1,
            schema.AccessList.t_subject == 1,
            schema.AccessList.subject.in_(u_gid),
            schema.AccessList.object.in_(h_gid),
            schema.AccessList.status != 2
        ).all()

    if len(group_access) == 0:
        return None
    return group_access


def get_user_permission(app_param: parameters.Parameters, subj):
    # select p.* from "permission" p
    # where
    #   (p.subject = subj and p.t_subject = 0)
    #   or (p.subject in (select gu."group" from group_user gu where gu."user" = subj) and p.t_subject = 1);
    with schema.db_select(app_param.engine) as db:
        user_groups = db.query(schema.GroupUser.group) \
            .filter(schema.GroupUser.user == subj) \
            .group_by(schema.GroupUser.group).subquery()

        permission = db.query(schema.Permission) \
            .filter(or_(
            and_(schema.Permission.subject == subj, schema.Permission.t_subject == 0),
            and_(schema.Permission.subject.in_(user_groups), schema.Permission.t_subject == 1)
        )
        ).all()
    if len(permission) == 0:
        return None

    return permission


def get_group_permission(app_param: parameters.Parameters, group: list):
    with schema.db_select(app_param.engine) as db:
        permission = db.query(schema.Permission).filter(
            schema.Permission.t_subject == 1,
            schema.Permission.subject.in_(group)
        ).all()

    if len(permission) == 0:
        return None

    return permission


def get_host_group(param: parameters.Parameters, hid):
    h_list = [hid]
    while True:
        parent = get_parent_host(param, h_list[-1])
        if parent == 0:
            break
        else:
            h_list.append(parent)

    with schema.db_select(param.engine) as db:
        group = db.query(schema.GroupHost).filter(schema.GroupHost.host.in_(h_list)).all()

    return [t.group for t in group]


def get_parent_host(param: parameters.Parameters, hid):
    with schema.db_select(param.engine) as db:
        host = db.query(schema.Host).filter(schema.Host.id == hid).one()
    return host.parent


def get_action(param: parameters.WebParameters, uid, date):
    date_start = date
    date_stop = date + datetime.timedelta(days=1)
    if uid == 0:
        with schema.db_select(param.engine) as db:
            actions = db.query(schema.Action, schema.ActionType, schema.User) \
                .join(schema.ActionType, schema.Action.action_type == schema.ActionType.id) \
                .join(schema.User, schema.Action.user == schema.User.uid) \
                .filter(and_(schema.Action.date >= utils.date_to_datetime(date_start),
                             schema.Action.date < utils.date_to_datetime(date_stop))) \
                .order_by(schema.Action.date.desc()).all()
    else:
        with schema.db_select(param.engine) as db:
            actions = db.query(schema.Action, schema.ActionType, schema.User) \
                .join(schema.ActionType, schema.Action.action_type == schema.ActionType.id) \
                .join(schema.User, schema.Action.user == schema.User.uid) \
                .filter(and_(schema.Action.date >= utils.date_to_datetime(date_start),
                             schema.Action.date < utils.date_to_datetime(date_stop),
                             schema.Action.user == uid)) \
                .order_by(schema.Action.date.desc()).all()
    return actions


def get_prefix(param: parameters.WebParameters, prefix_id=None):
    with schema.db_select(param.engine) as db:
        if prefix_id:
            prefix = db.query(schema.Prefix).filter(schema.Prefix.id == prefix_id).one()
        else:
            prefix = db.query(schema.Prefix).order_by(schema.Prefix.name).all()
    return prefix


def get_new_user(param: parameters.WebParameters):
    with schema.db_select(param.engine) as db:
        user = db.query(schema.User).filter(schema.User.check == 0).all()
    return user


def add_user_group(param: parameters.Parameters, uid: int, gid: int, action: bool=True):
    with schema.db_select(param.engine) as db:
        user_group = db.query(schema.GroupUser) \
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

        if action:
            action = schema.Action(
                user=param.user_info.uid,
                action_type=53,
                date=datetime.datetime.now(),
                message="Добавлена группа: {group.group} - user={group.user}({group})".format(group=r)
            )
            db.add(action)
            db.flush()
    return True


def add_host_group(param: parameters.WebParameters, host_id, gid):
    with schema.db_select(param.engine) as db:
        user_group = db.query(schema.GroupUser) \
            .filter(schema.GroupHost.host == host_id, schema.GroupHost.group == gid).all()
        if len(user_group) > 0:
            return False
    with schema.db_edit(param.engine) as db:
        r = schema.GroupHost(
            host=host_id,
            group=gid
        )
        db.add(r)
        db.flush()
        db.refresh(r)

        action = schema.Action(
            user=param.user_info.uid,
            action_type=54,
            date=datetime.datetime.now(),
            message="Добавлена группа: {group.group} - host={group.host}({group})".format(group=r)
        )
        db.add(action)
        db.flush()
    return True


def add_prefix(param: parameters.WebParameters, name, describe):
    with schema.db_edit(param.engine) as db:
        p = schema.Prefix(
            name=name,
            note=describe
        )
        db.add(p)
        db.flush()
        db.refresh(p)

        action = schema.Action(
            user=param.user_info.uid,
            action_type=3,
            date=datetime.datetime.now(),
            message="Добавлен префикс ({prefix})".format(prefix=p)
        )
        db.add(action)
        db.flush()
    return True


def add_ipmi(param: parameters.WebParameters, name, vendor, ports):
    with schema.db_edit(param.engine) as db:
        i = schema.IPMIType(
            name=name,
            vendor=vendor,
            ports=ports
        )
        db.add(i)
        db.flush()
        db.refresh(i)

        action = schema.Action(
            user=param.user_info.uid,
            action_type=5,
            date=datetime.datetime.now(),
            message="Добавлен IPMI ({ipmi})".format(ipmi=i)
        )
        db.add(action)
        db.flush()
    return True


def set_user_permission(param: parameters.WebParameters, user_access: int, connection_access: int, uid: int):
    user_access = access.UserAccess(user_access)
    connection_access = access.ConnectionAccess(connection_access)
    with schema.db_edit(param.engine) as db:
        try:
            perm = db.query(schema.Permission).filter(
                schema.Permission.t_subject == 0,
                schema.Permission.subject == uid
            ).one()
            perm.conn_access = connection_access.get_int()
            perm.user_access = user_access.get_int()
            db.flush()
        except NoResultFound:
            perm = schema.Permission(
                t_subject=0,
                subject=uid,
                conn_access=connection_access.get_int(),
                user_access=user_access.get_int()
            )
            db.add(perm)
        except MultipleResultsFound:
            raise error.WTF("Дубли default Permission в таблице Permission!!!")


def set_group_permission(param: parameters.WebParameters, group_id, form: forms.ChangePermission):
    user_access = access.UserAccess(0)
    user_access.change('ShowHostInformation', set_access=form.ShowHostInformation.data)
    user_access.change('EditHostInformation', set_access=form.EditHostInformation.data)
    user_access.change('EditDirectory', set_access=form.EditDirectory.data)
    user_access.change('EditPrefixHost', set_access=form.EditPrefixHost.data)
    user_access.change('ShowLogin', set_access=form.ShowLogin.data)
    user_access.change('ShowPassword', set_access=form.ShowPassword.data)
    user_access.change('ShowAllSession', set_access=form.ShowAllSession.data)
    user_access.change('AccessRequest', set_access=form.AccessRequest.data)
    user_access.change('Administrate', set_access=form.Administrate.data)

    connection_access = access.ConnectionAccess(0)
    connection_access.change('Connection', set_access=form.Connection.data)
    connection_access.change('FileTransfer', set_access=form.FileTransfer.data)
    connection_access.change('ConnectionService', set_access=form.ConnectionService.data)
    connection_access.change('ConnectionOnlyService', set_access=form.ConnectionOnlyService.data)
    connection_access.change('ConnectionIlo', set_access=form.ConnectionIlo.data)
    with schema.db_edit(param.engine) as db:
        try:
            perm = db.query(schema.Permission).filter(
                schema.Permission.t_subject == 1,
                schema.Permission.subject == group_id
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

        action = schema.Action(
            user=param.user_info.uid,
            action_type=61,
            date=datetime.datetime.now(),
            message="Смена прав доступа для группы {group_id}({user_access}, {connection_access})".format(
                group_id=group_id,
                user_access=user_access.get_int(),
                connection_access=connection_access.get_int()
            )
        )
        db.add(action)
        db.flush()


def set_user_prefix(param: parameters.WebParameters, prefix, uid):
    with schema.db_edit(param.engine) as db:
        user = db.query(schema.User).filter(schema.User.uid == uid).one()
        user.prefix = prefix
        db.flush()
        db.refresh(user)
        action = schema.Action(
            user=param.user_info.uid,
            action_type=60,
            date=datetime.datetime.now(),
            message="Смена префикса пользователя - {user.full_name}({user.prefix})".format(user=user)
        )
        db.add(action)
        db.flush()

    return True


def set_parameters(param: parameters.WebParameters, name: str, value: str):
    with schema.db_edit(param.engine) as db:
        p = db.query(schema.Parameter).filter(schema.Parameter.name == name).one()
        if value != p.value:
            p.value = value
            db.flush()
            db.refresh(p)

            action = schema.Action(
                user=param.user_info.uid,
                action_type=2,
                date=datetime.datetime.now(),
                message="Изменение параметров - {param}".format(param=p)
            )
            db.add(action)
            db.flush()

    return True


def search(param: parameters.Parameters, query):
    """
    Возвращает список хостов подходящих под условие.
    :param param: WebParameters
    :param query: string
    :return: list
    """
    with schema.db_select(param.engine) as db:
        host_list = db.query(schema.Host) \
            .filter(or_(schema.Host.name.like("%" + query + "%"),
                        schema.Host.ilo == query,
                        schema.Host.ip == query,
                        schema.Host.describe.like("%" + query + "%"),
                        schema.Host.note.like("%" + query + "%"))) \
            .filter(schema.Host.remove.is_(False),
                    schema.Host.prefix == param.user_info.prefix) \
            .order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
    return host_list


def user_info(username, engine):
    with schema.db_select(engine) as db:
        try:
            user = db.query(schema.User).filter(schema.User.login == username).one()
        except NoResultFound:
            return False
        except MultipleResultsFound:
            return False

    return user


def user_disable(param: parameters.WebParameters, uid, disable=False, enable=False):
    """
    Включение/Отключение учетных записей.
    :param param:   WebParameters
    :param uid: User ID
    :param disable: if True - Disable user
    :param enable: if True - Enable user
    :return: True
    """
    with schema.db_edit(param.engine) as db:
        user = db.query(schema.User).filter(schema.User.uid == uid).one()
        if disable:
            user.disable = True
            user.date_disable = datetime.datetime.now()
            user.check = 1
            status = 'Отключение'
            status_id = 57
            db.flush()
        if enable:
            user.disable = False
            user.date_disable = datetime.datetime.now() + datetime.timedelta(days=365)
            user.check = 1
            status = 'Включение'
            status_id = 58
            db.flush()

        action = schema.Action(
            user=param.user_info.uid,
            action_type=status_id,
            date=datetime.datetime.now(),
            message="{} пользователя: {user.full_name}({user})".format(status, user=user)
        )
        db.add(action)
        db.flush()

    return True


def restore_deny_password(param: parameters.WebParameters, key):
    with schema.db_select(param.engine) as db:
        try:
            db.query(schema.RestorePassword).filter(
                sqlalchemy.and_(schema.RestorePassword.key == key, schema.RestorePassword.status == 1)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return False

    with schema.db_edit(param.engine) as db:
        db.query(schema.RestorePassword). \
            filter(schema.RestorePassword.status == 1, schema.RestorePassword.key == key). \
            update({schema.RestorePassword.status: 0, schema.RestorePassword.date_complete: datetime.datetime.now()})
        db.add(
            schema.Action(
                user=param.user_info.uid if param.user_info else sql.null(),
                action_type=50,
                date=datetime.datetime.now(),
                message='Восстановение пароля отменено (Client IP: {})'.format(request.remote_addr)
            )
        )
    return True


def user_registration(reg_data, param: parameters.Parameters):
    with schema.db_edit(param.engine) as db:
        user = schema.User(
            uid=reg_data['uid'],
            login=reg_data['login'],
            full_name=reg_data['full_name'],
            date_create=datetime.datetime.now(),
            disable=False,
            date_disable=datetime.datetime.now() + datetime.timedelta(days=365),
            ip=reg_data['ip'],
            email=reg_data['email'],
            check=reg_data['check']
        )
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
            user=param.user_info.uid,
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
            user=param.user_info.uid,
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
            user=param.user_info.uid,
            action_type=23,
            date=datetime.datetime.now(),
            message="Добавление сервиса: {service.host} - id={service.id}({service})".format(service=service)
        )
        db.add(action)
        db.flush()
        return True


def add_service_type(param: parameters.WebParameters, name, default_port):
    with schema.db_edit(param.engine) as db:
        service_type = schema.ServiceType(
            name=name,
            default_port=default_port
        )
        db.add(service_type)
        db.flush()
        db.refresh(service_type)
        action = schema.Action(
            user=param.user_info.uid,
            action_type=8,
            date=datetime.datetime.now(),
            message="Добавление сервиса: id={service.id}({service})".format(service=service_type)
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
                        n_host.connection_type = db.query(schema.ConnectionType). \
                            filter(func.upper(schema.ConnectionType.name) == func.upper(h[i])).one().id
                    except sqlalchemy.orm.exc.NoResultFound:
                        n_host.connection_type = None
            elif str(i).upper() == 'Vendor'.upper():
                with schema.db_select(param.engine) as db:
                    try:
                        n_host.ilo_type = db.query(schema.IPMIType). \
                            filter(func.upper(schema.IPMIType.vendor) == func.upper(h[i])).one().id
                    except sqlalchemy.orm.exc.NoResultFound:
                        n_host.ilo_type = None
            elif str(i).split(':')[0].upper() == 'Note'.upper():
                n_host.note[str(i).split(':')[1]] = h[i]
        n_host.note = json.dumps(n_host.note, ensure_ascii=False)
        if not n_host.connection_type:
            with schema.db_select(param.engine) as db:
                n_host.connection_type = db.query(schema.ConnectionType). \
                    order_by(schema.ConnectionType.id).first().id
        if not n_host.file_transfer_type:
            with schema.db_select(param.engine) as db:
                n_host.file_transfer_type = db.query(schema.FileTransferType). \
                    order_by(schema.FileTransferType.id).first().id
        if not n_host.ilo_type:
            with schema.db_select(param.engine) as db:
                n_host.ilo_type = db.query(schema.IPMIType). \
                    order_by(schema.IPMIType.id).first().id
        add_host(param, n_host, password=password, parent=parent)
        del n_host
    return True


def add_route(param: parameters.WebParameters, r):
    with schema.db_edit(param.engine) as db:
        routes = db.query(schema.RouteMap).filter(schema.RouteMap.host == r['host']).all()

        route = schema.RouteMap(
            sequence=len(routes) + 1,
            host=r['host'],
            route=r['route']
        )
        db.add(route)
        db.flush()
        db.refresh(route)

        action = schema.Action(
            user=param.user_info.uid,
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
            user=param.user_info.uid,
            action_type=52,
            date=datetime.datetime.now(),
            message="Добавлена группа: {group.name} - id={group.id}({group})".format(group=group)
        )
        db.add(action)
        db.flush()
    return True


def add_access(param: parameters.WebParameters, a):
    with schema.db_edit(param.engine) as db:
        db.add(a)
        db.flush()
        db.refresh(a)

        action = schema.Action(
            user=param.user_info.uid,
            action_type=30,
            date=datetime.datetime.now(),
            message="Добавлено правило доступа - id={a.id}({a})".format(a=a)
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
            user=param.user_info.uid,
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
            user=param.user_info.uid,
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
            user=param.user_info.uid,
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
            user=param.user_info.uid,
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
            user=param.user_info.uid,
            action_type=24,
            date=datetime.datetime.now(),
            message="Удаление группы: id={}".format(group)
        )
        db.add(action)
        db.flush()

    return True


def del_access(param: parameters.WebParameters, access):
    """
    Удаление правил доступа
    :param param: WebParameters
    :param access: schema.AccessList.id
    :return: True
    """
    with schema.db_edit(param.engine) as db:
        db.query(schema.AccessList).filter(
            schema.AccessList.id == access
        ).update(
            {
                schema.AccessList.status: 2
            }
        )
        action = schema.Action(
            user=param.user_info.uid,
            action_type=31,
            date=datetime.datetime.now(),
            message="Удаление правила доступа: id={}".format(access)
        )
        db.add(action)
        db.flush()
    return True


def del_group_user(param: parameters.WebParameters, group=None, user=None):
    with schema.db_edit(param.engine) as db:
        db.query(schema.GroupUser).filter(schema.GroupUser.group == group, schema.GroupUser.user == user).delete()
        action = schema.Action(
            user=param.user_info.uid,
            action_type=55,
            date=datetime.datetime.now(),
            message="Удаление группы у пользователя {}: id={}".format(user, group)
        )
        db.add(action)
        db.flush()
    return True


def del_group_host(param: parameters.WebParameters, group=None, host=None):
    with schema.db_edit(param.engine) as db:
        db.query(schema.GroupHost).filter(schema.GroupHost.group == group, schema.GroupHost.host == host).delete()
        action = schema.Action(
            user=param.user_info.uid,
            action_type=56,
            date=datetime.datetime.now(),
            message="Удаление группы у хоста {}: id={}".format(host, group)
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
                user=param.user_info.uid,
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
                user=param.user_info.uid,
                action_type=24,
                date=datetime.datetime.now(),
                message="Удаление сервиса: id={}".format(service)
            )
            db.add(action)
            db.flush()
    return True


def del_prefix(param: parameters.WebParameters, prefix):
    with schema.db_edit(param.engine) as db:
        db.query(schema.Prefix).filter(schema.Prefix.id == prefix).delete()
        action = schema.Action(
            user=param.user_info.uid,
            action_type=4,
            date=datetime.datetime.now(),
            message="Удаление префикса: {id}".format(id=prefix)
        )
        db.add(action)
        db.flush()
    return True


def del_service_type(param: parameters.WebParameters, service):
    with schema.db_edit(param.engine) as db:
        s = db.query(schema.ServiceType).filter(schema.ServiceType.id == service).one()
        db.query(schema.ServiceType).filter(schema.ServiceType.id == service).delete()
        action = schema.Action(
            user=param.user_info.uid,
            action_type=9,
            date=datetime.datetime.now(),
            message="Удаление сервиса: {service.name}({service.id})".format(service=s)
        )
        db.add(action)
        db.flush()
    return True


def del_ipmi(param: parameters.WebParameters, ipmi):
    with schema.db_edit(param.engine) as db:
        db.query(schema.IPMIType).filter(schema.IPMIType.id == ipmi).delete()
        action = schema.Action(
            user=param.user_info.uid,
            action_type=7,
            date=datetime.datetime.now(),
            message="Удаление IPMI: {id}".format(id=ipmi)
        )
        db.add(action)
        db.flush()
    return True


def clear_routes(param: parameters.WebParameters, host_id):
    with schema.db_edit(param.engine) as db:
        db.query(schema.RouteMap).filter(schema.RouteMap.host == host_id).delete()
        action = schema.Action(
            user=param.user_info.uid,
            action_type=26,
            date=datetime.datetime.now(),
            message="Очистка маршрутов: host={}".format(host_id)
        )
        db.add(action)
        db.flush()

    return True


def check_worktime():
    work_hour = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    work_weekdays = [1, 2, 3, 4, 5]
    if datetime.datetime.today().hour in work_hour and datetime.datetime.today().isoweekday() in work_weekdays:
        return True
    return False


def get_password(app_param: parameters.Parameters, host):
    """
    Возвращает schema.Password
    :param app_param: Настроки приложения.
    :param host: Идентификатор хоста
    :return: None or schema.Password
    """
    with schema.db_select(app_param.engine) as db:
        try:
            login_password = db.query(schema.PasswordList).filter(
                schema.PasswordList.user == app_param.user_info.uid,
                schema.PasswordList.host == host
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            login_password = None

    return login_password


def save_password(app_param: parameters.AppParameters, host_id, user, password):
    """
    Сохранение пользовательских паролей для узлов сети.
    :param app_param: Настройки приложения
    :param host_id: ID узла
    :param user: Логин пользователя
    :param password: Пароль пользователя
    :return: None
    """
    with schema.db_edit(app_param.engine) as db:
        try:
            login_password = db.query(schema.PasswordList).filter(
                schema.PasswordList.user == app_param.user_info.uid,
                schema.PasswordList.host == host_id
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            login_password = None
        if login_password:
            login_password.login = user
            login_password.password = utils.password(password, host_id)
        else:
            db.add(
                schema.PasswordList(
                    user=app_param.user_info.uid,
                    host=host_id,
                    login=user,
                    password=utils.password(password, host_id)
                )
            )
        db.flush()


if __name__ == '__main__':
    e = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format('postgresql',
                                                         'acs',
                                                         'acs',
                                                         'localhost',
                                                         '5432',
                                                         'acs'
                                                         ))
    print(hashlib.md5('admin'.encode()).hexdigest())