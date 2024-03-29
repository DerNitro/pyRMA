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
from datetime import date
from pyrmalib import utils

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, BooleanField, PasswordField
from wtforms.fields.datetime import DateField
from wtforms.validators import DataRequired, IPAddress, NumberRange, ValidationError


def ip_net_check(form, field):
    if utils.valid_net(field.data) or utils.valid_ip(field.data):
        pass
    else:
        raise ValidationError('Не корректное значение IP адреса!!!')


def port_list_check(form, field):
    for port in str(field.data).split(','):
        try:
            if 0 < int(port) <= 65535:
                pass
            else:
                raise ValidationError('Не корректное значение TCP Порта!!!')
        except ValueError:
            raise ValidationError('Не корректное значение TCP Порта!!!')


class Login(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()], )
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit_login = SubmitField('Войти')


class EditFolder(FlaskForm):
    name = StringField('Имя директории')
    describe = StringField('Описание')
    note = TextAreaField('Note')
    edit_sub = SubmitField('Редктировать')
    delete_sub = SubmitField('Удалить')
    add_sub = SubmitField('Добавить')


class EditHost(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    folder = SelectField('Директория')
    ip = StringField('IP адрес', validators=[DataRequired(), IPAddress()])
    port = IntegerField('Порт', validators=[NumberRange(min=0, max=65536)])
    connection_type = SelectField('Протокол подключения')
    file_transfer_type = SelectField('Протокол передачи данных')
    describe = StringField('Описание')
    ilo = StringField('IPMI адрес', validators=[IPAddress()])
    ilo_type = SelectField('Вендор IPMI')
    default_login = StringField('Логин')
    default_password = StringField('Пароль')
    note = TextAreaField('Note')
    proxy = BooleanField('Jump-хост')
    add_sub = SubmitField('Добавить')
    edit_sub = SubmitField('Изменить')
    delete_sub = SubmitField('Удалить')

    file_host = FileField('Файл', validators=[FileRequired()])
    upload_sub = SubmitField('Загрузить')


class AddServiceHost(FlaskForm):
    type = SelectField('Тип подключения')
    remote_ip = SelectField('Адрес назначения')
    describe = StringField('Описание')

    add_sub = SubmitField('Добавить')


class AddServiceHostAdmin(FlaskForm):
    type = SelectField('Тип подключения')
    remote_ip = StringField('Адрес назначения', validators=[IPAddress(), DataRequired()])
    describe = StringField('Описание')

    add_sub = SubmitField('Добавить')


class JumpHost(FlaskForm):
    jump = SelectField('Jump хост')
    add_sub = SubmitField('Добавить')

    clear_sub = SubmitField('Очистить')


class AddGroup(FlaskForm):
    name = StringField('Имя группы')
    type = SelectField('Тип группы', choices=[(0, 'Пользователи'), (1, 'Хосты')], coerce=int)

    add_sub = SubmitField('Добавить')


class ChangePermission(FlaskForm):
    ShowHostInformation = BooleanField('Просмотр информации об узле')
    EditHostInformation = BooleanField('Редактировать хосты')
    EditDirectory = BooleanField('Создание|Редактирование директорий')
    EditPrefixHost = BooleanField('Смена родителя для узлов')
    ShowLogin = BooleanField('Отображение логина')
    ShowPassword = BooleanField('Отображение пароля')
    ShowAllSession = BooleanField('Просмотр сессии пользователя')
    AccessRequest = BooleanField('Согласование доступов')
    EditCredential = BooleanField('Редактирование учетных данных подключения')

    Connection = BooleanField('Подключение к узлу')
    FileTransfer = BooleanField('Передача файлов')
    ConnectionService = BooleanField('Подключение сервисов')
    ConnectionOnlyService = BooleanField('Подключение только сервисов')
    ConnectionIlo = BooleanField('Подключение к интерфейсу управления сервером')

    edit_sub = SubmitField('Изменить')


class AddUserGroup(FlaskForm):
    name = SelectField('Группа пользователей', coerce=int)
    add_sub = SubmitField('Добавить')


class AddHostGroup(FlaskForm):
    name = SelectField('Группа улов', coerce=int)
    add_sub = SubmitField('Добавить')


class ResetPassword(FlaskForm):
    login = StringField('Логин или email')
    reset_sub = SubmitField('Восстановить пароль')


class Search(FlaskForm):
    search = StringField('Поиск')
    submit_search = SubmitField('Поиск')


class ShowLog(FlaskForm):
    date = DateField(format='%Y-%m-%d', default = date.today(), validators=[DataRequired()])
    user = SelectField('Пользователь', coerce=int)
    sub = SubmitField('Выбрать')


class ChangePrefix(FlaskForm):
    prefix = SelectField('Префикс', coerce=int)
    sub = SubmitField('Сохранить')


class AddAccess(FlaskForm):
    user_group = SelectField('Группа пользователей', coerce=int)
    host_group = SelectField('Группа хостов', coerce=int)
    date = DateField(format='%Y-%m-%d', default=date.today(), validators=[DataRequired()])
    note = StringField("Описание")
    sub = SubmitField('Добавить')


class DelButton(FlaskForm):
    sub = SubmitField('Удалить')


class Parameters(FlaskForm):
    email_host = StringField('Адрес EMAIL Сервера', validators=[IPAddress()])
    email_port = IntegerField('Порт EMAIL Сервера', validators=[NumberRange(min=1, max=65535)])
    email_from = StringField('Email отправителя', validators=[DataRequired()])
    email_cc = StringField('Получатели копии email сообщений')
    auto_extension = BooleanField('Автоопределение доступа')
    extension_days = IntegerField('Количество дней для автоопределения', validators=[NumberRange(min=1, max=365)])
    enable_route_map = BooleanField('Включение маршрутизации')
    check_ip = BooleanField('Включение проверки пользовательских IP адресов')
    forward_tcp_port_disable = StringField('Запрещенные порты для проброса(Разделитель ;)')
    forward_tcp_port_range = StringField('Диапазон портов для проброса портов(Разделитель ;)')
    sub = SubmitField('Сохранить')


class AddPrefix(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    describe = StringField('Описание')
    sub = SubmitField('Добавить')


class IPMI(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    vendor = StringField('Вендор')
    ports = StringField('Порты', validators=[DataRequired(), port_list_check])
    sub = SubmitField('Добавить')


class AddService(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    default_port = StringField('Порт по умолчанию')
    sub = SubmitField('Добавить')


class Access(FlaskForm):
    data_access = DateField(format='%Y-%m-%d', validators=[DataRequired()])
    connection = BooleanField('Подключение')
    file_transfer = BooleanField('Передача файлов')
    ipmi = BooleanField('IPMI')
    sub = SubmitField('OK')

class ConnectionFilter(FlaskForm):
    date_start = DateField(format='%Y-%m-%d', validators=[DataRequired()])
    date_end = DateField(format='%Y-%m-%d', validators=[DataRequired()])
    sub = SubmitField('Ок')

class User(FlaskForm):
    name = StringField('имя', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    ip = StringField('ip', validators=[DataRequired()])
    save = SubmitField('Сохранить')
