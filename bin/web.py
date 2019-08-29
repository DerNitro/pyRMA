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

from flask import Flask, render_template, request, redirect, session, url_for
from pyrmalib import parameters, weblib, log, access
import os.path
from sqlalchemy import create_engine
import validators

webParameters = parameters.WebParameters()
webParameters.engine = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format(webParameters.dbase,
                                                                        webParameters.dbase_param[2],
                                                                        webParameters.dbase_param[3],
                                                                        webParameters.dbase_param[0],
                                                                        webParameters.dbase_param[1],
                                                                        webParameters.dbase_param[4]
                                                                        ))
app = Flask(__name__,
            template_folder=webParameters.template,
            static_folder=os.path.join(webParameters.template, 'static'))
app.secret_key = os.urandom(64)

logger = log.Log("Web_syslog", **webParameters.log_param)

siteMap = {'index': 'index.html',
           'settings': 'settings.html',
           'administrate': 'admin.html',
           'restore': 'restore.html',
           'reset password': 'reset_password.html',
           'hosts': 'hosts.html',
           'host': 'host.html',
           'login': 'login.html',
           'registration': 'registration.html',
           '404': '404.html',
           'access_denied': 'access_denied.html',
           'add_folder': 'add_folder.html'}


def check_auth(username, password, client_ip):
    return weblib.login_access(username=username, password=password, engine=webParameters.engine, ip=client_ip)


@app.route('/', methods=['GET'])
@weblib.authorization(session, request, webParameters)
def root():
    if access.check_access(webParameters, 'Administrate'):
        content = weblib.get_admin_content_dashboard(webParameters)
    else:
        content = weblib.get_user_content_dashboard(webParameters)
    return render_template(siteMap['index'],
                           admin=access.check_access(webParameters, 'Administrate'),
                           content=content)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if weblib.login_access(request.form['username'],
                               request.form['password'],
                               request.remote_addr,
                               webParameters.engine):
            session['username'] = request.form['username']
            return redirect('/')
        else:
            error = 'Не правильный логин|пароль или учетная запись заблокирована!!!'
    return render_template(siteMap['login'], error=error)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/settings')
@weblib.authorization(session, request, webParameters)
def settings():
    return render_template(siteMap['settings'], admin=access.check_access(webParameters, 'Administrate'))


@app.route('/hosts')
@app.route('/hosts/<directory_id>')
@weblib.authorization(session, request, webParameters)
def hosts(directory_id=None):
    if directory_id:
        directory_id = directory_id
        edit_host_information = access.check_access(webParameters, 'EditHostInformation',
                                                    h_object=weblib.get_host(webParameters, host_id=directory_id))
        edit_directory = access.check_access(webParameters, 'EditDirectory',
                                             h_object=weblib.get_host(webParameters, host_id=directory_id))
        admin = access.check_access(webParameters, 'Administrate',
                                    h_object=weblib.get_host(webParameters, host_id=directory_id))
    else:
        directory_id = 0
        edit_host_information = access.check_access(webParameters, 'EditHostInformation')
        edit_directory = access.check_access(webParameters, 'EditDirectory')
        admin = access.check_access(webParameters, 'Administrate')
    host_list = weblib.get_host_list(webParameters, directory_id)
    return render_template(siteMap['hosts'],
                           admin=admin,
                           host_list=host_list,
                           path=weblib.get_path(webParameters, host_id=directory_id),
                           directory_id=directory_id,
                           EditHostInformation=edit_host_information,
                           EditDirectory=edit_directory)


@app.route('/hosts/<directory_id>/add_folder', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def add_folder(directory_id):
    error = None
    status = None
    admin = access.check_access(webParameters, 'Administrate',
                                h_object=weblib.get_host(webParameters, host_id=directory_id))

    if request.method == 'POST':
        folder = {
            'name': request.form['name'],
            'describe': request.form['describe'],
            'parent': directory_id,
            'prefix': webParameters.user_info.prefix
        }
        print(folder)
        if weblib.get_host(webParameters, name=folder['name'], parent=directory_id):
            error = 'Имя уже существует'

        if not error:
            if weblib.add_folder(webParameters, folder):
                status = 'Директория добавлена'
            else:
                status = 'Ошибка создания директории'

    return render_template(siteMap['add_folder'],
                           admin=admin,
                           directory_id=directory_id,
                           error=error,
                           status=status)


@app.route('/hosts/<directory_id>/add_host')
@weblib.authorization(session, request, webParameters)
def add_host(directory_id):
    return 'add_host'


@app.route('/host/<host_id>')
@weblib.authorization(session, request, webParameters)
def host(host_id):
    if access.check_access(webParameters,
                           'ShowHostInformation',
                           h_object=weblib.get_host(webParameters, host_id=host_id)):
        return render_template(siteMap['host'],
                               admin=access.check_access(webParameters, 'Administrate'),
                               EditHostInformation=access.check_access(webParameters,
                                                                       'EditHostInformation',
                                                                       h_object=weblib.get_host(webParameters,
                                                                                                host_id=host_id)),
                               content=weblib.get_content_host(webParameters, host_id)
                               )
    else:
        return render_template(siteMap['access_denied'])


@app.route('/administrate')
@weblib.authorization(session, request, webParameters)
def administrate():
    return render_template(siteMap['administrate'], admin=access.check_access(webParameters, 'Administrate'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    status = None
    error = None
    if request.method == 'POST':
        registration_data = {'username': request.form['username'],
                             'password': request.form['password'],
                             'full_name': request.form['full_name'],
                             'email': request.form['email'],
                             'ip': request.form['ip']}
        password_check = request.form['password_check']
        if registration_data['password'] != password_check:
            error = 'Не корректная пара паролей!'
        if weblib.user_info(registration_data['username'], webParameters.engine):
            error = 'Данное имя пользователя занято!'
        if not validators.email(registration_data['email']):
            error = 'Не корректно указан email!'
        if not validators.ipv4(registration_data['ip']):
            error = 'Не корректно указан IP адрес!'
        if registration_data['username'] \
                and password_check \
                and registration_data['password'] \
                and registration_data['full_name'] \
                and registration_data['email'] \
                and registration_data['ip']:
            pass
        else:
            error = 'Не все заполнены поля!'

        if not error:
            if weblib.user_registration(registration_data, webParameters.engine):
                status = 'Пользователь создан.'
            else:
                error = 'Во время создания пользователя произошла ошибка!'

    return render_template(siteMap['registration'], status=status, error=error)


@app.route('/restore', methods=['GET','POST'])
def get_restore():
    if request.method == 'POST':
        if weblib.restore_password(request.form['username'], webParameters.engine, request):
            status = "Инструкции отправлены"
            return render_template(siteMap['restore'], status=status)
        else:
            status = "Error!!!"
            return render_template(siteMap['restore'], status=status)

    return render_template(siteMap['restore'])


@app.route('/restore/<key>', methods=['GET', 'POST'])
def restore(key):
    if request.method == 'GET':
        if weblib.reset_password(key, webParameters.engine, check=True):
            return render_template(siteMap['reset password'], key=key)
        else:
            render_template(siteMap['404']), 404
    elif request.method == 'POST':
        if request.form['password_check'] == request.form['password']:
            if weblib.reset_password(key, webParameters.engine, password=request.form['password']):
                status = 'Password reset'
                return render_template(siteMap['reset password'], status=status)
            else:
                status = 'Error reset'
                return render_template(siteMap['reset password'], status=status)
        else:
            return render_template(siteMap['reset password'])


if webParameters.template is not None:
    app.run(host=webParameters.ip, port=webParameters.port)
else:
    print('Not set template!!!')
