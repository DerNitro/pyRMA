#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

from flask import Flask, render_template, redirect, request, Response
from functools import wraps
from acs import parameters, weblib, log
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
           'restore': 'restore.html'}


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
    return "Hi"


@app.route('/restore', methods=['GET', 'POST'])
def restore():
    if request.method == 'GET':
        return render_template(siteMap['restore'])
    elif request.method == 'POST':
        return 'POST'

if webParameters.template is not None:
    app.run(host=webParameters.ip, port=webParameters.port)
else:
    print('Not set template!!!')
