# -*- coding: utf-8 -*-
# encoding: utf-8
import random

from acs import schema, utils, email
import hashlib
import sqlalchemy
import datetime
import string


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
            param = db.query(schema.Parameter).filter(schema.Parameter.name == 'CHECK_IP').one()
        except sqlalchemy.orm.exc.NoResultFound:
            return False

    if not aaa:
        return False

    if aaa.password != hashlib.md5(password.encode()).hexdigest():
        return False

    if not utils.check_ip(ip, user.ip) and param.value == '1':
        return False

    return True


def restore_password(username, engine):
    with schema.db_select(engine) as db:
        user_id = db.query(schema.User.login).join(schema.AAAUser, schema.User.login == schema.AAAUser.uid).\
            filter(sqlalchemy.or_(schema.AAAUser.username == username, schema.User.email == username)).all()

    if len(user_id) !=1:
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

    email.send_mail()
    return True


def set_cookie(response, username, remote_addr, engine):
    pass

