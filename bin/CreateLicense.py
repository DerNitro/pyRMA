#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

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

import argparse
import hashlib
import textwrap
from datetime import timedelta, datetime

P_NAME = 'pyFakeCreateLic'
P_VER = '0.1'

arg = argparse.ArgumentParser(
    epilog=P_NAME + ' ' + P_VER + ' (C) "Sergey Utkin"',
    add_help=False,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
    Программа создания файла лицензии.
    Уткин Сергей
    utkins01@gmail.com'''))

param = arg.add_argument_group(title='Параметры')
param.add_argument('idhost', type=str, action='store', help='Уникальный ключ хоста')
param.add_argument('hostname', type=str, action='store', help='Имя хоста')
param.add_argument('platform', type=str, action='store', help='Платформа')
param.add_argument('--days',
                   action='store',
                   type=int,
                   help='Срок действия ключа в днях. По умолчанию 365 дней',
                   default=365)
param.add_argument('--file', action='store', type=str, help='Выходной файл')
param.add_argument('--version', action='version', help='Версия программы',
                   version='%(prog)s {}'.format(P_VER))
param.add_argument('--help', '-h', action='help', help='Справка')
option = vars(arg.parse_args())

idhost = option['idhost']
hostname = option['hostname']
platform = option['platform']
days = datetime.now() + timedelta(days=option['days'])


def create_hash(id_host, host_name, os, day):
    return hashlib.md5(str(id_host).encode() + str(host_name).encode() + str(os).encode() + str(
        day.strftime('%d/%m/%Y')).encode()).hexdigest()


if option['file']:
    f = open(option['file'], 'w')
    f.write(str("{0} {1} {2} {3} {4}".format(create_hash(idhost, hostname, platform, days),
                                             idhost,
                                             hostname,
                                             platform,
                                             days.strftime('%d/%m/%Y'))))
    f.close()
else:
    print(str("{0} {1} {2} {3} {4}".format(create_hash(idhost, hostname, platform, days),
                                           idhost,
                                           hostname,
                                           platform,
                                           days.strftime('%d/%m/%Y'))))
