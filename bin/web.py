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

from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from flask_wtf.csrf import CSRFProtect
from pyrmalib import schema, parameters, applib, access, forms, error as rma_error
import os
import pwd
from sqlalchemy import create_engine, sql
from werkzeug.utils import secure_filename

webParameters = parameters.WebParameters()
webParameters.engine = create_engine(
    '{0}://{1}:{2}@{3}:{4}/{5}'.format(
        webParameters.dbase,
        webParameters.dbase_param["user"],
        webParameters.dbase_param["password"],
        webParameters.dbase_param["host"],
        webParameters.dbase_param["port"],
        webParameters.dbase_param["database"]
    )
)
app = Flask(
    __name__,
    template_folder=webParameters.template,
    static_folder=os.path.join(webParameters.template, 'static')
)
app.secret_key = os.urandom(64)
app.debug = True    # TODO: Снять DEBUG
csrf = CSRFProtect()
csrf.init_app(app)

# Создание пользователя администратор.
pw_name, pw_passwd, pw_uid, pw_gid, pw_gecos, pw_dir, pw_shell = pwd.getpwuid(os.getuid())
if not applib.user_info(pw_name, webParameters.engine):
    applib.user_registration(
        {
            'uid': pw_uid,
            'login': pw_name,
            'full_name': pw_gecos,
            'ip': '0.0.0.0/0',
            'email': "{}@{}".format(pw_name, webParameters.email['domain_name']),
            'check': 1,
            'admin': True
        },
        webParameters
    )

webParameters.log.info('start app')
print(webParameters.log.handler)

siteMap = {
    'index': 'index.html',
    'connection': 'connection.html',
    'connections': 'connections.html',
    '404': '404.html',
    'error': 'error.html',
    'access_denied': 'access_denied.html',
    'hosts': 'hosts.html',
    'host': 'host.html',
    'login': 'login.html',
    'add_folder': 'add_folder.html',
    'edit_folder': 'edit_folder.html',
    'add_host': 'add_host.html',
    'edit_host': 'edit_host.html',
    'add_service': 'add_service.html',
    'delete_service': 'del_service.html',
    'logs': 'action.html',
    'access_list': 'access_list.html',
    'change_ipmi': 'change_ipmi.html',
    'access': 'access.html',
    'administrate': 'administrate.html',
    'administrate_users': 'users.html',
    'administrate_user': 'user.html',
    'administrate_group': 'administrate_group.html',
    'administrate_group_show': 'group.html',
    'administrate_group_delete': 'del_group.html',
    'administrate_ipmi': 'administrate_ipmi.html',
    'administrate_del_ipmi': 'del_ipmi.html',
    'administrate_prefix': 'administrate_prefix.html',
    'administrate_del_prefix': 'del_prefix.html',
    'administrate_service': 'administrate_service.html',
    'administrate_del_service': 'del_service_type.html'
}


def check_auth(username, password, client_ip):
    return applib.login_access(username=username, password=password, engine=webParameters.engine, ip=client_ip)


