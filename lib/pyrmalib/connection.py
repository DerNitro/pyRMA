#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Filename : ssh
    Date: 28.09.2018 06:38
    Project: pyRMA
    AUTHOR : Sergey Utkin

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

from pyrmalib import modules


class SSH(modules.ConnectionModules):
    """
    Модуль подключения к удаленному узлу по SSH.
    """
    def __init__(self):
        super().__init__()
        self.NAME = 'SSH'
        self.DESCRIPTION = 'Модуль подключения по протоколу SSH'
        self.AUTHOR = 'Sergey Utkin'
        self.DATE_CREATE = '01/10/2018'


class SFTP(modules.ConnectionModules):
    """
    Модуль передачи файлов по SSH.
    """
    def __init__(self):
        super().__init__()
        self.NAME = 'SFTP'
        self.DESCRIPTION = 'Модуль передачи файлов по SFTP'
        self.AUTHOR = 'Sergey Utkin'
        self.DATE_CREATE = '01/10/2018'


class TELNET(modules.ConnectionModules):
    """
    Модуль подключения к удаленному узлу по telnet
    """
    def __init__(self):
        super().__init__()
        self.NAME = 'Telnet'
        self.DESCRIPTION = 'Модуль подключения по протоколу Telnet'
        self.AUTHOR = 'Sergey Utkin'
        self.DATE_CREATE = '01/10/2018'


class SERVICE(modules.ConnectionModules):
    """
    Модуль формирования подключения только сервисов.
    """
    def __init__(self):
        super().__init__()
        self.NAME = 'OnlyServices'
        self.DESCRIPTION = 'Модуль подключниея только сервисов'
        self.AUTHOR = 'Sergey Utkin'
        self.DATE_CREATE = '01/10/2018'
