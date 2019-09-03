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
from pyrmalib import schema, utils, email, template, parameters, error, access
from functools import wraps
import hashlib
import sqlalchemy
import datetime
import string
from flask import request, redirect, session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import create_engine


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

    return True


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
            content['default_password'] = utils.password(host.default_password, host_id, False)
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
                filter(schema.IloType.id == host.ilo_type).one()
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
                host = db.query(schema.Host).filter(schema.Host.id == host_id).one()
            except NoResultFound:
                return None
            except MultipleResultsFound:
                raise error.WTF("Дубли Host.id в таблице Host!!!")

            return host
    if name and parent:
        with schema.db_select(param.engine) as db:
            try:
                host = db.query(schema.Host).filter(schema.Host.name == name, schema.Host.parent == parent).one()
            except NoResultFound:
                return None
            except MultipleResultsFound:
                raise error.WTF("Дубли Host.name в таблице Host!!!")

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


def get_path(param: parameters.WebParameters, host_id=None):
    """
    Возвращает строку пути к хосту
    :param param: WebParameters
    :param host_id: schema.Host.id
    :return: str
    """
    if host_id is None or host_id == 0:
        return "/"
    else:
        return "path"


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
            message="Создание директории: {folder.name} - id={folder.id}".format(folder=folder)
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
            message="Редактирование директории: {folder.name} - id={folder.id}".format(folder=host)
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


if __name__ == '__main__':
    e = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format('postgresql',
                                                         'acs',
                                                         'acs',
                                                         'localhost',
                                                         '5432',
                                                         'acs'
                                                         ))
    pass
