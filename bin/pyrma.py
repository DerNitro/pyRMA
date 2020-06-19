#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8
# PYTHONPATH=./lib/ ./bin/pyrma.py

"""
       Copyright 2016, Sergey Utkin mailto:utkins01@gmail.com

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

import sys
import traceback
from pyrmalib import parameters, interface, schema, error, modules
import sqlalchemy.orm
from sqlalchemy import create_engine
from pyrmalib.utils import *
import datetime

__author__ = 'Sergey Utkin'
__email__ = 'utkins01@gmail.com'
__version__ = "0.0.1"
__status__ = "Development"
__maintainer__ = "Sergey Utkin"
__copyright__ = "Copyright 2016, Sergey Utkin"
__program__ = 'pyRMA'

try:
    appParameters = parameters.AppParameters()
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
    engine = create_engine(
        '{0}://{1}:{2}@{3}:{4}/{5}'.format(
            appParameters.dbase,
            appParameters.dbase_param["user"],
            appParameters.dbase_param["password"],
            appParameters.dbase_param["host"],
            appParameters.dbase_param["port"],
            appParameters.dbase_param["database"]
        )
    )
else:
    appParameters.log.error('Некорректные параметры подключения к БД.', pr=True)
    sys.exit(12)

appParameters.engine = engine

try:
    with schema.db_select(engine) as db:
        appParameters.table_parameter = db.query(schema.Parameter).all()
        appParameters.log.debug(appParameters.table_parameter)
except sqlalchemy.orm.exc.NoResultFound:
    error.WTF("Ошибка инициализации приложения")
    sys.exit(13)

try:
    with schema.db_select(engine) as db:
        aaa_user, user_info = db.query(schema.AAAUser, schema.User). \
            filter(schema.AAAUser.uid == schema.User.login). \
            filter(schema.AAAUser.username == appParameters.user_name).one()
        appParameters.log.debug(aaa_user)
        appParameters.log.debug(user_info)
        appParameters.aaa_user = aaa_user
        appParameters.user_info = user_info
except sqlalchemy.orm.exc.NoResultFound:
    appParameters.log.error("Пользователь не существует.", pr=True)
    sys.exit(14)

# Проверка соответсвия IP адреса с адресом подключения.
try:
    ssh_client_ip = os.environ.get('SSH_CLIENT').split()[0]
except AttributeError:
    ssh_client_ip = '127.0.0.1'
if list(filter(lambda x: x.name == 'CHECK_IP', appParameters.table_parameter))[0].value == '0':
    appParameters.log.debug("Проверка IP отключена")
else:
    if not check_ip(ssh_client_ip, user_info.ip):
        appParameters.log.error("Подключение с неразрешеного IP адрес", pr=True)
        sys.exit(15)
    else:
        appParameters.log.info(
            "Подключение пользователя {0} с IP: {1}.".format(
                aaa_user.username, ssh_client_ip
            )
        )

# Проверка блокироваки уч. записи, с автоматическим продлением даты блокировки.
if user_info.date_disable < datetime.datetime.now() or user_info.disable:
    appParameters.log.error("Учетная запись заблокирована.", pr=True)
    sys.exit(16)
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

try:
    ttyrec_file = os.path.join(os.environ.get('file_path').split()[0], os.environ.get('file_rec').split()[0])
except AttributeError:
    appParameters.log.error("Ошибка записи сессии.", pr=True)
    sys.exit(17)

with schema.db_edit(engine) as db:
    session = schema.Session(
            user=aaa_user.uid,
            date_start=datetime.datetime.now(),
            pid=os.getpid(),
            ppid=os.getppid(),
            ip=ssh_client_ip,
            ttyrec=ttyrec_file
        )

    db.add(session)
    db.flush()
    db.refresh(session)
    appParameters.session = session.id

with schema.db_edit(engine) as db:
    db.add(schema.Action(action_type=1,
                         user=aaa_user.uid,
                         date=datetime.datetime.now(),
                         message="Успешное подключение к системе."))

# Запуск интерфейса.
appParameters.log.debug("Запуск графического интерфейса.")
App = interface.Interface(appParameters)
connection_host = App.run()
if connection_host:      # type: modules.ConnectionModules
    connection_host.firewall()
    pass
appParameters.log.info('Выход из приложения.')

with schema.db_edit(engine) as db:
    db.query(schema.Session).filter(
        schema.Session.id == appParameters.session
    ).update(
        {
            schema.Session.status: 1,
            schema.Session.date_end: datetime.datetime.now(),
            schema.Session.termination: 0
        }
    )

sys.exit(0)
