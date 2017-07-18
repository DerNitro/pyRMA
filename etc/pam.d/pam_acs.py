#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

from acs import schema, parameters
import sqlalchemy
import hashlib

"""
    Модуль PAM для авторизации пользователей SSH
    на основе данных в PostgreSQL
    
    http://pam-python.sourceforge.net/doc/html/#
    https://linux.die.net/man/3/pam
    https://github.com/gohourglass/pam-python-iam/blob/master/lib/security/pam_iam.py
"""


def get_user(login):
    """
    Функция получения данных о пользователе из СУБД.
    :param login: Имя пользователя
    :type login: str
    :return: Возвращает информацию user, group, group_list
    """
    try:
        pam_parameters = parameters.PamParametrs()
    except FileNotFoundError:
        return None

    engine = sqlalchemy.create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format(pam_parameters.dbase,
                                                                         pam_parameters.dbase_param[2],
                                                                         pam_parameters.dbase_param[3],
                                                                         pam_parameters.dbase_param[0],
                                                                         pam_parameters.dbase_param[1],
                                                                         pam_parameters.dbase_param[4]
                                                              ))
    with schema.db_select(engine) as db:
        user = db.query(schema.AAAUser).filter(schema.AAAUser.username == login).one()
        group = db.query(schema.AAAGroup)
        group_list = db.query(schema.AAAGroupList).filter(schema.AAAGroupList.username == login)
        pass

    return user, group, group_list


def pam_sm_authenticate(pamh, flags, argv):
    try:
        p_user = pamh.get_user(None)
    except pamh.exception as e:
        return e.pam_result

    if not p_user:
        return pamh.PAM_USER_UNKNOWN

    user, group, group_list = get_user(p_user)

    if not user:
        return pamh.PAM_USER_UNKNOWN

    try:
        resp = pamh.conversation(pamh.Message(pamh.PAM_PROMPT_ECHO_OFF, "Password: "))
    except pamh.exception as e:
        return e.pam_result

    if hashlib.md5(resp.resp.encode()).hexdigest() == user.password:
        return pamh.PAM_SUCCESS

    return pamh.PAM_AUTH_ERR


def pam_sm_setcred(pamh, flags, argv):
  return pamh.PAM_SUCCESS


def pam_sm_acct_mgmt(pamh, flags, argv):
  return pamh.PAM_SUCCESS


def pam_sm_open_session(pamh, flags, argv):
  return pamh.PAM_SUCCESS


def pam_sm_close_session(pamh, flags, argv):
  return pamh.PAM_SUCCESS


def pam_sm_chauthtok(pamh, flags, argv):
  return pamh.PAM_SUCCESS


if __name__ == '__main__':
    pass