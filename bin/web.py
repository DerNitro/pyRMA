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
import datetime
import json

from flask import Flask, render_template, request, redirect, session, url_for
from flask_wtf.csrf import CSRFProtect
from pyrmalib import schema, parameters, weblib, log, access, forms, error as rma_error
import os.path
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename

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
app.debug = True
csrf = CSRFProtect()
csrf.init_app(app)

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
           'add_folder': 'add_folder.html',
           'edit_folder': 'edit_folder.html',
           'add_host': 'add_host.html',
           'edit_host': 'edit_host.html',
           'add_service': 'add_service.html',
           'delete_service': 'del_service.html',
           'route': 'route.html',
           'admin_group': 'admin_group.html',
           'administrate_group_delete': 'del_group.html',
           'administrate_group_show': 'group.html',
           'administrate_users': 'users.html',
           'administrate_user': 'user.html',
           'change_password': 'change_password.html',
           'logs': 'action.html',
           'access_list': 'access_list.html'}


def check_auth(username, password, client_ip):
    return weblib.login_access(username=username, password=password, engine=webParameters.engine, ip=client_ip)


@app.route('/', methods=['GET'])
@weblib.authorization(session, request, webParameters)
def root():
    search_field = forms.Search()
    if access.check_access(webParameters, 'Administrate'):
        content = weblib.get_admin_content_dashboard(webParameters)
    else:
        content = weblib.get_user_content_dashboard(webParameters)
    return render_template(siteMap['index'],
                           admin=access.check_access(webParameters, 'Administrate'),
                           content=content,
                           search=search_field)


