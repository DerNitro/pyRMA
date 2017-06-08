#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

import sys
import traceback
from acs import parameters
from acs import interface
from acs import schema
import sqlalchemy.orm
from sqlalchemy import create_engine
from acs.utils import *
import datetime

__author__ = 'Sergey Utkin'
__email__ = 'utkins01@gmail.com'
__version__ = "0.0.1"
__status__ = "Testing"
__maintainer__ = "Sergey Utkin"
__copyright__ = "Copyright 2016, Sergey Utkin"
__program__ = 'Access Control System'

try:
    appParameters = parameters.Parameters()
except FileNotFoundError:
    print('Ошибка инициализации приложения!!!')
    print(traceback.print_exc(limit=1))
    sys.exit(1)
except parameters.CheckConfigError:
    print('Ошибка инициализации приложения!!!')
    print(traceback.print_exc(limit=1))
    sys.exit(2)

appParameters.program = __program__
appParameters.version = __version__
appParameters.log.info('Запуск приложения: {0} {1}'.format(__program__, __version__))
appParameters.log.debug(appParameters)

if not os.path.isfile(appParameters.license):
    print('Отсутствует файл лицензии!!!')
    appParameters.log.error("Отсутствует файл лицензии: {0}!!!".format(appParameters.license), pr=True)
    sys.exit(10)

if not check_license(appParameters.license):
    appParameters.log.error('Не корректный файл лицензии!!!', pr=True)
    sys.exit(11)
else:
    appParameters.log.info('Файл лицензии корректный.')

if appParameters.dbase in ['postgresql', 'mysql', 'oracle']:
    if appParameters.dbase == 'mysql':
        appParameters.dbase += '+pymysql'
    engine = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format(appParameters.dbase,
                                                              appParameters.dbase_param[2],
                                                              appParameters.dbase_param[3],
                                                              appParameters.dbase_param[0],
                                                              appParameters.dbase_param[1],
                                                              appParameters.dbase_param[4]))
else:
    appParameters.log.error('Некорректные параметры подключения к БД.', pr=True)
    sys.exit(12)

appParameters.engine = engine

try:
    with schema.db_select(engine) as db:
        appParameters.table_parameter = db.query(schema.Parameter).all()
except sqlalchemy.orm.exc.NoResultFound:
    # TODO: Заполнить таблицу дефолтными значениями.
    pass


try:
    with schema.db_select(engine) as db:
        aaa_user, user_info = db.query(schema.AAAUser, schema.User). \
            filter(schema.AAAUser.uid == schema.User.login). \
            filter(schema.AAAUser.username == appParameters.user_name).one()
        appParameters.log.debug(aaa_user)
        appParameters.aaa_user = aaa_user
        appParameters.user_info = user_info
        appParameters.log.debug(user_info)
except sqlalchemy.orm.exc.NoResultFound:
    appParameters.log.error("Пользователь не существует.", pr=True)
    sys.exit(13)

# Проверка соответсвия IP адреса с адресом подключения.
if list(filter(lambda x: x.name == 'CHECK_IP', appParameters.table_parameter))[0].value == '0':
    appParameters.log.info("Проверка IP отключена")
else:
    if not check_ip(os.environ.get('SSH_CLIENT').split()[0], user_info.ip):
        appParameters.log.error("Подключение с неразрешеного IP адрес", pr=True)
        sys.exit(14)
    else:
        appParameters.log.info("Подключение пользователя {0} с IP: {1}.". \
                               format(aaa_user.username, os.environ.get('SSH_CLIENT').split()[0]))

# Проверка блокироваки уч. записи, с автоматическим проблением даты блокировки.
if user_info.date_disable < datetime.datetime.now() or user_info.disable:
    appParameters.log.error("Учетная запись заблокирована.", pr=True)
    sys.exit(15)
else:
    if list(filter(lambda x: x.name == 'AUTO_EXTENSION', appParameters.table_parameter))[0].value == '1' \
            and user_info.date_disable < datetime.datetime.now() + datetime.timedelta(days=15):
        ex_days = int(list(filter(lambda x: x.name == 'EXTENSION_DAYS', appParameters.table_parameter))[0].value)
        with schema.db_edit(engine) as db:
            status = db.query(schema.User).filter(schema.User.login == user_info.login). \
                update({schema.User.date_disable: datetime.datetime.now() + datetime.timedelta(days=ex_days)})
        if status == 1:
            appParameters.log.info("Продлен доступ к системе на {0} дней.".format(ex_days))
        else:
            appParameters.log.warning("Huston we have problem!!!")

with schema.db_edit(engine) as db:
    db.add(schema.Action(action_type=1,
                         user=aaa_user.uid,
                         date=datetime.datetime.now(),
                         message="Успешное подключение к системе."))

# schema.Group.__table__.create(bind=engine)
# Запуск интерфейса.
appParameters.log.debug("Запуск графического интерфейса.")
App = interface.Interface()
App.appParameters = appParameters
App.run()
appParameters.log.info('Выход из приложения.')
sys.exit(0)
