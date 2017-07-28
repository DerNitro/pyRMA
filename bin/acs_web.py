#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

from bottle import Bottle, template, response, request, static_file, redirect, TEMPLATE_PATH
from acs import parameters, weblib, log
import os.path
from sqlalchemy import create_engine


webParameters = parameters.WebParameters()
TEMPLATE_PATH.insert(0, webParameters.template)
engine = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format(webParameters.dbase,
                                                          webParameters.dbase_param[2],
                                                          webParameters.dbase_param[3],
                                                          webParameters.dbase_param[0],
                                                          webParameters.dbase_param[1],
                                                          webParameters.dbase_param[4]
                                                          ))
app = Bottle()
# schema.install(engine)
logger = log.Log("Web_syslog", level=webParameters.log_level, facility=webParameters.log_facility)

siteMap = {'index': 'index.html',
           'login': 'login.html',
           'restore': 'restore.html'}


def log_access(req, resp):
    return '{0}: "{1} {2}" {3}'.format(req.remote_addr, req.method, req.path, resp.status)


@app.route('/')
def root():
    logger.info(log_access(request, response))
    if weblib.check_access(request, engine):
        redirect('/index.html')
    else:
        redirect('/login.html')


@app.route('/index.html')
def index():
    logger.info(log_access(request, response))
    return template(os.path.join(webParameters.template, siteMap['index']), menu=True)


@app.route('/login.html')
def login():
    logger.info(log_access(request, response))
    return template(os.path.join(webParameters.template, siteMap['login']), menu=False)


@app.post('/login.html')
def post_login():
    username = request.forms.get('username')
    password = request.forms.get('password')
    remember = request.forms.get('remember_me')
    logger.info(log_access(request, response))
    if weblib.login_access(username, password, request.remote_addr, engine):
        if remember:
            weblib.set_cookie(response, username, request.remote_addr, engine)
        redirect('/')
    else:
        return template(os.path.join(webParameters.template, siteMap['login']),
                        menu=False, status='Не верный пароль')


@app.route('/restore.html')
def restore():
    logger.info(log_access(request, response))
    return template(os.path.join(webParameters.template, siteMap['restore']))


@app.post('/restore.html')
def generation_restore_password():
    logger.info(log_access(request, response))
    username = request.forms.get('username')
    if weblib.restore_password(username, engine, request):
        return template(os.path.join(webParameters.template, siteMap['restore']),
                        status='Инструкции отправлены на email')
    else:
        return template(os.path.join(webParameters.template, siteMap['restore']),
                        status='Пользователь не найден, обратитесь к администратору.')


# Статические страницы
@app.error(404)
def error404():
    logger.info(log_access(request, response))
    return '<b>"Nothing here, sorry"</b>!'


@app.get('/<filename:re:.*\.css>')
def stylesheets(filename):
    logger.info(log_access(request, response))
    return static_file(filename, root=os.path.join(webParameters.template))


if webParameters.template is not None:
    # schema.WebAccess.__table__.create(bind=engine)
    app.run(host=webParameters.ip, port=webParameters.port)
else:
    print('Not set template!!!')