@app.route('/search', methods=['POST'])
@weblib.authorization(session, request, webParameters)
def search():
    form = forms.Search()
    query = form.search.data
    host_list = weblib.search(webParameters, query)
    admin = access.check_access(webParameters, 'Administrate')

    return render_template(siteMap['hosts'],
                           admin=admin,
                           host_list=host_list,
                           Search=query,
                           search=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = forms.Login(meta={'csrf_context': str(request.remote_addr)})
    if request.method == 'POST' and form.validate_on_submit():
        if weblib.login_access(request.form['username'],
                               request.form['password'],
                               request.remote_addr,
                               webParameters.engine):
            session['username'] = request.form['username']
            return redirect(url_for('root'))
        else:
            error = 'Не правильный логин|пароль или учетная запись заблокирована!!!'
    return render_template(siteMap['login'], error=error, form=form)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/settings')
@weblib.authorization(session, request, webParameters)
def settings():
    search_field = forms.Search()
    return render_template(
        siteMap['settings'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field
    )


@app.route('/administrate/logs', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def logs(date=None):
    search_field = forms.Search()
    form = forms.ShowLog()
    form.user.choices = [(0, "Все")]
    for aaa, user in weblib.get_users(webParameters)['users']:
        form.user.choices.append((user.login, user.full_name))

    date = datetime.date.today()
    user = 0
    if request.method == 'POST' and form.validate_on_submit():
        date = form.date.data
        user = form.user.data
    action_list = weblib.get_action(webParameters, user, date)

    return render_template(
        siteMap['logs'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        form=form,
        action_list=action_list
    )


@app.route('/route/<host_id>', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def route(host_id):
    form = forms.AddRoute()
    search_field = forms.Search()
    form.route.choices = weblib.get_route_host(webParameters)

    if request.method == 'POST' and form.add_sub.data:
        r = {
            'host': host_id,
            'route': form.route.data
        }
        weblib.add_route(webParameters, r)

    if request.method == 'POST' and form.clear_sub.data:
        weblib.clear_routes(webParameters, host_id)

    return render_template(siteMap['route'],
                           form=form,
                           admin=access.check_access(webParameters, 'Administrate'),
                           host_id=host_id,
                           routes=weblib.get_routes(webParameters, host_id),
                           search=search_field)


@app.route('/hosts')
@app.route('/hosts/<directory_id>')
@weblib.authorization(session, request, webParameters)
def hosts(directory_id=None):
    form = forms.AddHostGroup()
    search_field = forms.Search()
    form.name.choices = [(t.id, t.name) for t in weblib.get_group_host(webParameters)]
    if directory_id:
        directory_id = int(directory_id)
        edit_host_information = access.check_access(webParameters, 'EditHostInformation',
                                                    h_object=weblib.get_host(webParameters, host_id=directory_id))
        edit_directory = access.check_access(webParameters, 'EditDirectory',
                                             h_object=weblib.get_host(webParameters, host_id=directory_id))
        admin = access.check_access(webParameters, 'Administrate',
                                    h_object=weblib.get_host(webParameters, host_id=directory_id))
        folder = weblib.get_host(webParameters, host_id=directory_id)
        group = ", ".join([t.name for i, t in weblib.get_group_list(webParameters, host=directory_id)])
    else:
        directory_id = 0
        edit_host_information = access.check_access(webParameters, 'EditHostInformation')
        edit_directory = access.check_access(webParameters, 'EditDirectory')
        admin = access.check_access(webParameters, 'Administrate')
        folder = None
        group = None
    host_list = weblib.get_host_list(webParameters, directory_id)
    if folder and folder.note:
        note = json.loads(folder.note)
    else:
        note = None
    return render_template(siteMap['hosts'],
                           admin=admin,
                           host_list=host_list,
                           note=note,
                           form=form,
                           search=search_field,
                           group=group,
                           directory_id=directory_id,
                           EditHostInformation=edit_host_information,
                           EditDirectory=edit_directory)


@app.route('/hosts/<directory_id>/add_folder', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def add_folder(directory_id):
    form = forms.EditFolder()
    search_field = forms.Search()
    error = None
    status = None
    admin = access.check_access(webParameters, 'Administrate',
                                h_object=weblib.get_host(webParameters, host_id=directory_id))

    if request.method == 'POST' and form.add_sub.data:
        folder = {
            'name': form.name.data,
            'describe': form.describe.data,
            'parent': directory_id,
            'prefix': webParameters.user_info.prefix,
            'note': form.note.data
        }
        check_folder = weblib.get_host(webParameters, name=folder['name'], parent=directory_id)
        if check_folder:
            error = 'Имя уже существует'

        if not error:
            if weblib.add_folder(webParameters, folder):
                status = 'Директория добавлена'
            else:
                status = 'Ошибка создания директории'

    return render_template(siteMap['add_folder'],
                           admin=admin,
                           directory_id=directory_id,
                           form=form,
                           error=error,
                           status=status,
                           search=search_field)


@app.route('/hosts/<directory_id>/edit_folder', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def edit_folder(directory_id):
    form = forms.EditFolder()
    search_field = forms.Search()
    h = weblib.get_host(webParameters, host_id=directory_id)
    error = None
    status = None
    admin = access.check_access(webParameters, 'Administrate', h_object=h)

    if request.method == 'GET':
        if not h:
            status = "Невозможно отредактировать данную директорию!!!"
        else:
            form.name.data = h.name
            form.describe.data = h.describe
            form.note.data = h.note

    if request.method == 'POST' and form.edit_sub.data:
        folder = {
            'name': form.name.data,
            'describe': form.describe.data,
            'parent': directory_id,
            'prefix': webParameters.user_info.prefix,
            'note': form.note.data
        }
        check_folder = weblib.get_host(webParameters, name=folder['name'], parent=h.parent)
        if check_folder:
            if int(check_folder.id) != int(directory_id):
                error = 'Имя уже существует'

        if not error:
            if weblib.edit_folder(webParameters, folder, directory_id):
                status = 'Директория отредактирована'
            else:
                status = 'Ошибка редактирования директории'

    elif request.method == 'POST' and form.delete_sub.data:
        weblib.delete_folder(webParameters, directory_id)
        status = "Директория удалена"

    return render_template(siteMap['edit_folder'],
                           admin=admin,
                           directory_id=directory_id,
                           error=error,
                           status=status,
                           form=form,
                           search=search_field)


@app.route('/hosts/<directory_id>/add_host', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def add_host(directory_id):
    form = forms.EditHost()
    search_field = forms.Search()
    folder = weblib.get_host(webParameters, host_id=directory_id)
    form.connection_type.choices = weblib.get_connection_type(webParameters)
    form.file_transfer_type.choices = weblib.get_file_transfer_type(webParameters)
    form.ilo_type.choices = weblib.get_ilo_type(webParameters)
    admin = access.check_access(webParameters, 'Administrate', h_object=folder)
    error = None
    status = None

    if request.method == 'GET':
        form.default_login.data = 'root'
    # TODO: Проверка наличия в базе данных
    if request.method == 'POST' and form.add_sub.data:
        h = schema.Host(
            name=form.name.data,
            ip=form.ip.data,
            tcp_port=form.port.data,
            connection_type=form.connection_type.data,
            file_transfer_type=form.file_transfer_type.data,
            describe=form.describe.data,
            ilo=form.ilo.data,
            ilo_type=form.ilo_type.data,
            default_login=form.default_login.data,
            default_password=form.default_password.data,
            note=form.note.data,
            type=1,
            proxy=form.proxy.data
        )
        weblib.add_host(webParameters, h, parent=directory_id, password=form.default_password.data)
        status = "Хост добавлен"

    if request.method == 'POST' and form.upload_sub.data:
        f = form.file_host.data
        filename = secure_filename(f.filename)
        if not os.path.isdir('/tmp/pyRMA'):
            os.mkdir('/tmp/pyRMA')
        f.save(os.path.join('/tmp/pyRMA', filename))
        try:
            weblib.add_hosts_file(webParameters, os.path.join('/tmp/pyRMA', filename), parent=directory_id)
            status = "Узлы добавлены"
        except rma_error.WTF as e:
            error = e
        finally:
            os.remove(os.path.join('/tmp/pyRMA', filename))

    return render_template(siteMap['add_host'],
                           admin=admin,
                           directory_id=directory_id,
                           error=error,
                           status=status,
                           form=form,
                           search=search_field)


@app.route('/host/<host_id>/edit', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def edit_host(host_id):
    search_field = forms.Search()
    form = forms.EditHost()
    h = weblib.get_host(webParameters, host_id=host_id)
    form.connection_type.choices = weblib.get_connection_type(webParameters)
    form.file_transfer_type.choices = weblib.get_file_transfer_type(webParameters)
    form.ilo_type.choices = weblib.get_ilo_type(webParameters)
    error = None
    status = None
    admin = access.check_access(webParameters, 'Administrate', h_object=h)

    if request.method == 'GET':
        if not h:
            status = "Невозможно отредактировать данный хост!!!"
        else:
            form.name.data = h.name
            form.proxy.data = h.proxy
            form.ip.data = h.ip
            form.port.data = h.tcp_port
            form.ilo.data = h.ilo
            form.describe.data = h.describe
            form.note.data = h.note
            form.default_login.data = h.default_login
            form.default_password.data = h.default_password
            form.connection_type.process_data(h.connection_type)
            form.file_transfer_type.process_data(h.file_transfer_type)
            form.ilo_type.process_data(h.ilo_type)

    if request.method == 'POST' and form.edit_sub.data:
        d = {'name': form.name.data,
             'ip': form.ip.data,
             'port': form.port.data,
             'connection_type': form.connection_type.data,
             'file_transfer_type': form.file_transfer_type.data,
             'describe': form.describe.data,
             'ilo': form.ilo.data,
             'ilo_type': form.ilo_type.data,
             'default_login': form.default_login.data,
             'default_password': form.default_password.data,
             'note': form.note.data,
             'proxy': form.proxy.data
             }
        check_folder = weblib.get_host(webParameters, name=form.name.data, parent=h.parent)
        if check_folder:
            if int(check_folder.id) != int(host_id):
                error = 'Имя уже существует'
        if not error:
            if weblib.edit_host(webParameters, d, host_id):
                return redirect(url_for('host', host_id=host_id))
            else:
                status = 'Ошибка редактирования хоста'

    elif request.method == 'POST' and form.delete_sub.data:
        weblib.delete_host(webParameters, host_id)
        status = "Хост удален"

    return render_template(siteMap['edit_host'],
                           admin=admin,
                           directory_id=h.parent,
                           host_id=h.id,
                           error=error,
                           status=status,
                           form=form,
                           search=search_field)


@app.route('/host/<host_id>')
@weblib.authorization(session, request, webParameters)
def host(host_id):
    if not weblib.check_host(webParameters, host_id):
        return redirect(url_for('hosts', directory_id=host_id))
    search_field = forms.Search()
    form = forms.AddHostGroup()
    form.name.choices = [(t.id, t.name) for t in weblib.get_group_host(webParameters)]
    content_host = weblib.get_content_host(webParameters, host_id)
    if access.check_access(webParameters,
                           'ShowHostInformation',
                           h_object=weblib.get_host(webParameters, host_id=host_id)):
        return render_template(siteMap['host'],
                               admin=access.check_access(webParameters, 'Administrate'),
                               EditHostInformation=access.check_access(webParameters,
                                                                       'EditHostInformation',
                                                                       h_object=weblib.get_host(webParameters,
                                                                                                host_id=host_id)),
                               content=content_host,
                               form=form,
                               search=search_field
                               )
    else:
        return render_template(siteMap['access_denied'])


@app.route('/delete_service/<service_id>', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def del_service(service_id):
    search_field = forms.Search()
    service = weblib.get_service(webParameters, service=service_id)
    if request.method == 'POST':
        weblib.del_service(webParameters, service=service_id)
        return redirect('/host/{service.host}'.format(service=service))
    return render_template(siteMap['delete_service'],
                           admin=access.check_access(webParameters, 'Administrate'),
                           service=service,
                           search=search_field)


@app.route('/host/<host_id>/add_service', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def add_service(host_id):
    search_field = forms.Search()
    edit_host_information = access.check_access(webParameters, 'EditHostInformation',
                                                h_object=weblib.get_host(webParameters, host_id=host_id))
    admin = access.check_access(webParameters, 'Administrate',
                                h_object=weblib.get_host(webParameters, host_id=host_id))
    error = None
    status = None

    if edit_host_information or admin:
        form = forms.AddService()
        form.type.choices = weblib.get_service_type(webParameters)

        if request.method == 'POST' and form.add_sub.data:
            s = schema.Service(
                type=form.type.data,
                host=host_id,
                local_port=weblib.get_local_port(webParameters),
                remote_port=form.remote_port.data,
                remote_ip=form.remote_ip.data,
                internal=form.internal.data,
                describe=form.describe.data
            )

            if weblib.check_ip_net(form.remote_ip.data, '127.0.0.0/8') and not form.internal.data:
                error = 'Не корректное значение "Адрес назначения" или "Внутренний"!!!'
            else:
                if weblib.add_service(webParameters, s):
                    status = 'Сервис добавлен'

        return render_template(siteMap['add_service'],
                               form=form,
                               error=error,
                               status=status,
                               admin=admin,
                               host_id=host_id,
                               search=search_field)
    else:
        return render_template(siteMap['access_denied'])


@app.route('/administrate')
@weblib.authorization(session, request, webParameters)
def administrate():
    search_field = forms.Search()
    return render_template(
        siteMap['administrate'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field
    )


@app.route('/administrate/access', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def administrate_access():
    search_field = forms.Search()
    add_access_form = forms.AddAccess()
    add_access_form.user_group.choices = [(t.id, t.name) for t in weblib.get_group_user(webParameters)]
    add_access_form.host_group.choices = [(0, "ALL")] + [(t.id, t.name) for t in weblib.get_group_host(webParameters)]
    if request.method == 'POST' and add_access_form.validate_on_submit():
        a = schema.AccessList(
            t_subject=1,
            subject=add_access_form.user_group.data,
            t_object=1,
            object=add_access_form.host_group.data,
            date_disable=add_access_form.date.data,
            note=add_access_form.note.data
        )
        weblib.add_access(webParameters, a)

    access_list = weblib.get_access_list(webParameters)
    return render_template(
        siteMap['access_list'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        form=add_access_form,
        access_list=access_list
    )


@app.route('/administrate/group', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def administrate_group():
    search_field = forms.Search()
    form = forms.AddGroup()
    if request.method == 'POST' and form.validate_on_submit():
        g = {
            'name': form.name.data,
            'type': form.type.data
        }

        weblib.add_group(webParameters, g)
    return render_template(siteMap['admin_group'],
                           admin=access.check_access(webParameters, 'Administrate'),
                           form=form,
                           group_user=weblib.get_group_user(webParameters),
                           group_host=weblib.get_group_host(webParameters),
                           search=search_field)


@app.route('/administrate/group/<group_id>', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def administrate_group_show(group_id):
    search_field = forms.Search()
    form = forms.ChangePermission()
    if request.method == 'POST' and form.edit_sub.data:
        weblib.set_group_permission(webParameters, group_id, form)

    content = weblib.get_group(webParameters, group_id)

    if content['permission']:
        form.ShowHostInformation.data = \
            access.check_access(webParameters, 'ShowHostInformation', check_permission=content['permission'])
        form.EditHostInformation.data = \
            access.check_access(webParameters, 'EditHostInformation', check_permission=content['permission'])
        form.EditDirectory.data = \
            access.check_access(webParameters, 'EditDirectory', check_permission=content['permission'])
        form.EditPrefixHost.data = \
            access.check_access(webParameters, 'EditPrefixHost', check_permission=content['permission'])
        form.ShowLogin.data = \
            access.check_access(webParameters, 'ShowLogin', check_permission=content['permission'])
        form.ShowPassword.data = \
            access.check_access(webParameters, 'ShowPassword', check_permission=content['permission'])
        form.ShowAllSession.data = \
            access.check_access(webParameters, 'ShowAllSession', check_permission=content['permission'])
        form.ShowAllGroupSession.data = \
            access.check_access(webParameters, 'ShowAllGroupSession', check_permission=content['permission'])
        form.Administrate.data = \
            access.check_access(webParameters, 'Administrate', check_permission=content['permission'])

        form.Connection.data = \
            access.check_access(webParameters, 'Connection', check_permission=content['permission'])
        form.FileTransfer.data = \
            access.check_access(webParameters, 'FileTransfer', check_permission=content['permission'])
        form.ConnectionService.data = \
            access.check_access(webParameters, 'ConnectionService', check_permission=content['permission'])
        form.ConnectionOnlyService.data = \
            access.check_access(webParameters, 'ConnectionOnlyService', check_permission=content['permission'])
        form.ConnectionIlo.data = \
            access.check_access(webParameters, 'ConnectionIlo', check_permission=content['permission'])

    return render_template(siteMap['administrate_group_show'],
                           content=content,
                           form=form,
                           admin=access.check_access(webParameters, 'Administrate'),
                           search=search_field)


@app.route('/administrate/group/<group_id>/delete', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def administrate_group_delete(group_id):
    search_field = forms.Search()
    if request.method == 'POST':
        weblib.del_group(webParameters, group=group_id)
        return redirect('/administrate/group')
    return render_template(siteMap['administrate_group_delete'],
                           admin=access.check_access(webParameters, 'Administrate'),
                           group_id=group_id,
                           search=search_field)


@app.route('/administrate/users')
@weblib.authorization(session, request, webParameters)
def administrate_users():
    search_field = forms.Search()
    content = weblib.get_users(webParameters)
    return render_template(siteMap['administrate_users'],
                           content=content,
                           cur_date=datetime.datetime.now(),
                           admin=access.check_access(webParameters, 'Administrate'),
                           search=search_field)


@app.route('/administrate/user/<uid>/enable')
@weblib.authorization(session, request, webParameters)
def administrate_user_enable(uid):
    weblib.user_disable(webParameters, uid, enable=True)
    return redirect(request.referrer)


@app.route('/administrate/user/<uid>/disable')
@weblib.authorization(session, request, webParameters)
def administrate_user_disable(uid):
    weblib.user_disable(webParameters, uid, disable=True)
    return redirect(request.referrer)


@app.route('/administrate/user/<uid>/change_password', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def administrate_user_change_password(uid):
    search_field = forms.Search()
    form = forms.UserChangePassword()
    user_info = weblib.get_user(webParameters, uid)['user']
    if request.method == 'POST' and form.validate_on_submit():
        weblib.user_change_password(webParameters, uid, form.password.data)
        return redirect(url_for('administrate_user', uid=uid))
    print(form.is_submitted(), form.validate())
    print(form.errors)
    return render_template(siteMap['change_password'],
                           form=form,
                           user=user_info,
                           admin=access.check_access(webParameters, 'Administrate'),
                           search=search_field)


@app.route('/administrate/user/<uid>', methods=['GET', 'POST'])
@weblib.authorization(session, request, webParameters)
def administrate_user(uid):
    search_field = forms.Search()
    group_user_form = forms.AddUserGroup()
    prefix_form = forms.ChangePrefix()
    group_user_form.name.choices = [(t.id, t.name) for t in weblib.get_group_user(webParameters)]
    prefix_form.prefix.choices = [(t.id, t.name) for t in weblib.get_prefix(webParameters)]
    if request.method == 'POST' and group_user_form.validate_on_submit():
        weblib.add_user_group(webParameters, uid, group_user_form.name.data)
    if request.method == 'POST' and prefix_form.sub.data and prefix_form.validate_on_submit():
        prefix = None
        for t in weblib.get_prefix(webParameters):
            if t.id == prefix_form.prefix.data:
                prefix = t.name
                break
        weblib.set_user_prefix(webParameters, prefix, uid)
    return render_template(siteMap['administrate_user'],
                           content=weblib.get_user(webParameters, uid),
                           group_user_form=group_user_form,
                           prefix_form=prefix_form,
                           cur_date=datetime.datetime.now(),
                           admin=access.check_access(webParameters, 'Administrate'),
                           search=search_field)


@app.route('/administrate/user/<user>/group/<group>/delete')
@weblib.authorization(session, request, webParameters)
def administrate_user_group_delete(user, group):
    weblib.del_group_user(webParameters, group=group, user=user)
    return redirect(request.referrer)


@app.route('/administrate/host/<host_id>/group/<group>/delete')
@weblib.authorization(session, request, webParameters)
def administrate_host_group_delete(host_id, group):
    weblib.del_group_host(webParameters, group=group, host=host_id)
    return redirect(request.referrer)


@app.route('/administrate/host/<host_id>', methods=['POST'])
@weblib.authorization(session, request, webParameters)
def administrate_host(host_id):
    form = forms.AddHostGroup()
    if request.method == 'POST' and form.add_sub.data:
        weblib.add_host_group(webParameters, host_id, form.name.data)
    return redirect(request.referrer)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    status = None
    error = None
    form = forms.Registration()
    if request.method == 'POST' and form.validate_on_submit():
        registration_data = {'username': form.login.data,
                             'password': form.password.data,
                             'full_name': form.full_name.data,
                             'email': form.email.data,
                             'ip': form.ip.data}
        if weblib.user_registration(registration_data, webParameters.engine):
            status = 'Пользователь создан.'
        else:
            error = 'Во время создания пользователя произошла ошибка!'

    return render_template(siteMap['registration'], status=status, error=error, form=form)


@app.route('/restore', methods=['GET', 'POST'])
def get_restore():
    form = forms.ResetPassword()
    if request.method == 'POST' and form.validate_on_submit():
        if weblib.restore_password(form.login.data, webParameters.engine, request):
            status = "Инструкции отправлены"
            return render_template(siteMap['restore'], status=status)
        else:
            status = "Error!!!"
            return render_template(siteMap['restore'], status=status)

    return render_template(siteMap['restore'], form=form)


@app.route('/restore/<key>', methods=['GET', 'POST'])
def restore(key):
    form = forms.UserChangePassword()
    status = None
    if request.method == 'GET':
        if not weblib.reset_password(key, webParameters.engine, check=True):
            render_template(siteMap['404']), 404
    elif request.method == 'POST':
        if form.validate_on_submit():
            if weblib.reset_password(key, webParameters.engine, password=request.form['password']):
                status = 'Password reset'
            else:
                status = 'Error reset'
    return render_template(siteMap['reset password'], key=key, form=form, status=status)


if webParameters.template is not None:
    app.run(host=webParameters.ip, port=webParameters.port)
else:
    print('Not set template!!!')
