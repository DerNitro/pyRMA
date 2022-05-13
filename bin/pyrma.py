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

from pickle import TRUE
import sys
import pwd, grp
import traceback
from pyrmalib import parameters, interface, schema, error, modules, applib
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
pw_name, pw_passwd, pw_uid, pw_gid, pw_gecos, pw_dir, pw_shell = pwd.getpwuid(os.getuid())

if appParameters.dbase in ['postgresql']:
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
    ssh_client_ip = os.environ.get('SSH_CLIENT').split()[0]
except AttributeError:
    ssh_client_ip = '127.0.0.1'

try:
    with schema.db_select(engine) as db:
        user_info = db.query(schema.User). \
            filter(schema.User.login == pw_name).one()
        appParameters.log.debug(user_info)
        appParameters.user_info = user_info
except sqlalchemy.orm.exc.NoResultFound:
    groups = [g.gr_name for g in grp.getgrall() if pw_name in g.gr_mem]
    groups.append(grp.getgrgid(pw_gid).gr_name)
    app_group = applib.get_group_user(appParameters)
    if len(list(set(groups) & set([t.name for t in app_group]))) > 0:
        applib.user_registration(
            {
                'uid': pw_uid,
                'login': pw_name,
                'full_name': pw_gecos,
                'ip': ssh_client_ip,
                'email': "{}@{}".format(pw_name, appParameters.users['email_domain_name']),
                'check': 0
            },
            appParameters
        )
        for i in list(set(groups) & set([t.name for t in app_group])):
            gid = None
            for g in app_group:
                if i == g.name:
                    gid = g.id
            if gid:
                applib.add_user_group(appParameters, pw_uid, gid)
finally:
    with schema.db_select(engine) as db:
        user_info = db.query(schema.User). \
            filter(schema.User.login == appParameters.user_name).one()
        appParameters.log.debug(user_info)
        appParameters.user_info = user_info

# Проверка соответсвия IP адреса с адресом подключения.
if list(filter(lambda x: x.name == 'CHECK_IP', appParameters.table_parameter))[0].value == '0':
    appParameters.log.debug("Проверка IP отключена")
else:
    if not check_ip(ssh_client_ip, user_info.ip):
        appParameters.log.error("Подключение с неразрешеного IP адрес", pr=True)
        sys.exit(15)
    else:
        appParameters.log.info(
            "Подключение пользователя {0} с IP: {1}.".format(
                appParameters.user_info.login, ssh_client_ip
            )
        )

# Проверка блокировки уч. записи, с автоматическим продлением даты блокировки.
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
            user=user_info.uid,
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
                         user=user_info.uid,
                         date=datetime.datetime.now(),
                         message="Успешное подключение к системе."))

# Запуск интерфейса.
appParameters.log.debug("Запуск графического интерфейса.")
App = interface.Interface(appParameters)
connection_host = App.run()
if connection_host:      # type: modules.ConnectionModules
    connection_host.run()
    try:
        connection_host.connection()
    except KeyboardInterrupt:
        pass
connection_host.close()
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