@app.route('/', methods=['GET'])
@applib.authorization(session, request, webParameters)
def root():
    search_field = forms.Search()
    if webParameters.user_info.admin:
        content = applib.get_admin_content_dashboard(webParameters)
    else:
        content = applib.get_user_content_dashboard(webParameters)
    return render_template(
        siteMap['index'],
        admin=webParameters.user_info.admin,
        content=content,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/connection', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def connections():
    search_field = forms.Search()
    filter_field = forms.ConnectionFilter()

    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    if request.method == 'POST' and filter_field.validate_on_submit():
        message = "Подключения за {}".format(filter_field.date.data)
        connection = applib.get_connections(webParameters,date=filter_field.date.data)
    else:
        message = 'Подключения за последние сутки'
        connection = applib.get_connections(webParameters)

    return render_template(
        siteMap['connections'],
        admin=webParameters.user_info.admin,
        search=search_field,
        username=webParameters.user_info.login,
        connections=connection,
        message=message,
        filter_field=filter_field
    )


@app.route('/ttyrec/<path:path>')
@applib.authorization(session, request, webParameters)
def ttyrec(path):
    return send_from_directory(webParameters.data_dir, path)

@app.route('/file/<path:path>')
@applib.authorization(session, request, webParameters)
def file(path):
    return send_from_directory(webParameters.data_dir, path)

@app.route('/pcap/<path:path>')
@applib.authorization(session, request, webParameters)
def capture(path):
    return send_from_directory(webParameters.data_dir, path)


@app.route('/connection/<connection_id>', methods=['GET'])
@applib.authorization(session, request, webParameters)
def connection(connection_id=None):
    search_field = forms.Search()

    content = applib.get_connection(webParameters, connection_id)

    if not webParameters.user_info.admin \
        and not applib.access.check_access(webParameters, 'ShowAllSession', h_object=content['host']):
        return render_template(siteMap['access_denied'])

    return render_template(
        siteMap['connection'],
        admin=webParameters.user_info.admin,
        search=search_field,
        username=webParameters.user_info.login,
        content=content
    )


@app.route('/search', methods=['POST'])
@applib.authorization(session, request, webParameters)
def search():
    form = forms.Search()
    query = form.search.data
    host_list = applib.search(webParameters, query)
    admin = webParameters.user_info.admin

    return render_template(
        siteMap['hosts'],
        admin=admin,
        host_list=host_list,
        Search=query,
        search=form,
        username=webParameters.user_info.login
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = forms.Login(meta={'csrf_context': str(request.remote_addr)})
    if request.method == 'POST' and form.validate_on_submit():
        if applib.login_access(request.form['username'],
                               request.form['password'],
                               request.remote_addr,
                               webParameters):
            session['username'] = request.form['username']
            return redirect(url_for('root'))
        else:
            error = 'Не правильный логин|пароль или учетная запись заблокирована!!!'
    return render_template(siteMap['login'], error=error, form=form)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/administrate/logs', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def logs(date=None):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    search_field = forms.Search()
    form = forms.ShowLog()
    form.user.choices = [(0, "Все")]
    for user in applib.get_users(webParameters)['users']:
        form.user.choices.append((user.uid, user.full_name))

    date = datetime.date.today()
    user = 0
    if request.method == 'POST' and form.validate_on_submit():
        date = form.date.data
        user = form.user.data
    action_list = applib.get_action(webParameters, user, date)

    return render_template(
        siteMap['logs'],
        admin=webParameters.user_info.admin,
        search=search_field,
        form=form,
        action_list=action_list,
        username=webParameters.user_info.login
    )



@app.route('/hosts')
@app.route('/hosts/<directory_id>', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def hosts(directory_id=None):
    group_form = forms.AddHostGroup()
    jump_form = forms.JumpHost()
    search_field = forms.Search()
    admin = webParameters.user_info.admin
    
    if request.method == 'POST' and jump_form.add_sub.data:
        applib.add_jump(
            webParameters,
            {
                'host': directory_id,
                'jump': jump_form.jump.data
            }
        )
    
    if request.method == 'POST' and jump_form.clear_sub.data:
        applib.clear_jump(webParameters, directory_id)
    
    if applib.get_group_host(webParameters):
        group_form.name.choices = [(t.id, t.name) for t in applib.get_group_host(webParameters)]
    else:
        group_form = False
    
    if applib.get_jump_hosts(webParameters):
        jump_form.jump.choices = applib.get_jump_hosts(webParameters)
    else:
        jump_form = False
    
    if directory_id:
        directory_id = int(directory_id)
        edit_host_information = access.check_access(
            webParameters, 'EditHostInformation',
            h_object=applib.get_host(webParameters, host_id=directory_id)
        ) or webParameters.user_info.admin
        edit_directory = access.check_access(
            webParameters, 'EditDirectory',
            h_object=applib.get_host(webParameters, host_id=directory_id)
        ) or webParameters.user_info.admin
        folder = applib.get_host(webParameters, host_id=directory_id)
        group = ", ".join([t.name for i, t in applib.get_group_list(webParameters, host=directory_id)])
    else:
        directory_id = 0
        edit_host_information = access.check_access(webParameters, 'EditHostInformation') or webParameters.user_info.admin
        edit_directory = access.check_access(webParameters, 'EditDirectory') or webParameters.user_info.admin
        folder = None
        group = None
    host_list = applib.get_host_list(webParameters, directory_id)
    if folder and folder.note:
        note = json.loads(folder.note)
    else:
        note = None
    return render_template(
        siteMap['hosts'],
        admin=admin,
        host_list=host_list,
        note=note,
        jump = applib.get_jump_host(webParameters, directory_id),
        jump_form=jump_form,
        search=search_field,
        group=group,
        group_form=group_form,
        directory_id=directory_id,
        EditHostInformation=edit_host_information,
        EditDirectory=edit_directory,
        username=webParameters.user_info.login
    )


@app.route('/hosts/<directory_id>/add_folder', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def add_folder(directory_id):
    form = forms.EditFolder()
    search_field = forms.Search()
    error = None
    status = None

    if request.method == 'POST' and form.add_sub.data:
        folder = {
            'name': form.name.data,
            'describe': form.describe.data,
            'parent': directory_id,
            'prefix': webParameters.user_info.prefix,
            'note': form.note.data
        }
        check_folder = applib.get_host(webParameters, name=folder['name'], parent=directory_id)
        if check_folder:
            error = 'Имя уже существует'

        if not error:
            if applib.add_folder(webParameters, folder):
                return redirect(url_for('hosts', directory_id=directory_id))
            else:
                status = 'Ошибка создания директории'

    return render_template(
        siteMap['add_folder'],
        admin=webParameters.user_info.admin,
        directory_id=directory_id,
        form=form,
        error=error,
        status=status,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/hosts/<directory_id>/edit_folder', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def edit_folder(directory_id):
    form = forms.EditFolder()
    search_field = forms.Search()
    h = applib.get_host(webParameters, host_id=directory_id)
    error = None
    status = None

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
        check_folder = applib.get_host(webParameters, name=folder['name'], parent=h.parent)
        if check_folder:
            if int(check_folder.id) != int(directory_id):
                error = 'Имя уже существует'

        if not error:
            if applib.edit_folder(webParameters, folder, directory_id):
                return redirect(url_for('hosts', directory_id=directory_id))
            else:
                status = 'Ошибка редактирования директории'

    elif request.method == 'POST' and form.delete_sub.data:
        applib.delete_folder(webParameters, directory_id)
        status = "Директория удалена"

    return render_template(
        siteMap['edit_folder'],
        admin=webParameters.user_info.admin,
        directory_id=directory_id,
        error=error,
        status=status,
        form=form,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/hosts/<directory_id>/add_host', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def add_host(directory_id):
    form = forms.EditHost()
    search_field = forms.Search()
    folder = applib.get_host(webParameters, host_id=directory_id)
    form.connection_type.choices = applib.get_connection_type(webParameters)
    form.file_transfer_type.choices = applib.get_file_transfer_type(webParameters)
    form.ilo_type.choices = applib.get_ilo_type(webParameters)
    error = None
    status = None

    if request.method == 'GET':
        form.default_login.data = 'root'
    if request.method == 'POST' and form.add_sub.data:
        h = schema.Host(
            name=form.name.data,
            ip=form.ip.data,
            tcp_port=form.port.data if form.port.data else sql.null(),
            connection_type=form.connection_type.data,
            file_transfer_type=form.file_transfer_type.data if form.file_transfer_type.data != 'None' else sql.null(),
            describe=form.describe.data,
            ilo=form.ilo.data,
            ilo_type=form.ilo_type.data if form.ilo_type.data != 'None' else sql.null(),
            default_login=form.default_login.data,
            default_password=form.default_password.data,
            note=form.note.data,
            type=1,
            proxy=form.proxy.data
        )
        applib.add_host(webParameters, h, parent=directory_id, password=form.default_password.data)
        return redirect(url_for('hosts', directory_id=directory_id))

    if request.method == 'POST' and form.upload_sub.data:
        f = form.file_host.data
        filename = secure_filename(f.filename)
        if not os.path.isdir('/tmp/pyRMA'):
            os.mkdir('/tmp/pyRMA')
        f.save(os.path.join('/tmp/pyRMA', filename))
        try:
            applib.add_hosts_file(webParameters, os.path.join('/tmp/pyRMA', filename), parent=directory_id)
            status = "Узлы добавлены"
            return redirect(url_for('hosts', directory_id=directory_id))
        except rma_error.WTF as e:
            error = e
        finally:
            os.remove(os.path.join('/tmp/pyRMA', filename))

    return render_template(
        siteMap['add_host'],
        admin=webParameters.user_info.admin,
        directory_id=directory_id,
        error=error,
        status=status,
        form=form,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/host/<host_id>/edit', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def edit_host(host_id):
    search_field = forms.Search()
    form = forms.EditHost()
    h = applib.get_host(webParameters, host_id=host_id)
    form.connection_type.choices = applib.get_connection_type(webParameters)
    form.file_transfer_type.choices = applib.get_file_transfer_type(webParameters)
    form.ilo_type.choices = applib.get_ilo_type(webParameters)
    error = None
    status = None

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
        d = {
            'name': form.name.data,
            'ip': form.ip.data,
            'port': form.port.data,
            'connection_type': form.connection_type.data,
            'file_transfer_type': form.file_transfer_type.data if form.file_transfer_type.data != 'None' else sql.null(),
            'describe': form.describe.data,
            'ilo': form.ilo.data,
            'ilo_type': form.ilo_type.data if form.ilo_type.data != 'None' else sql.null(),
            'default_login': form.default_login.data,
            'default_password': form.default_password.data,
            'note': form.note.data,
            'proxy': form.proxy.data
        }
        check_folder = applib.get_host(webParameters, name=form.name.data, parent=h.parent)
        if check_folder:
            if int(check_folder.id) != int(host_id):
                error = 'Имя уже существует'
        if not error:
            if applib.edit_host(webParameters, d, host_id):
                return redirect(url_for('host', host_id=host_id))
            else:
                status = 'Ошибка редактирования хоста'

    elif request.method == 'POST' and form.delete_sub.data:
        applib.delete_host(webParameters, host_id)
        return redirect(url_for('hosts', directory_id=h.parent))

    return render_template(
        siteMap['edit_host'],
        admin=webParameters.user_info.admin,
        directory_id=h.parent,
        host_id=h.id,
        error=error,
        status=status,
        form=form,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/host/<host_id>', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def host(host_id):
    jump_form = forms.JumpHost()
    if request.method == 'POST' and jump_form.add_sub.data:
        applib.add_jump(
            webParameters,
            {
                'host': host_id,
                'jump': jump_form.jump.data
            }
        )
    
    if request.method == 'POST' and jump_form.clear_sub.data:
        applib.clear_jump(webParameters, host_id)

    if applib.get_jump_hosts(webParameters):
        jump_form.jump.choices = applib.get_jump_hosts(webParameters)
    else:
        jump_form = False
    
    if not applib.check_host(webParameters, host_id):
        return redirect(url_for('hosts', directory_id=host_id))
    
    search_field = forms.Search()
    group_form = forms.AddHostGroup()
    connection_filter = forms.ConnectionFilter()

    cdate = None
    if request.method == 'POST' and connection_filter.validate_on_submit():
        cdate = connection_filter.date.data
    
    if applib.get_group_host(webParameters):
        group_form.name.choices = [(t.id, t.name) for t in applib.get_group_host(webParameters)]
    else:
        group_form = False
    
    object_host = applib.get_host(webParameters, host_id=host_id)
    content_host = applib.get_content_host(webParameters, host_id, connection_date=cdate)
    show_host_info = access.check_access(webParameters, 'ShowHostInformation', h_object=object_host)
    admin = webParameters.user_info.admin
    if show_host_info or admin:
        return render_template(
            siteMap['host'],
            admin=admin,
            EditHostInformation=access.check_access(
                webParameters,
                'EditHostInformation',
                h_object=object_host
            ) or webParameters.user_info.admin,
            content=content_host,
            jump = applib.get_jump_host(webParameters, host_id),
            jump_form=jump_form,
            group_form=group_form,
            search=search_field,
            connection_filter=connection_filter,
            username=webParameters.user_info.login
        )
    else:
        return render_template(siteMap['access_denied'])


@app.route('/delete_service/<service_id>', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def del_service(service_id):
    search_field = forms.Search()
    del_button = forms.DelButton()
    service = applib.get_service(webParameters, service=service_id)
    if request.method == 'POST' and del_button.validate_on_submit():
        applib.del_service(webParameters, service=service_id)
        return redirect('/host/{service.host}'.format(service=service))
    return render_template(
        siteMap['delete_service'],
        admin=webParameters.user_info.admin,
        service=service,
        del_button=del_button,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/host/<host_id>/add_service', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def add_service(host_id):
    search_field = forms.Search()
    host = applib.get_host(webParameters, host_id=host_id)
    edit_host_information = access.check_access(
        webParameters, 'EditHostInformation',
        h_object=host
    )
    admin = webParameters.user_info.admin
    error = None

    if edit_host_information or admin:
        form = forms.AddServiceHost()
        form.type.choices = applib.get_service_type(webParameters)
        form.remote_ip.choices = [host.ip, '127.0.0.1']

        if request.method == 'POST' and form.add_sub.data:
            service_type = applib.get_service_type(webParameters, service_type_id=form.type.data)
            
            s = schema.Service(
                type=form.type.data,
                host=host_id,
                local_port=applib.get_local_port(webParameters),
                remote_port=service_type.default_port,
                remote_ip=form.remote_ip.data,
                describe=form.describe.data
            )

            if applib.add_service(webParameters, s):
                return redirect(url_for('host', host_id=host_id))

        return render_template(
            siteMap['add_service'],
            form=form,
            error=error,
            admin=admin,
            host_id=host_id,
            search=search_field,
            username=webParameters.user_info.login
        )
    else:
        return render_template(siteMap['access_denied'])


@app.route('/administrate')
@applib.authorization(session, request, webParameters)
def administrate():
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    search_field = forms.Search()
    return render_template(
        siteMap['administrate'],
        admin=webParameters.user_info.admin,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/administrate/service', methods=['GET'])
@applib.authorization(session, request, webParameters)
def administrate_service():
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    search_field = forms.Search()
    form_add_service = forms.AddService()
    service = applib.get_service_type(webParameters, raw=True)
    return render_template(
        siteMap['administrate_service'],
        admin=webParameters.user_info.admin,
        search=search_field,
        service=service,
        form_add_service=form_add_service,
        username=webParameters.user_info.login
    )


@app.route('/administrate/ipmi', methods=['GET'])
@applib.authorization(session, request, webParameters)
def administrate_ipmi():
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    search_field = forms.Search()
    form_add_ipmi = forms.IPMI()
    ipmi = applib.get_ilo_type(webParameters, raw=True)
    return render_template(
        siteMap['administrate_ipmi'],
        admin=webParameters.user_info.admin,
        search=search_field,
        ipmi=ipmi,
        form_add_ipmi=form_add_ipmi,
        username=webParameters.user_info.login
    )


@app.route('/administrate/add/ipmi', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_ipmi_add():
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    form_add_ipmi = forms.IPMI()
    if request.method == 'POST' and form_add_ipmi.validate_on_submit():
        applib.add_ipmi(
            webParameters,
            form_add_ipmi.name.data,
            form_add_ipmi.vendor.data,
            form_add_ipmi.ports.data
        )
    return redirect('/administrate/ipmi')


@app.route('/administrate/add/prefix', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_prefix_add():
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    form_add_prefix = forms.AddPrefix()
    if request.method == 'POST' and form_add_prefix.validate_on_submit():
        applib.add_prefix(
            webParameters,
            form_add_prefix.name.data,
            form_add_prefix.describe.data
        )
    return redirect('/administrate/prefix')


@app.route('/administrate/add/service', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_service_add():
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    form_add_service = forms.AddService()
    if request.method == 'POST' and form_add_service.validate_on_submit():
        try:
            applib.add_service_type(
                webParameters,
                form_add_service.name.data,
                form_add_service.default_port.data
            )
        except rma_error.InsertError as e:
            return render_template(
                siteMap['error'],
                error=e
            )
    return redirect('/administrate/service')


@app.route('/administrate/delete/ipmi/<ipmi_id>', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_ipmi_delete(ipmi_id):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    del_button = forms.DelButton()
    search_field = forms.Search()
    ipmi = applib.get_ilo_type(webParameters, ipmi_id=ipmi_id, raw=True)
    if request.method == 'POST' and del_button.validate_on_submit():
        applib.del_ipmi(webParameters, ipmi_id)
        return redirect('/administrate/ipmi')
    return render_template(
        siteMap['administrate_del_ipmi'],
        admin=webParameters.user_info.admin,
        del_button=del_button,
        search=search_field,
        ipmi=ipmi,
        username=webParameters.user_info.login
    )


@app.route('/administrate/delete/service/<service_id>', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_service_delete(service_id):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    service = applib.get_service_type(webParameters, service_type_id=service_id)
    del_button = forms.DelButton()
    search_field = forms.Search()
    if request.method == 'POST' and del_button.validate_on_submit():
        applib.del_service_type(webParameters, service_id)
        return redirect('/administrate/service')
    return render_template(
        siteMap['administrate_del_service'],
        admin=webParameters.user_info.admin,
        del_button=del_button,
        search=search_field,
        service=service,
        username=webParameters.user_info.login
    )


@app.route('/administrate/change/ipmi/<ipmi_id>', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_ipmi_change(ipmi_id):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    search_field = forms.Search()
    ipmi = applib.get_ilo_type(webParameters, ipmi_id=ipmi_id, raw=True)
    form = forms.IPMI()
    if request.method == 'POST' and form.validate_on_submit():
        data = {
            'name': form.name.data,
            'vendor': form.vendor.data,
            'ports': form.ports.data
        }
        print(data)
        applib.change_ipmi(webParameters, ipmi_id, data)
        return redirect('/administrate/ipmi')
    form.name.data = ipmi.name
    form.vendor.data = ipmi.vendor
    form.ports.data = ipmi.ports
    form.sub.label.text = 'Изменить'
    return render_template(
        siteMap['change_ipmi'],
        admin=webParameters.user_info.admin,
        search=search_field,
        form=form,
        ipmi=ipmi
    )


@app.route('/administrate/access', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_access():
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    search_field = forms.Search()
    if not applib.get_group_user(webParameters):
        return render_template(siteMap['error'], error="Не созданы группы пользователей!!!")
    add_access_form = forms.AddAccess()
    add_access_form.user_group.choices = [(t.id, t.name) for t in applib.get_group_user(webParameters)]
    if applib.get_group_host(webParameters):
        add_access_form.host_group.choices = [(0, "ALL")] + [(t.id, t.name)
                                                             for t in applib.get_group_host(webParameters)]
    else:
        add_access_form.host_group.choices = [(0, "ALL")]
    if request.method == 'POST' and add_access_form.validate_on_submit():
        a = schema.AccessList(
            t_subject=1,
            subject=add_access_form.user_group.data,
            t_object=1,
            object=add_access_form.host_group.data,
            date_disable=add_access_form.date.data,
            note=add_access_form.note.data,
            status=1
        )
        applib.add_access(webParameters, a)

    access_list = applib.get_access_list(webParameters)
    return render_template(
        siteMap['access_list'],
        admin=webParameters.user_info.admin,
        search=search_field,
        form=add_access_form,
        access_list=access_list,
        cur_date=datetime.datetime.now(),
        username=webParameters.user_info.login
    )


@app.route('/administrate/access/delete/<aid>')
@applib.authorization(session, request, webParameters)
def administrate_access_delete(aid):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    applib.del_access(webParameters, aid)
    return redirect(request.referrer)


@app.route('/administrate/group', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_group():
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    search_field = forms.Search()
    form = forms.AddGroup()
    if request.method == 'POST' and form.validate_on_submit():
        g = {
            'name': form.name.data,
            'type': form.type.data
        }

        applib.add_group(webParameters, g)
    return render_template(
        siteMap['administrate_group'],
        admin=webParameters.user_info.admin,
        form=form,
        group_user=applib.get_group_user(webParameters),
        group_host=applib.get_group_host(webParameters),
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/administrate/group/<group_id>', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_group_show(group_id):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    search_field = forms.Search()
    form = forms.ChangePermission()
    if request.method == 'POST' and form.edit_sub.data:
        applib.set_group_permission(webParameters, group_id, form)

    content = applib.get_group(webParameters, group_id)

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
        form.AccessRequest.data = \
            access.check_access(webParameters, 'AccessRequest', check_permission=content['permission'])
        form.EditCredential.data = \
            access.check_access(webParameters, 'EditCredential', check_permission=content['permission'])

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

    return render_template(
        siteMap['administrate_group_show'],
        content=content,
        form=form,
        admin=webParameters.user_info.admin,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/administrate/group/<group_id>/delete', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_group_delete(group_id):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    search_field = forms.Search()
    del_button = forms.DelButton()
    if request.method == 'POST' and del_button.validate_on_submit():
        applib.del_group(webParameters, group=group_id)
        return redirect('/administrate/group')
    return render_template(
        siteMap['administrate_group_delete'],
        admin=webParameters.user_info.admin,
        del_button=del_button,
        group_id=group_id,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/administrate/users')
@applib.authorization(session, request, webParameters)
def administrate_users():
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    search_field = forms.Search()
    content = applib.get_users(webParameters)
    return render_template(
        siteMap['administrate_users'],
        content=content,
        cur_date=datetime.datetime.now(),
        admin=webParameters.user_info.admin,
        search=search_field,
        username=webParameters.user_info.login
    )


@app.route('/administrate/user/<uid>/enable')
@applib.authorization(session, request, webParameters)
def administrate_user_enable(uid):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    if webParameters.user_info.admin:
        applib.user_disable(webParameters, uid, enable=True)
    return redirect(request.referrer)


@app.route('/administrate/user/<uid>/disable')
@applib.authorization(session, request, webParameters)
def administrate_user_disable(uid):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    if webParameters.user_info.admin:
        applib.user_disable(webParameters, uid, disable=True)
    return redirect(request.referrer)


@app.route('/administrate/user/<uid>/enable_admin')
@applib.authorization(session, request, webParameters)
def administrate_user_enable_admin(uid):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    if webParameters.user_info.admin:
        applib.user_admin_disable(webParameters, uid, enable=True)
    return redirect(request.referrer)


@app.route('/administrate/user/<uid>/disable_admin')
@applib.authorization(session, request, webParameters)
def administrate_user_disable_admin(uid):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    if webParameters.user_info.admin:
        applib.user_admin_disable(webParameters, uid, disable=True)
    return redirect(request.referrer)


@app.route('/administrate/user/<uid>', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def administrate_user(uid):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    search_field = forms.Search()
    connection_filter = forms.ConnectionFilter()
    user_form = forms.User()

    cdate = None
    if request.method == 'POST' and connection_filter.validate_on_submit():
        cdate = connection_filter.date.data

    if request.method == 'POST' and user_form.validate_on_submit():
        applib.user_edit(webParameters, uid, user_form.email.data, user_form.ip.data)

    content = applib.get_user(webParameters, uid, connection_date=cdate)
    user_form.email.data = content['user'].email
    user_form.ip.data = content['user'].ip
    
    if applib.get_group_user(webParameters):
        group_user_form = forms.AddUserGroup()
        group_user_form.name.choices = [(t.id, t.name) for t in applib.get_group_user(webParameters)]
    else:
        group_user_form = False
    if applib.get_group_user(webParameters):
        if request.method == 'POST' and group_user_form.validate_on_submit():
            applib.add_user_group(webParameters, uid, group_user_form.name.data)
    return render_template(
        siteMap['administrate_user'],
        content=content,
        group_user_form=group_user_form,
        user_form=user_form,
        cur_date=datetime.datetime.now(),
        admin=webParameters.user_info.admin,
        search=search_field,
        connection_filter=connection_filter,
        username=webParameters.user_info.login
    )


@app.route('/administrate/user/<user>/group/<group>/delete')
@applib.authorization(session, request, webParameters)
def administrate_user_group_delete(user, group):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    applib.del_group_user(webParameters, group=group, user=user)
    return redirect(request.referrer)


@app.route('/administrate/host/<host_id>/group/<group>/delete')
@applib.authorization(session, request, webParameters)
def administrate_host_group_delete(host_id, group):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])

    applib.del_group_host(webParameters, group=group, host=host_id)
    return redirect(request.referrer)


@app.route('/administrate/host/<host_id>', methods=['POST'])
@applib.authorization(session, request, webParameters)
def administrate_host(host_id):
    if not webParameters.user_info.admin:
        return render_template(siteMap['access_denied'])
    
    form = forms.AddHostGroup()
    if request.method == 'POST' and form.add_sub.data:
        applib.add_host_group(webParameters, host_id, form.name.data)
    return redirect(request.referrer)


@app.route('/access/<id_access>/<command>', methods=['GET', 'POST'])
@applib.authorization(session, request, webParameters)
def acc(id_access, command):
    form = forms.Access()
    if command == 'access':
        title = 'Согласовать доступ'
    elif command == 'deny':
        title = 'Отказать в доступе'
    else:
        return render_template(siteMap['404']), 404

    access_list = applib.get_access_request(webParameters, acc_id=id_access)
    if len(access_list) != 1:
        return render_template(siteMap['error']), 404

    form.data_access.data = access_list[0]['access'].date_access
    form.connection.data = access_list[0]['access'].connection
    form.file_transfer.data = access_list[0]['access'].file_transfer
    form.ipmi.data = access_list[0]['access'].ipmi

    if request.method == 'POST' and form.sub.data:
        if command == 'access':
            access_list[0]['access'].date_access = form.data_access.data
            access_list[0]['access'].connection = form.connection.data
            access_list[0]['access'].file_transfer = form.file_transfer.data
            access_list[0]['access'].ipmi = form.ipmi.data
            access.access_request(webParameters, access_list[0])
        elif command == 'deny':
            access.deny_request(webParameters, access_list[0])
        return redirect(url_for('root'))

    return render_template(
        siteMap['access'],
        admin=webParameters.user_info.admin,
        title=title,
        access=access_list[0],
        current_url=request.full_path,
        form=form
    )


if webParameters.template is not None:
    app.run(host=webParameters.ip, port=webParameters.port)
else:
    print('Not set template!!!')
