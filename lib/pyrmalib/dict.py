#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Copyright 2020 Sergey Utkin utkins01@gmail.com

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

action_type = {
    1: "Вход в систему доступа",
    2: "Изменение параметров",
    3: "Создание префикса",
    4: "Удаление префикса",
    5: "Добавление IPMI",
    6: "Изменение IPMI",
    7: "Удаление IPMI",
    8: "Добавление Сервиса",
    9: "Удаление Сервиса",
    10: "Создание директории",
    11: "Редактирование директории",
    12: "Удаление директории",
    20: "Создание хоста",
    21: "Редактирование хоста",
    22: "Удаление хоста",
    23: "Добавление сервиса(хост)",
    24: "Удаление сервиса(хост)",
    25: "Добавление Jump хоста",
    26: "Удаление Jump хоста",
    30: "Добавление правила доступа",
    31: "Удаление правила доступа",
    32: "Запрос доступа",
    33: "Подтверждение доступа",
    34: "Запрет доступа",
    40: "Включение прав администратора",
    41: "Выключение прав администратора",
    51: "Изменение правил доступа",
    52: "Добавление группы",
    53: "Добавление группы к пользователю",
    54: "Добавление группы к хосту",
    55: "Удаление группы у пользователя",
    56: "Удаление группы у хоста",
    57: "Отключение пользователя",
    58: "Включение пользователя",
    59: "Редактирование пользователя",
    60: "Смена префикса",
    61: "Смена прав доступа"
}

conn_type_dict = {
    "Connection":       1,
    "File Transfer":    2,
    "Service":          3,
    "IPMI":             4
}
