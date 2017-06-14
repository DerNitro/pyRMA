# -*- coding: utf-8 -*-
# encoding: utf-8

from acs import schema, utils
import hashlib
import sqlalchemy
import datetime


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


def set_cookie(response, username, remote_addr, engine):
    response.set_

