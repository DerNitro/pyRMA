#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Filename : forms
    Date: 02.09.2019 07:52
    Project: pyRMA
    AUTHOR : Sergey Utkin
    
    Copyright 2019 Sergey Utkin utkins01@gmail.com

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

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, BooleanField
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import DataRequired, IPAddress, NumberRange


class EditFolder(FlaskForm):
    name = StringField('Имя директории')
    describe = StringField('Описание')
    note = TextAreaField('Note')
    edit_sub = SubmitField('Редктировать')
    delete_sub = SubmitField('Удалить')
    add_sub = SubmitField('Добавить')


class EditHost(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    ip = StringField('IP адрес', validators=[DataRequired(), IPAddress()])
    port = IntegerField('Порт', validators=[NumberRange(min=0, max=65536)])
    connection_type = SelectField('Протокол подключения')
    file_transfer_type = SelectField('Протокол передачи данных')
    describe = StringField('Описание')
    ilo = StringField('iLo адрес', validators=[IPAddress()])
    ilo_type = SelectField('Вендор IPMI')
    default_login = StringField('Логин')
    default_password = StringField('Пароль')
    note = TextAreaField('Note')
    proxy = BooleanField('Прокси-сервер')
    add_sub = SubmitField('Добавить')
    edit_sub = SubmitField('Редктировать')
    delete_sub = SubmitField('Удалить')

    file_host = FileField('Файл', validators=[FileRequired()])
    upload_sub = SubmitField('Загрузить')


class AddService(FlaskForm):
    type = SelectField('Тип подключения')
    remote_port = IntegerField('Порт', validators=[NumberRange(min=0, max=65536)])
    remote_ip = StringField('Адрес назначения', validators=[IPAddress()])
    internal = BooleanField('Внутренний')
    describe = StringField('Описание')

    add_sub = SubmitField('Добавить')


class AddRoute(FlaskForm):
    route = SelectField('Промежуточный хост')
    add_sub = SubmitField('Добавить')

    clear_sub = SubmitField('Очистить')