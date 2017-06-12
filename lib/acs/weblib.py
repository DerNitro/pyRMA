# -*- coding: utf-8 -*-
# encoding: utf-8

from acs import schema, utils
import hashlib
import sqlalchemy


def check_access(request, engine):
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
