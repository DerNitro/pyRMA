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

from flask import Flask, render_template, redirect, request, Response, url_for
from functools import wraps
from pyrmalib import parameters, weblib, log
import os.path
from sqlalchemy import create_engine


webParameters = parameters.WebParameters()
engine = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format(webParameters.dbase,
                                                          webParameters.dbase_param[2],
                                                          webParameters.dbase_param[3],
                                                          webParameters.dbase_param[0],
                                                          webParameters.dbase_param[1],
                                                          webParameters.dbase_param[4]
                                                          ))
app = Flask('ACS_WEB',
            template_folder=webParameters.template,
            static_folder=os.path.join(webParameters.template, 'static'))
# schema.install(engine)
logger = log.Log("Web_syslog", level=webParameters.log_level, facility=webParameters.log_facility)

siteMap = {'index': 'index.html',
           'error': 'error.html',
           'restore': 'restore.html',
           'reset password': 'reset_password.html'}


def log_access(req, resp):
    return '{0}: "{1} {2}" {3}'.format(req.remote_addr, req.method, req.path, resp.status)


def check_auth(username, password, client_ip):
    return weblib.login_access(username=username, password=password, engine=engine, ip=client_ip)


def authenticate():
    return Response(render_template(siteMap['error'], error='NotAuthenticate'),
                    401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        client_ip = request.remote_addr
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password, client_ip):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@requires_auth
def root():
    return render_template(siteMap['index'])


@app.route('/restore', methods=['GET', 'POST'])
def get_restore():
    if request.method == 'GET':
        return render_template(siteMap['restore'])
    elif request.method == 'POST':
        if weblib.restore_password(request.form['username'], engine, request):
            status = "Инструкции отправлены"
            return render_template(siteMap['restore'], status=status)
        else:
            status = "Error!!!"
            return render_template(siteMap['restore'], status=status)


@app.route('/restore/<key>', methods=['GET', 'POST'])
def restore(key):
    if request.method == 'GET':
        if weblib.reset_password(key, engine, check=True):
            return render_template(siteMap['reset password'], key=key)
        else:
            render_template(siteMap['error'], error='404')
    elif request.method == 'POST':
        if request.form['password_check'] == request.form['password']:
            if weblib.reset_password(key, engine, password=request.form['password']):
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
