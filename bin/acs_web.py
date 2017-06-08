#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

from bottle import Bottle, template, response, request, static_file, redirect
from acs import parameters, weblib
import logging
from logging import handlers, Formatter
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
    return template(os.path.join(webParameters.template, siteMap['index']))


@app.route('/login.html')
def login():
    logger.info(log_access(request, response))
    return template(os.path.join(webParameters.template, siteMap['login']))


@app.post('/login.html')
def post_login():
    username = request.forms.get('login')
    password = request.forms.get('password')
    remember = request.forms.get('remember_me')
    if weblib.login_access(username, password, engine):
        return '<b>True</b>'.format(username, password, remember)
    else:
        return '<b>False</b>'.format(username, password, remember)


# Статические страницы
@app.error(404)
def error404(error):
    logger.info(log_access(request, response))
    return '<b>"Nothing here, sorry"</b>!'


if webParameters.template is not None:
    app.run(host=webParameters.ip, port=webParameters.port)
else:
    print('Not set template!!!')
