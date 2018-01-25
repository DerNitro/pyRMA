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
import random

from pyrmalib import schema, utils, email, template
import hashlib
import sqlalchemy
import datetime
import string
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


def check_access(request, engine):
    user_id = request.get_cookie('id', default=None)
    key = request.get_cookie('key', default=None)
    if user_id and key:
        with schema.db_select(engine) as db:
            access = db.query(schema.WebAccess).filter(schema.WebAccess.user == int(user_id)).one
        if not access:
            return False

        if key == access.key and request.remote_addr == access.ip and datetime.datetime.now() < access.expires:
            return True
        else:
            return False

    else:
        return False


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

    return True


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
        db.query(schema.RestorePassword).\
            filter(sqlalchemy.and_(schema.RestorePassword.key == key,
                   schema.RestorePassword.status == 1)).\
            update({schema.RestorePassword.status: 2,
                   schema.RestorePassword.date_complete:  datetime.datetime.now()})
        db.query(schema.AAAUser).\
            filter(schema.AAAUser.uid == restore.user).\
            update({schema.AAAUser.password: hashlib.md5(str(password).encode()).hexdigest()})
    email.send_mail(engine, template.restore_password_access(), aaa_user.uid, {'login': aaa_user.username})
    return True
