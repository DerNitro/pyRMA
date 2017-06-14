#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

from bottle import Bottle, template, response, request, static_file, redirect
from acs import parameters, weblib, schema
import logging
from logging import handlers, Formatter
import os.path
from sqlalchemy import create_engine
import sys


webParameters = parameters.WebParameters()
engine = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format(webParameters.dbase,
                                                          webParameters.dbase_param[2],
                                                          webParameters.dbase_param[3],
                                                          webParameters.dbase_param[0],
                                                          webParameters.dbase_param[1],
                                                          webParameters.dbase_param[4]
                                                          ))
app = Bottle()
# schema.install(engine)
logger = logging.getLogger('WebLog')
logger.setLevel(webParameters.log_level)
h = handlers.RotatingFileHandler(webParameters.log_file,
                                 backupCount=webParameters.log_rotate_count,
                                 maxBytes=webParameters.log_rotate_size)
log_format = Formatter('[%(asctime)s] [%(levelname)-8s] - %(message)s')
h.setFormatter(log_format)
logger.addHandler(h)

siteMap = {'index': 'index.html',
           'login': 'login.html'}


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
    return template(os.path.join(webParameters.template, siteMap['index']), path=webParameters.template, menu=True)


@app.route('/login.html')
def login():
    logger.info(log_access(request, response))
    return template(os.path.join(webParameters.template, siteMap['login']), path=webParameters.template, menu=False)


@app.post('/login.html')
def post_login():
    username = request.forms.get('username')
    password = request.forms.get('password')
    remember = request.forms.get('remember_me')
    logger.info(log_access(request, response))
    if weblib.login_access(username, password, request.remote_addr, engine):
        weblib.set_cookie(response, username, request.remote_addr, engine)
        redirect('/')
    else:
        return template(os.path.join(webParameters.template, siteMap['login']), path=webParameters.template, menu=False, status='Не верный пароль')


# Статические страницы
@app.error(404)
def error404(error):
    logger.info(log_access(request, response))
    return '<b>"Nothing here, sorry"</b>!'


@app.get('/<filename:re:.*\.css>')
def stylesheets(filename):
    return static_file(filename, root=webParameters.template)


if webParameters.template is not None:
    # schema.WebAccess.__table__.create(bind=engine)
    app.run(host=webParameters.ip, port=webParameters.port)
else:
    print('Not set template!!!')
