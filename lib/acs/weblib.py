# -*- coding: utf-8 -*-
# encoding: utf-8

from acs import schema
import hashlib


def check_access(request, engine):
    return False


def login_access(username, password, engine):
    with schema.db_select(engine) as db:
        aaa = db.query(schema.AAAUser).filter(schema.AAAUser.username == username).one()

    if not aaa:
        return False

    if aaa.password != hashlib.md5(password).hexdigest():
        return False

    return True