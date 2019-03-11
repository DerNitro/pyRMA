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
           'error': 'error.html',
           'restore': 'restore.html',
           'reset password': 'reset_password.html',
           'hosts': 'hosts.html',
           'login': 'login.html',
           'registration': 'registration.html'}


def check_auth(username, password, client_ip):
    return weblib.login_access(username=username, password=password, engine=webParameters.engine, ip=client_ip)


@app.route('/', methods=['GET'])
@weblib.authorization(session, request, webParameters)
def root():
    content = weblib.get_content_dashboard(webParameters)
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
            error = 'Не правильный логин или пароль'
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
@weblib.authorization(session, request, webParameters)
def hosts():
    return render_template(siteMap['hosts'], admin=access.check_access(webParameters, 'Administrate'))


@app.route('/administrate')
@weblib.authorization(session, request, webParameters)
def administrate():
    return render_template(siteMap['administrate'], admin=access.check_access(webParameters, 'Administrate'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    status = None
    error = None
    if request.method == 'POST':
        pass

    return render_template(siteMap['registration'], status=status, error=error)


@app.route('/restore', methods=['GET', 'POST'])
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
            render_template(siteMap['error'], error='404')
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
