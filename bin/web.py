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
from pyrmalib import schema, parameters, pyrmalib, access, forms, error as rma_error
import os.path
from sqlalchemy import create_engine
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
app = Flask(__name__,
            template_folder=webParameters.template,
            static_folder=os.path.join(webParameters.template, 'static'))
app.secret_key = os.urandom(64)
app.debug = True
csrf = CSRFProtect()
csrf.init_app(app)

webParameters.log.info('start app')
print(webParameters.log.handler)

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
           'access_list': 'access_list.html',
           'error': 'error.html',
           'settings_del_prefix': 'del_prefix.html',
           'change_ipmi': 'change_ipmi.html',
           'settings_del_ipmi': 'del_ipmi.html',
           'settings_ipmi': 'settings_ipmi.html',
           'settings_prefix': 'settings_prefix.html',
           'settings_service': 'settings_service.html',
           'settings_del_service': 'del_service_type.html',}


def check_auth(username, password, client_ip):
    return pyrmalib.login_access(username=username, password=password, engine=webParameters.engine, ip=client_ip)


@app.route('/', methods=['GET'])
@pyrmalib.authorization(session, request, webParameters)
def root():
    search_field = forms.Search()
    if access.check_access(webParameters, 'Administrate'):
        content = pyrmalib.get_admin_content_dashboard(webParameters)
    else:
        content = pyrmalib.get_user_content_dashboard(webParameters)
    return render_template(siteMap['index'],
                           admin=access.check_access(webParameters, 'Administrate'),
                           content=content,
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/search', methods=['POST'])
@pyrmalib.authorization(session, request, webParameters)
def search():
    form = forms.Search()
    query = form.search.data
    host_list = pyrmalib.search(webParameters, query)
    admin = access.check_access(webParameters, 'Administrate')

    return render_template(siteMap['hosts'],
                           admin=admin,
                           host_list=host_list,
                           Search=query,
                           search=form,
                           username=webParameters.aaa_user.username)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = forms.Login(meta={'csrf_context': str(request.remote_addr)})
    if request.method == 'POST' and form.validate_on_submit():
        if pyrmalib.login_access(request.form['username'],
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


@app.route('/settings', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def settings():
    search_field = forms.Search()
    parameters_form = forms.Parameters()
    if request.method == 'POST' and parameters_form.validate_on_submit():
        pyrmalib.set_parameters(webParameters, 'EMAIL_HOST', str(parameters_form.email_host.data))
        pyrmalib.set_parameters(webParameters, 'EMAIL_PORT', str(parameters_form.email_port.data))
        pyrmalib.set_parameters(webParameters, 'EMAIL_FROM', str(parameters_form.email_from.data))
        pyrmalib.set_parameters(webParameters, 'EMAIL_CC', str(parameters_form.email_cc.data))
        if parameters_form.auto_extension.data:
            pyrmalib.set_parameters(webParameters, 'AUTO_EXTENSION', '1')
        else:
            pyrmalib.set_parameters(webParameters, 'AUTO_EXTENSION', '0')
        pyrmalib.set_parameters(webParameters, 'EXTENSION_DAYS', str(parameters_form.extension_days.data))
        if parameters_form.enable_route_map.data:
            pyrmalib.set_parameters(webParameters, 'ENABLE_ROUTE_MAP', '1')
        else:
            pyrmalib.set_parameters(webParameters, 'ENABLE_ROUTE_MAP', '0')
        if parameters_form.check_ip.data:
            pyrmalib.set_parameters(webParameters, 'CHECK_IP', '1')
        else:
            pyrmalib.set_parameters(webParameters, 'CHECK_IP', '0')
        pyrmalib.set_parameters(
            webParameters,
            'FORWARD_TCP_PORT_DISABLE',
            str(parameters_form.forward_tcp_port_disable.data)
        )
        pyrmalib.set_parameters(
            webParameters,
            'FORWARD_TCP_PORT_RANGE',
            str(parameters_form.forward_tcp_port_range.data)
        )
    parameters_table = pyrmalib.get_parameters(webParameters)
    parameters_form.email_host.data = list(filter(lambda x: x.name == 'EMAIL_HOST', parameters_table))[0].value
    parameters_form.email_port.data = list(filter(lambda x: x.name == 'EMAIL_PORT', parameters_table))[0].value
    parameters_form.email_from.data = list(filter(lambda x: x.name == 'EMAIL_FROM', parameters_table))[0].value
    parameters_form.email_cc.data = list(filter(lambda x: x.name == 'EMAIL_CC', parameters_table))[0].value
    if list(filter(lambda x: x.name == 'AUTO_EXTENSION', parameters_table))[0].value == '1':
        parameters_form.auto_extension.data = True
    parameters_form.extension_days.data = list(filter(lambda x: x.name == 'EXTENSION_DAYS', parameters_table))[0].value
    if list(filter(lambda x: x.name == 'ENABLE_ROUTE_MAP', parameters_table))[0].value == '1':
        parameters_form.enable_route_map.data = True
    if list(filter(lambda x: x.name == 'CHECK_IP', parameters_table))[0].value == '1':
        parameters_form.check_ip.data = True
    parameters_form.forward_tcp_port_disable.data = list(filter(
        lambda x: x.name == 'FORWARD_TCP_PORT_DISABLE',
        parameters_table
    ))[0].value
    parameters_form.forward_tcp_port_range.data = list(filter(
        lambda x: x.name == 'FORWARD_TCP_PORT_RANGE',
        parameters_table
    ))[0].value
    return render_template(
        siteMap['settings'],
        parameters_form=parameters_form,
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        username=webParameters.aaa_user.username
    )


@app.route('/settings/service', methods=['GET'])
@pyrmalib.authorization(session, request, webParameters)
def settings_service():
    search_field = forms.Search()
    form_add_service = forms.AddService()
    service = pyrmalib.get_service_type(webParameters, raw=True)
    return render_template(
        siteMap['settings_service'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        service=service,
        form_add_service=form_add_service,
        username=webParameters.aaa_user.username
    )


@app.route('/settings/prefix', methods=['GET'])
@pyrmalib.authorization(session, request, webParameters)
def settings_prefix():
    search_field = forms.Search()
    form_add_prefix = forms.AddPrefix()
    prefix = pyrmalib.get_prefix(webParameters)
    return render_template(
        siteMap['settings_prefix'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        prefix=prefix,
        form_add_prefix=form_add_prefix,
        username=webParameters.aaa_user.username
    )


@app.route('/settings/ipmi', methods=['GET'])
@pyrmalib.authorization(session, request, webParameters)
def settings_ipmi():
    search_field = forms.Search()
    form_add_ipmi = forms.IPMI()
    ipmi = pyrmalib.get_ilo_type(webParameters, raw=True)
    return render_template(
        siteMap['settings_ipmi'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        ipmi=ipmi,
        form_add_ipmi=form_add_ipmi,
        username=webParameters.aaa_user.username
    )


@app.route('/settings/add/ipmi', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def settings_ipmi_add():
    form_add_ipmi = forms.IPMI()
    if request.method == 'POST' and form_add_ipmi.validate_on_submit():
        pyrmalib.add_ipmi(
            webParameters,
            form_add_ipmi.name.data,
            form_add_ipmi.vendor.data,
            form_add_ipmi.ports.data
        )
    return redirect('/settings/ipmi')


@app.route('/settings/add/prefix', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def settings_prefix_add():
    form_add_prefix = forms.AddPrefix()
    if request.method == 'POST' and form_add_prefix.validate_on_submit():
        pyrmalib.add_prefix(
            webParameters,
            form_add_prefix.name.data,
            form_add_prefix.describe.data
        )
    return redirect('/settings/prefix')


@app.route('/settings/delete/ipmi/<ipmi_id>', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def settings_ipmi_delete(ipmi_id):
    del_button = forms.DelButton()
    search_field = forms.Search()
    ipmi = pyrmalib.get_ilo_type(webParameters, ipmi_id=ipmi_id, raw=True)
    if request.method == 'POST' and del_button.validate_on_submit():
        pyrmalib.del_ipmi(webParameters, ipmi_id)
        return redirect('/settings/ipmi')
    return render_template(
        siteMap['settings_del_ipmi'],
        admin=access.check_access(webParameters, 'Administrate'),
        del_button=del_button,
        search=search_field,
        ipmi=ipmi,
        username=webParameters.aaa_user.username
    )


@app.route('/settings/delete/prefix/<prefix_id>', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def settings_prefix_delete(prefix_id):
    prefix = pyrmalib.get_prefix(webParameters, prefix_id=prefix_id)
    del_button = forms.DelButton()
    search_field = forms.Search()
    if request.method == 'POST' and del_button.validate_on_submit():
        pyrmalib.del_prefix(webParameters, prefix_id)
        return redirect('/settings/prefix')
    return render_template(
        siteMap['settings_del_prefix'],
        admin=access.check_access(webParameters, 'Administrate'),
        del_button=del_button,
        search=search_field,
        prefix=prefix,
        username=webParameters.aaa_user.username
    )


@app.route('/settings/delete/service/<service_id>', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def settings_service_delete(service_id):
    service = pyrmalib.get_service_type(webParameters, service_type_id=service_id)
    del_button = forms.DelButton()
    search_field = forms.Search()
    if request.method == 'POST' and del_button.validate_on_submit():
        pyrmalib.del_service_type(webParameters, service_id)
        return redirect('/settings/service')
    return render_template(
        siteMap['settings_del_service'],
        admin=access.check_access(webParameters, 'Administrate'),
        del_button=del_button,
        search=search_field,
        service=service,
        username=webParameters.aaa_user.username
    )



@app.route('/settings/change/ipmi/<ipmi_id>', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def settings_ipmi_change(ipmi_id):
    search_field = forms.Search()
    ipmi = pyrmalib.get_ilo_type(webParameters, ipmi_id=ipmi_id, raw=True)
    form = forms.IPMI()
    if request.method == 'POST' and form.validate_on_submit():
        data = {
            'name': form.name.data,
            'vendor': form.vendor.data,
            'ports': form.ports.data
        }
        print(data)
        pyrmalib.change_ipmi(webParameters, ipmi_id, data)
        return redirect('/settings/ipmi')
    form.name.data = ipmi.name
    form.vendor.data = ipmi.vendor
    form.ports.data = ipmi.ports
    form.sub.label.text = 'Изменить'
    return render_template(
        siteMap['change_ipmi'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        form=form,
        ipmi=ipmi
    )


@app.route('/administrate/logs', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def logs(date=None):
    search_field = forms.Search()
    form = forms.ShowLog()
    form.user.choices = [(0, "Все")]
    for aaa, user in pyrmalib.get_users(webParameters)['users']:
        form.user.choices.append((user.login, user.full_name))

    date = datetime.date.today()
    user = 0
    if request.method == 'POST' and form.validate_on_submit():
        date = form.date.data
        user = form.user.data
    action_list = pyrmalib.get_action(webParameters, user, date)

    return render_template(
        siteMap['logs'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        form=form,
        action_list=action_list,
        username=webParameters.aaa_user.username
    )


@app.route('/route/<host_id>', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def route(host_id):
    form = forms.AddRoute()
    search_field = forms.Search()
    form.route.choices = pyrmalib.get_route_host(webParameters)

    if request.method == 'POST' and form.add_sub.data:
        r = {
            'host': host_id,
            'route': form.route.data
        }
        pyrmalib.add_route(webParameters, r)

    if request.method == 'POST' and form.clear_sub.data:
        pyrmalib.clear_routes(webParameters, host_id)

    return render_template(siteMap['route'],
                           form=form,
                           admin=access.check_access(webParameters, 'Administrate'),
                           host_id=host_id,
                           routes=pyrmalib.get_routes(webParameters, host_id),
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/hosts')
@app.route('/hosts/<directory_id>')
@pyrmalib.authorization(session, request, webParameters)
def hosts(directory_id=None):
    form = forms.AddHostGroup()
    search_field = forms.Search()
    if pyrmalib.get_group_host(webParameters):
        form.name.choices = [(t.id, t.name) for t in pyrmalib.get_group_host(webParameters)]
    else:
        form = False
    if directory_id:
        directory_id = int(directory_id)
        edit_host_information = access.check_access(webParameters, 'EditHostInformation',
                                                    h_object=pyrmalib.get_host(webParameters, host_id=directory_id))
        edit_directory = access.check_access(webParameters, 'EditDirectory',
                                             h_object=pyrmalib.get_host(webParameters, host_id=directory_id))
        admin = access.check_access(webParameters, 'Administrate',
                                    h_object=pyrmalib.get_host(webParameters, host_id=directory_id))
        folder = pyrmalib.get_host(webParameters, host_id=directory_id)
        group = ", ".join([t.name for i, t in pyrmalib.get_group_list(webParameters, host=directory_id)])
    else:
        directory_id = 0
        edit_host_information = access.check_access(webParameters, 'EditHostInformation')
        edit_directory = access.check_access(webParameters, 'EditDirectory')
        admin = access.check_access(webParameters, 'Administrate')
        folder = None
        group = None
    host_list = pyrmalib.get_host_list(webParameters, directory_id)
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
                           EditDirectory=edit_directory,
                           username=webParameters.aaa_user.username)


@app.route('/hosts/<directory_id>/add_folder', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def add_folder(directory_id):
    form = forms.EditFolder()
    search_field = forms.Search()
    error = None
    status = None
    admin = access.check_access(webParameters, 'Administrate',
                                h_object=pyrmalib.get_host(webParameters, host_id=directory_id))

    if request.method == 'POST' and form.add_sub.data:
        folder = {
            'name': form.name.data,
            'describe': form.describe.data,
            'parent': directory_id,
            'prefix': webParameters.user_info.prefix,
            'note': form.note.data
        }
        check_folder = pyrmalib.get_host(webParameters, name=folder['name'], parent=directory_id)
        if check_folder:
            error = 'Имя уже существует'

        if not error:
            if pyrmalib.add_folder(webParameters, folder):
                status = 'Директория добавлена'
            else:
                status = 'Ошибка создания директории'

    return render_template(siteMap['add_folder'],
                           admin=admin,
                           directory_id=directory_id,
                           form=form,
                           error=error,
                           status=status,
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/hosts/<directory_id>/edit_folder', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def edit_folder(directory_id):
    form = forms.EditFolder()
    search_field = forms.Search()
    h = pyrmalib.get_host(webParameters, host_id=directory_id)
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
        check_folder = pyrmalib.get_host(webParameters, name=folder['name'], parent=h.parent)
        if check_folder:
            if int(check_folder.id) != int(directory_id):
                error = 'Имя уже существует'

        if not error:
            if pyrmalib.edit_folder(webParameters, folder, directory_id):
                status = 'Директория отредактирована'
            else:
                status = 'Ошибка редактирования директории'

    elif request.method == 'POST' and form.delete_sub.data:
        pyrmalib.delete_folder(webParameters, directory_id)
        status = "Директория удалена"

    return render_template(siteMap['edit_folder'],
                           admin=admin,
                           directory_id=directory_id,
                           error=error,
                           status=status,
                           form=form,
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/hosts/<directory_id>/add_host', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def add_host(directory_id):
    form = forms.EditHost()
    search_field = forms.Search()
    folder = pyrmalib.get_host(webParameters, host_id=directory_id)
    form.connection_type.choices = pyrmalib.get_connection_type(webParameters)
    form.file_transfer_type.choices = pyrmalib.get_file_transfer_type(webParameters)
    form.ilo_type.choices = pyrmalib.get_ilo_type(webParameters)
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
        pyrmalib.add_host(webParameters, h, parent=directory_id, password=form.default_password.data)
        status = "Хост добавлен"

    if request.method == 'POST' and form.upload_sub.data:
        f = form.file_host.data
        filename = secure_filename(f.filename)
        if not os.path.isdir('/tmp/pyRMA'):
            os.mkdir('/tmp/pyRMA')
        f.save(os.path.join('/tmp/pyRMA', filename))
        try:
            pyrmalib.add_hosts_file(webParameters, os.path.join('/tmp/pyRMA', filename), parent=directory_id)
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
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/host/<host_id>/edit', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def edit_host(host_id):
    search_field = forms.Search()
    form = forms.EditHost()
    h = pyrmalib.get_host(webParameters, host_id=host_id)
    form.connection_type.choices = pyrmalib.get_connection_type(webParameters)
    form.file_transfer_type.choices = pyrmalib.get_file_transfer_type(webParameters)
    form.ilo_type.choices = pyrmalib.get_ilo_type(webParameters)
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
        check_folder = pyrmalib.get_host(webParameters, name=form.name.data, parent=h.parent)
        if check_folder:
            if int(check_folder.id) != int(host_id):
                error = 'Имя уже существует'
        if not error:
            if pyrmalib.edit_host(webParameters, d, host_id):
                return redirect(url_for('host', host_id=host_id))
            else:
                status = 'Ошибка редактирования хоста'

    elif request.method == 'POST' and form.delete_sub.data:
        pyrmalib.delete_host(webParameters, host_id)
        status = "Хост удален"

    return render_template(siteMap['edit_host'],
                           admin=admin,
                           directory_id=h.parent,
                           host_id=h.id,
                           error=error,
                           status=status,
                           form=form,
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/host/<host_id>')
@pyrmalib.authorization(session, request, webParameters)
def host(host_id):
    if not pyrmalib.check_host(webParameters, host_id):
        return redirect(url_for('hosts', directory_id=host_id))
    search_field = forms.Search()
    form = forms.AddHostGroup()
    if pyrmalib.get_group_host(webParameters):
        form.name.choices = [(t.id, t.name) for t in pyrmalib.get_group_host(webParameters)]
    else:
        form = False
    content_host = pyrmalib.get_content_host(webParameters, host_id)
    if access.check_access(webParameters,
                           'ShowHostInformation',
                           h_object=pyrmalib.get_host(webParameters, host_id=host_id)):
        return render_template(
            siteMap['host'],
            admin=access.check_access(webParameters, 'Administrate'),
            EditHostInformation=access.check_access(webParameters,
                                                    'EditHostInformation',
                                                    h_object=pyrmalib.get_host(webParameters, host_id=host_id)),
            content=content_host,
            form=form,
            search=search_field,
            username=webParameters.aaa_user.username
        )
    else:
        return render_template(siteMap['access_denied'])


@app.route('/delete_service/<service_id>', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def del_service(service_id):
    search_field = forms.Search()
    service = pyrmalib.get_service(webParameters, service=service_id)
    if request.method == 'POST':
        pyrmalib.del_service(webParameters, service=service_id)
        return redirect('/host/{service.host}'.format(service=service))
    return render_template(siteMap['delete_service'],
                           admin=access.check_access(webParameters, 'Administrate'),
                           service=service,
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/host/<host_id>/add_service', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def add_service(host_id):
    search_field = forms.Search()
    edit_host_information = access.check_access(webParameters, 'EditHostInformation',
                                                h_object=pyrmalib.get_host(webParameters, host_id=host_id))
    admin = access.check_access(webParameters, 'Administrate',
                                h_object=pyrmalib.get_host(webParameters, host_id=host_id))
    error = None
    status = None

    if edit_host_information or admin:
        form = forms.AddServiceHost()
        form.type.choices = pyrmalib.get_service_type(webParameters)

        if request.method == 'POST' and form.add_sub.data:
            s = schema.Service(
                type=form.type.data,
                host=host_id,
                local_port=pyrmalib.get_local_port(webParameters),
                remote_port=form.remote_port.data,
                remote_ip=form.remote_ip.data,
                internal=form.internal.data,
                describe=form.describe.data
            )

            if pyrmalib.check_ip_net(form.remote_ip.data, '127.0.0.0/8') and not form.internal.data:
                error = 'Не корректное значение "Адрес назначения" или "Внутренний"!!!'
            else:
                if pyrmalib.add_service(webParameters, s):
                    status = 'Сервис добавлен'

        return render_template(siteMap['add_service'],
                               form=form,
                               error=error,
                               status=status,
                               admin=admin,
                               host_id=host_id,
                               search=search_field,
                               username=webParameters.aaa_user.username)
    else:
        return render_template(siteMap['access_denied'])


@app.route('/administrate')
@pyrmalib.authorization(session, request, webParameters)
def administrate():
    search_field = forms.Search()
    return render_template(
        siteMap['administrate'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        username=webParameters.aaa_user.username
    )


@app.route('/administrate/access', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def administrate_access():
    search_field = forms.Search()
    if not pyrmalib.get_group_user(webParameters):
        return render_template(siteMap['error'], error="Не созданы группы пользователей!!!")
    add_access_form = forms.AddAccess()
    add_access_form.user_group.choices = [(t.id, t.name) for t in pyrmalib.get_group_user(webParameters)]
    if pyrmalib.get_group_host(webParameters):
        add_access_form.host_group.choices = [(0, "ALL")] + [(t.id, t.name)
                                                             for t in pyrmalib.get_group_host(webParameters)]
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
        pyrmalib.add_access(webParameters, a)

    access_list = pyrmalib.get_access_list(webParameters)
    return render_template(
        siteMap['access_list'],
        admin=access.check_access(webParameters, 'Administrate'),
        search=search_field,
        form=add_access_form,
        access_list=access_list,
        cur_date=datetime.datetime.now(),
        username=webParameters.aaa_user.username
    )


@app.route('/administrate/access/delete/<aid>')
@pyrmalib.authorization(session, request, webParameters)
def administrate_access_delete(aid):
    pyrmalib.del_access(webParameters, aid)
    return redirect(request.referrer)


@app.route('/administrate/group', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def administrate_group():
    search_field = forms.Search()
    form = forms.AddGroup()
    if request.method == 'POST' and form.validate_on_submit():
        g = {
            'name': form.name.data,
            'type': form.type.data
        }

        pyrmalib.add_group(webParameters, g)
    return render_template(siteMap['admin_group'],
                           admin=access.check_access(webParameters, 'Administrate'),
                           form=form,
                           group_user=pyrmalib.get_group_user(webParameters),
                           group_host=pyrmalib.get_group_host(webParameters),
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/administrate/group/<group_id>', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def administrate_group_show(group_id):
    search_field = forms.Search()
    form = forms.ChangePermission()
    if request.method == 'POST' and form.edit_sub.data:
        pyrmalib.set_group_permission(webParameters, group_id, form)

    content = pyrmalib.get_group(webParameters, group_id)

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
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/administrate/group/<group_id>/delete', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def administrate_group_delete(group_id):
    search_field = forms.Search()
    del_button = forms.DelButton()
    if request.method == 'POST' and del_button.validate_on_submit():
        pyrmalib.del_group(webParameters, group=group_id)
        return redirect('/administrate/group')
    return render_template(siteMap['administrate_group_delete'],
                           admin=access.check_access(webParameters, 'Administrate'),
                           del_button=del_button,
                           group_id=group_id,
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/administrate/users')
@pyrmalib.authorization(session, request, webParameters)
def administrate_users():
    search_field = forms.Search()
    content = pyrmalib.get_users(webParameters)
    return render_template(siteMap['administrate_users'],
                           content=content,
                           cur_date=datetime.datetime.now(),
                           admin=access.check_access(webParameters, 'Administrate'),
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/administrate/user/<uid>/enable')
@pyrmalib.authorization(session, request, webParameters)
def administrate_user_enable(uid):
    pyrmalib.user_disable(webParameters, uid, enable=True)
    return redirect(request.referrer)


@app.route('/administrate/user/<uid>/disable')
@pyrmalib.authorization(session, request, webParameters)
def administrate_user_disable(uid):
    pyrmalib.user_disable(webParameters, uid, disable=True)
    return redirect(request.referrer)


@app.route('/administrate/user/<uid>/change_password', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def administrate_user_change_password(uid):
    search_field = forms.Search()
    form = forms.UserChangePassword()
    user_info = pyrmalib.get_user(webParameters, uid)['user']
    if request.method == 'POST' and form.validate_on_submit():
        pyrmalib.user_change_password(webParameters, uid, form.password.data)
        return redirect(url_for('administrate_user', uid=uid))
    print(form.is_submitted(), form.validate())
    print(form.errors)
    return render_template(siteMap['change_password'],
                           form=form,
                           user=user_info,
                           admin=access.check_access(webParameters, 'Administrate'),
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/administrate/user/<uid>', methods=['GET', 'POST'])
@pyrmalib.authorization(session, request, webParameters)
def administrate_user(uid):
    search_field = forms.Search()
    prefix_form = forms.ChangePrefix()
    if pyrmalib.get_group_user(webParameters):
        group_user_form = forms.AddUserGroup()
        group_user_form.name.choices = [(t.id, t.name) for t in pyrmalib.get_group_user(webParameters)]
    else:
        group_user_form = False
    prefix_form.prefix.choices = [(t.id, t.name) for t in pyrmalib.get_prefix(webParameters)]
    if pyrmalib.get_group_user(webParameters):
        if request.method == 'POST' and group_user_form.validate_on_submit():
            pyrmalib.add_user_group(webParameters, uid, group_user_form.name.data)
    if request.method == 'POST' and prefix_form.sub.data and prefix_form.validate_on_submit():
        prefix = None
        for t in pyrmalib.get_prefix(webParameters):
            if t.id == prefix_form.prefix.data:
                prefix = t.name
                break
        pyrmalib.set_user_prefix(webParameters, prefix, uid)
    return render_template(siteMap['administrate_user'],
                           content=pyrmalib.get_user(webParameters, uid),
                           group_user_form=group_user_form,
                           prefix_form=prefix_form,
                           cur_date=datetime.datetime.now(),
                           admin=access.check_access(webParameters, 'Administrate'),
                           search=search_field,
                           username=webParameters.aaa_user.username)


@app.route('/administrate/user/<user>/group/<group>/delete')
@pyrmalib.authorization(session, request, webParameters)
def administrate_user_group_delete(user, group):
    pyrmalib.del_group_user(webParameters, group=group, user=user)
    return redirect(request.referrer)


@app.route('/administrate/host/<host_id>/group/<group>/delete')
@pyrmalib.authorization(session, request, webParameters)
def administrate_host_group_delete(host_id, group):
    pyrmalib.del_group_host(webParameters, group=group, host=host_id)
    return redirect(request.referrer)


@app.route('/administrate/host/<host_id>', methods=['POST'])
@pyrmalib.authorization(session, request, webParameters)
def administrate_host(host_id):
    form = forms.AddHostGroup()
    if request.method == 'POST' and form.add_sub.data:
        pyrmalib.add_host_group(webParameters, host_id, form.name.data)
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
        if pyrmalib.user_registration(registration_data, webParameters.engine):
            status = 'Пользователь создан.'
        else:
            error = 'Во время создания пользователя произошла ошибка!'

    return render_template(siteMap['registration'], status=status, error=error, form=form)


@app.route('/restore', methods=['GET', 'POST'])
def get_restore():
    form = forms.ResetPassword()
    if request.method == 'POST' and form.validate_on_submit():
        if pyrmalib.restore_password(form.login.data, webParameters.engine, request):
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
        if not pyrmalib.reset_password(key, webParameters.engine, check=True):
            render_template(siteMap['404']), 404
    elif request.method == 'POST':
        if form.validate_on_submit():
            if pyrmalib.reset_password(key, webParameters.engine, password=request.form['password']):
                status = 'Password reset'
            else:
                status = 'Error reset'
    return render_template(siteMap['reset password'], key=key, form=form, status=status)


if webParameters.template is not None:
    app.run(host=webParameters.ip, port=webParameters.port)
else:
    print('Not set template!!!')
