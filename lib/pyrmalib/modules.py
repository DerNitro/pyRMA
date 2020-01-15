#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Filename : Modules
    Date: 28.09.2018 06:43
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


class Modules:
    NAME = ''
    DESCRIPTION = ''
    AUTHOR = ''
    DATE_CREATE = ''

    def __init__(self):
        pass

    def initialize(self):
        """
        Иннициализация плагина в системе
        :return: Возвращает код завершения
        """
        pass


class ConnectionModules(Modules):
    def __init__(self):
        super().__init__()

    def connection(self):
        """
        Инициирует логику подключения к удаленному хосту.
        :return: Возвращает код завершения
        """
        pass

    def firewall(self):
        """
        Формирует правила сетевого экрана.
        :return: Возвращает код завершения
        """
        pass

    def route(self):
        """
        формирует маршрут доступа до узла.
        :return: Возвращает код завершения
        """
        pass
