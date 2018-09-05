# coding=utf-8
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

import weakref
import datetime
import npyscreen
import curses.ascii
from pyrmalib import schema, template, utils


class MultiLineEditableBoxed(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEditable


class ButtonLine(npyscreen.FixedText):
    def display(self, *args, **keywords):
        self.value = 'Используйте F1 для просмотра списка команд.'


class RecordList(npyscreen.MultiLineAction):
    def display_value(self, vl: schema.Host):
        if type(vl) is schema.Host:
            if vl.type == 2:
                return '\t[{0:<20}]\t\t{1}'.format(vl.name, vl.describe if vl.describe else '')
            elif vl.type == 1:
                return '\t {0:<20} \t\t{1}'.format(vl.name, vl.describe if vl.describe else '')
        else:
            return '\t{0:<20}'.format('..')

    def actionHighlighted(self, act_on_this: schema.Host, key_press):
        if type(act_on_this) is schema.Host:
            if act_on_this.type == 2:
                self.parent.Level.append(act_on_this.id)
                self.parent.Filter = ''
                self.parent.History.append(self.cursor_line)
                self.cursor_line = 0
                self.parent.update_list()
            elif act_on_this.type == 1:
                connection_form = ConnectionForm(host=act_on_this, color='GOOD')
                connection_form.edit()
                pass
        else:
            self.parent.Filter = ''
            self.parent.Level.pop()
            self.cursor_line = self.parent.History.pop()
            self.parent.update_list()

    def h_cursor_beginning(self, ch):
        super().h_cursor_beginning(ch)
        self.parent.SelectHost = self.values[self.cursor_line]

    def h_cursor_end(self, ch):
        super().h_cursor_end(ch)
        self.parent.SelectHost = self.values[self.cursor_line]

    def h_cursor_page_down(self, ch):
        super().h_cursor_page_down(ch)
        self.parent.SelectHost = self.values[self.cursor_line]

    def h_cursor_page_up(self, ch):
        super().h_cursor_page_up(ch)
        self.parent.SelectHost = self.values[self.cursor_line]

    def h_cursor_line_up(self, ch):
        super().h_cursor_line_up(ch)
        self.parent.SelectHost = self.values[self.cursor_line]

    def h_cursor_line_down(self, ch):
        super().h_cursor_line_down(ch)
        self.parent.SelectHost = self.values[self.cursor_line]

    def handle_mouse_event(self, mouse_event):
        super().handle_mouse_event(mouse_event)
        self.parent.SelectHost = self.values[self.cursor_line]

    def update(self, clear=True):
        super().update(clear)
        self.parent.SelectHost = self.values[self.cursor_line]

    def move_next_filtered(self, include_this_line=False, *args):
        super().move_next_filtered(include_this_line, *args)
        self.parent.SelectHost = self.values[self.cursor_line]

    def move_previous_filtered(self, *args):
        super().move_previous_filtered(*args)
        self.parent.SelectHost = self.values[self.cursor_line]


class HostListDisplay(npyscreen.FormMutt):
    MAIN_WIDGET_CLASS = RecordList
    COMMAND_WIDGET_CLASS = ButtonLine
    Level = [0]
    History = []
    Filter = ''
    SelectHost = None  # scheme.Host
    HostList = None

    def beforeEditing(self):
        self.wStatus1.value = ' {0} - {1} '.format(appParameters.program,
                                                   appParameters.version)
        self.wStatus2.value = ' Управление: '
        self.keypress_timeout = 30
        self.update_list()

        self.add_handlers({'^Q': self.app_exit,
                           '+': self.filter,
                           'i': self.show_host_information,
                           # 'd': self.add_folder,
                           # 'e': self.edit_element,
                           # 'a': self.add_host
                           })

        self.help = template.help_main_form().format(program=appParameters.program,
                                                     version=appParameters.version)

    def update_list(self):
        if appParameters.user_info.permissions.get('Administrate'):
            with schema.db_select(appParameters.engine) as db:
                self.HostList = db.query(schema.Host).filter(schema.Host.parent == self.Level[-1]). \
                    filter(schema.Host.name.like('%{0}%'.format(self.Filter))). \
                    order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
        else:
            with schema.db_select(appParameters.engine) as db:
                self.HostList = db.query(schema.Host). \
                    filter(schema.Host.prefix.in_(appParameters.user_info.prefix)). \
                    filter(schema.Host.parent == self.Level[-1]). \
                    filter(schema.Host.name.like('%{0}%'.format(self.Filter))). \
                    order_by(schema.Host.type.desc()).order_by(schema.Host.name.desc()).all()

        appParameters.log.debug(self.HostList)

        if len(self.Level) == 1:
            self.wMain.values = self.HostList
        else:
            self.wMain.values = ['back'] + self.HostList
        self.wMain.display()
        self.wCommand.display()

    def app_exit(self, *args, **keywords):
        appParameters.log.debug('Выход из интерфейса.')
        self.parentApp.switchForm(None)

    def filter(self, *args, **keywords):
        filter_form = Filter()
        filter_form.owner = weakref.proxy(self)
        filter_form.display()
        filter_form.FilterText.edit()
        del filter_form
        self.update_list()

    def add_host(self, *args, **keywords):
        if appParameters.user_info.permissions.get('EditHostInformation') or \
                appParameters.user_info.permissions.get('Administrate'):
            appParameters.log.debug('def add_host: self.level[-1] = {0}'.format(self.Level[-1]))
            self.parentApp.addForm('HOST', HostFormEdit)
            self.parentApp.getForm('HOST').Parent = self.Level[-1]
            self.parentApp.switchForm('HOST')
        else:
            npyscreen.notify_confirm('Нет прав доступа для операции', title='Ошибка', form_color='DANGER')

    def add_folder(self, *args, **keywords):
        if appParameters.user_info.permissions.get('EditDirectory') or \
                appParameters.user_info.permissions.get('Administrate'):
            appParameters.log.debug('def add_folder: self.level[-1] = {0}'.format(self.Level[-1]))
            self.parentApp.addForm('FOLDER', FolderForm)
            self.parentApp.getForm('FOLDER').Parent = self.Level[-1]
            self.parentApp.switchForm('FOLDER')
        else:
            npyscreen.notify_confirm('Нет прав доступа для операции', title='Ошибка', form_color='DANGER')

    def edit_element(self, *args, **keywords):
        if self.SelectHost.type == 2:
            if appParameters.user_info.permissions.get('EditDirectory') or \
                    appParameters.user_info.permissions.get('Administrate'):
                appParameters.log.debug('def edit_element: SelectHost = {0}'.format(self.SelectHost.id))
                self.parentApp.addForm('FOLDER', FolderForm)
                self.parentApp.getForm('FOLDER').Parent = self.Level[-1]
                self.parentApp.getForm('FOLDER').Edit = self.SelectHost.id
                self.parentApp.switchForm('FOLDER')
            else:
                npyscreen.notify_confirm('Нет прав доступа для операции', title='Ошибка', form_color='DANGER')
        elif self.SelectHost.type == 1:
            if appParameters.user_info.permissions.get('EditHostInformation') or \
                    appParameters.user_info.permissions.get('Administrate'):
                appParameters.log.debug('def edit_element: SelectHost = {0}'.format(self.SelectHost.id))
                self.parentApp.addForm('HOST', HostFormEdit)
                self.parentApp.getForm('HOST').SelectHost = self.SelectHost
                self.parentApp.getForm('HOST').fill_values()
                self.parentApp.switchForm('HOST')

    def delete_element(self, *args, **keywords):
        pass

    def show_host_information(self, *args, **keywords):
        if appParameters.user_info.permissions.get('ShowHostInformation') or \
                appParameters.user_info.permissions.get('Administrate'):
            host_form_information = npyscreen.Form(self.SelectHost.name)
            host_form_information.add(npyscreen.TitleFixedText, name='Имя хоста:', value=self.SelectHost.name)
            host_form_information.add(npyscreen.TitleFixedText, name="IP адрес:", value=self.SelectHost.ip)
            host_form_information.add(npyscreen.TitleFixedText, name="Описание:", value=self.SelectHost.describe)
            host_form_information.how_exited_handers[
                npyscreen.wgwidget.EXITED_ESCAPE] = host_form_information.exit_editing
            host_form_information.display()
            host_form_information.edit()
        pass


class HostFormEdit(npyscreen.ActionFormV2):
    Parent = 0
    SelectHost = None
    Route = []
    Service = []

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.add_handlers({'^Q': self.on_cancel})

        with schema.db_select(appParameters.engine) as db:
            self.ctype = db.query(schema.ConnectionType).all()
            self.itype = db.query(schema.IloType).all()
        self.ctype_names = []
        if len(self.ctype) > 0:
            for i in self.ctype:
                self.ctype_names.append(i.name)
        else:
            # Защита от пустого списка.
            self.ctype_names.append('None')

        self.itype_names = []

        if len(self.itype) > 0:
            for i in self.itype:
                self.itype_names.append(i.name)
            self.itype_name = self.itype_names[0]
        else:
            # Защита от пустого списка.
            self.itype_name = None
            self.itype_names.append('None')

        self.HostName = self.add(npyscreen.TitleText, name='Имя хоста', labelColor='VERYGOOD')
        self.Description = self.add(npyscreen.TitleText, name='Description')
        self.HostIP = self.add(npyscreen.TitleText, name='IP адрес', labelColor='VERYGOOD')
        if self.itype_names[0] == 'None':
            self.HostILO = self.add(npyscreen.TitleText, name='IP адрес ILO')
            self.HostILO.value = 'Не поддерживается'
            self.HostILO.editable = False
        else:
            self.HostILO = self.add(npyscreen.TitleText, name='IP адрес {}'.format(self.itype_names[0]))
            self.HostILO.add_handlers({curses.ascii.NL: self.select_itype,
                                       curses.ascii.CR: self.select_itype})
            self.HostILO.labelColor = 'CONTROL'

        self.Login = self.add(npyscreen.TitleText, name='Логин')
        self.Password = self.add(npyscreen.TitleText, name='Пароль')

        self.ConnectionTypeButton = self.add(npyscreen.TitleFixedText,
                                             name='Тип подключения',
                                             use_two_lines=False)

        self.ConnectionTypeButton.add_handlers({curses.ascii.NL: self.select_ctype,
                                                curses.ascii.CR: self.select_ctype})
        self.ConnectionTypeButton.value = self.ctype_names[0]
        self.ConnectionTypeButton.labelColor = 'CONTROL'
        self.nextrely += 1

        self.ServiceList = self.add(npyscreen.ButtonPress,
                                    name='Сервисы',
                                    when_pressed_function=self.service_list)
        if list(filter(lambda x: x.name == 'ENABLE_ROUTE_MAP', appParameters.table_parameter))[0].value == '1':
            self.RouteMapButton = self.add(npyscreen.ButtonPress,
                                           name='Маршрут',
                                           when_pressed_function=self.route_map,
                                           rely=self.ServiceList.rely,
                                           relx=self.ServiceList.relx + self.ServiceList.label_width + 2)
        self.nextrely += 1
        self.Note = self.add(MultiLineEditableBoxed, name='Описание узла', scroll_exit=True, editable=True)

    def fill_values(self, *args, **keywords):
        self.HostName.value = self.SelectHost.name
        self.Description.value = self.SelectHost.describe
        if self.SelectHost.tcp_port is not None:
            self.HostIP.value = str("{}:{}".format(self.SelectHost.ip, self.SelectHost.tcp_port)).lstrip(':')
        else:
            self.HostIP.value = self.SelectHost.ip
        self.HostILO.value = self.SelectHost.ilo
        self.Login.value = self.SelectHost.default_login
        self.Password.value = self.SelectHost.default_password
        self.Note.values = self.SelectHost.note
        self.ConnectionTypeButton.value = self.ctype_names[self.SelectHost.connection_type - 1]
        self.itype_name = self.itype_names[self.SelectHost.ilo_type - 1]
        self.HostILO.label_widget.value = 'IP адрес {0}'.format(self.itype_name)
        self.display()

    def select_ctype(self, *args, **keywords):
        ctype_form = npyscreen.Popup(name="Тип подключения")
        select_one = ctype_form.add(npyscreen.SelectOne, values=self.ctype_names, value=[0, ])
        ctype_form.edit()
        self.ConnectionTypeButton.value = self.ctype_names[select_one.value.pop()]
        self.display()

    def select_itype(self, *args, **keywords):
        itype_form = npyscreen.Popup(name="Тип подключения")
        select_one = itype_form.add(npyscreen.SelectOne, values=self.itype_names, value=[0, ])
        itype_form.edit()
        self.itype_name = self.itype_names[select_one.value.pop()]
        self.HostILO.label_widget.value = 'IP адрес {0}'.format(self.itype_name)
        self.display()

    def route_map(self, *args, **keywords):
        pass

    def service_list(self, *args, **keywords):
        service_form = ServiceForm(name='Подключенные сервисы', lines=len(self.Service)+10, services=self.Service)
        service_form.owner = weakref.proxy(self)
        service_form.edit()

    def create(self):
        super(HostFormEdit, self).create()
        self.cycle_widgets = True

    def check_host_name(self):
        with schema.db_select(appParameters.engine) as db:
            count = db.query(schema.Host).filter(schema.Host.name == self.HostName.value). \
                filter(schema.Host.parent == self.Parent). \
                filter(schema.Host.prefix == appParameters.user_info.prefix). \
                filter(schema.Host.type == 1). \
                filter(schema.Host.remove is False).count()
        if count == 0 or (self.SelectHost is not None and self.SelectHost.name == self.HostName.value):
            return True
        else:
            return False

    def on_cancel(self, *args, **keyword):
        self.parentApp.switchFormPrevious()

    def on_ok(self):
        error_list = []

        # проверка на незаполненные поля.
        if self.HostName.value == '':
            error_list.append('Отсутствует значение "Имя хоста"')
        if self.HostIP.value == '':
            error_list.append('Отсутствует значение "IP адрес"')

        # Проверка на корректность введеных данных.
        if not self.check_host_name():
            error_list.append('Имя узла {name} - уже существует'.format(name=self.HostName.value))

        if not utils.valid_ip(str(self.HostIP.value).strip()):
            error_list.append('Не корректное значение "IP адрес"')
        if not utils.valid_ip(str(self.HostILO.value).strip()) and len(self.HostILO.value) > 0:
            error_list.append('Не корректное значение "IP адрес iLo"')

        if len(error_list) == 0:
            ctype = 1
            for i in self.ctype:
                if i.name == self.ConnectionTypeButton.value:
                    ctype = i.id
            itype = None
            for i in self.itype:
                if i.name == self.itype_name:
                    itype = i.id

            try:
                ip, port = str(self.HostIP.value).strip().split(':')
            except ValueError:
                appParameters.log.warning("except ValueError str(self.HostIP.value).strip().join(':') - {}"
                                          .format(self.HostIP.value))
                ip = str(self.HostIP.value).strip()
                port = None

            if self.SelectHost is None:
                host = schema.Host(
                    name=str(self.HostName.value).strip(),
                    ip=ip,
                    type=1,
                    connection_type=ctype,
                    ilo_type=itype,
                    describe=str(self.Description.value).strip(),
                    ilo=str(self.HostILO.value).strip(),
                    parent=self.Parent,
                    default_login=str(self.Login.value).strip(),
                    default_password=str(self.Password.value).strip(),
                    tcp_port=port,
                    prefix=appParameters.user_info.prefix,
                    note=self.Note.values,
                    remove=False
                )
                with schema.db_edit(appParameters.engine) as db:
                    db.add(host)
                    db.flush()
                    db.add(schema.Action(action_type=20,
                                         user=appParameters.aaa_user.uid,
                                         date=datetime.datetime.now(),
                                         message='Добавлен узел host - id={0}'.format(host.id)))
                    appParameters.log.info('add host id={0}'.format(host.id))
            else:
                self.SelectHost.name = str(self.HostName.value).strip()
                self.SelectHost.ip = ip
                self.SelectHost.connection_type = ctype
                self.SelectHost.ilo_type = itype
                self.SelectHost.describe = str(self.Description.value).strip()
                self.SelectHost.ilo = str(self.HostILO.value).strip()
                self.SelectHost.default_login = str(self.Login.value).strip()
                self.SelectHost.default_password = str(self.Password.value).strip()
                self.SelectHost.tcp_port = port
                self.SelectHost.note = self.Note.values

                appParameters.log.info('edit host id={0}'.format(self.SelectHost.id))

                with schema.db_edit(appParameters.engine) as db:
                    db.add(self.SelectHost)
                    db.flush()
                    db.add(schema.Action(action_type=21,
                                         user=appParameters.aaa_user.uid,
                                         date=datetime.datetime.now(),
                                         message='Изменен узел host - id={0}'.format(self.SelectHost.id)))

            self.parentApp.switchFormPrevious()
        else:
            npyscreen.notify_confirm(error_list, title='Ошибка', form_color='DANGER')


class ServiceForm(npyscreen.Popup):
    OK_BUTTON_TEXT = 'Выход'

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.owner = None
        self.Service = []
        self.add_handlers({'^Q': self.exit})

        self.Service.extend(keywords['services'])
        self.service_list = self.add(npyscreen.MultiSelect, max_height=len(self.Service)+2)
        self.add_button = self.add(npyscreen.ButtonPress,
                                   name='Добавить',
                                   when_pressed_function=self.add_service,
                                   rely=self.lines - self.OK_BUTTON_BR_OFFSET[0] - 1)
        self.del_button = self.add(npyscreen.ButtonPress,
                                   name='Удалить',
                                   when_pressed_function=self.del_service,
                                   rely=self.add_button.rely,
                                   relx=self.add_button.relx + self.add_button.label_width + 2)

    def create(self):
        super(ServiceForm, self).create()
        # self.show_service()

    def add_service(self):
        with schema.db_select(appParameters.engine) as db:
            service_type = db.query(schema.ServiceType)

        add_service_form = AddService(name='Добавить сервис',
                                      service_type=service_type,
                                      cycle_widgets=True,
                                      lines=service_type.count()+10)
        add_service_form.owner = weakref.proxy(self)
        add_service_form.edit()
        appParameters.log.debug('ServiceForm.add_service(); self.Service = {0}'.format(self.Service))
        self.show_service()

    def show_service(self):
        self.service_list.value = ["{0}:{1} - {2}".format(s.remote_ip, s.remote_port, s. describe) for s in self.Service]
        self.refresh()
        pass

    def del_service(self):
        self.show_service()
        pass

    def exit(self, *args, **keywords):
        self.editing = False
        pass


class AddService(npyscreen.ActionPopup):
    OK_BUTTON_TEXT = "Добавить"
    CANCEL_BUTTON_TEXT = "Отмена"
    CANCEL_BUTTON_BR_OFFSET = (2, len(OK_BUTTON_TEXT.encode('utf-8')) + 2)
    FIX_MINIMUM_SIZE_WHEN_CREATED = False

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.owner = None
        self.add_handlers({'^Q': self.exit})
        self.service_type = keywords['service_type']
        self.DestinationIP = self.add(npyscreen.TitleText, name='IP адрес')
        self.DestinationPort = self.add(npyscreen.TitleText, name='TCP порт')
        self.Description = self.add(npyscreen.TitleText, name='Describe')
        self.add(npyscreen.Textfield)
        self.Type = self.add(npyscreen.SelectOne, values=[x.name for x in self.service_type])
        pass

    def create(self):
        super(AddService, self).create()

    def exit(self, *args, **keywords):
        self.editing = False
        pass

    def on_ok(self):
        if not utils.valid_ip(self.DestinationIP.value):
            npyscreen.notify_confirm("Не корректно введен IP адрес.", title='Ошибка', form_color='DANGER')
            return 0

        forward_tcp_port_disable = utils.get_app_parameters(appParameters.table_parameter,
                                                            'FORWARD_TCP_PORT_DISABLE').split(';')

        forward_tcp_port_disable = list(map(int, forward_tcp_port_disable))
        appParameters.log.debug('AddService.on_ok(); forward_tcp_port_disable = {0}'.format(forward_tcp_port_disable))

        try:
            int(self.DestinationPort.value)
        except ValueError:
            npyscreen.notify_confirm("Порт назначения должен быть числовым", title='Ошибка', form_color='DANGER')
            return 0

        if int(self.DestinationPort.value) in forward_tcp_port_disable \
                or 0 > int(self.DestinationPort.value) > 65535:
            npyscreen.notify_confirm("Порт назначения не корректен, либо заблокирован администратором",
                                     title='Ошибка', form_color='DANGER')
            return 0

        service = schema.Service(
            type=self.service_type[self.Type.value.pop()].id,
            remote_port=self.DestinationPort.value,
            remote_ip=self.DestinationIP.value,
            describe=self.Description.value
        )
        appParameters.log.debug('AddService.on_ok(); service = {0}'.format(service))
        self.owner.Service.append(service)
        pass


class Filter(npyscreen.Popup):
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.owner = None
        self.FilterText = self.add(npyscreen.TitleText, name='Фильтр:', )
        self.nextrely += 1
        self.Status_Line = self.add(npyscreen.Textfield, color='LABEL', editable=False)

    def update_status(self):
        host = self.owner.HostList
        count = 0
        for ITER in host:
            if self.FilterText.value in ITER.name:
                count += 1
        if count == 0:
            self.Status_Line.value = '(Нет совпадений)'
        elif count == 1:
            self.Status_Line.value = '(1 совпадение)'
        else:
            self.Status_Line.value = '(%s совпадений)' % count

    def create(self):
        super(Filter, self).create()

    def adjust_widgets(self):
        self.update_status()
        self.Status_Line.display()
        self.owner.Filter = self.FilterText.value


class ConnectionForm(npyscreen.Popup):
    OK_BUTTON_TEXT = 'Закрыть'

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.host = keywords['host']
        self.name = 'Подключение к узлу: {0}'.format(self.host.name)

    def create(self):
        super(ConnectionForm, self).create()
        self.cycle_widgets = True


class FolderForm(npyscreen.ActionPopup):
    Parent = 0
    Edit = 0
    GroupList = []

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.DirName = self.add(npyscreen.TitleText, name='Имя')
        self.Desc = self.add(npyscreen.TitleText, name='Описание')

    def create(self):
        self.cycle_widgets = True

    def beforeEditing(self):
        if self.Edit == 0:
            self.name = 'Создать новую директорию'
        else:
            self.name = 'Редактировать'
            with schema.db_select(appParameters.engine) as db:
                host = db.query(schema.Host).filter(schema.Host.id == self.Edit).one()
            self.DirName.value = host.name
            self.Desc.value = host.describe

    def on_cancel(self):
        self.parentApp.switchFormPrevious()

    def on_ok(self):
        if self.Edit == 0:
            with schema.db_select(appParameters.engine) as db:
                count = db.query(schema.Host).filter(schema.Host.name == self.DirName.value). \
                    filter(schema.Host.parent == self.Parent). \
                    filter(schema.Host.prefix == appParameters.user_info.prefix). \
                    filter(schema.Host.type == 2). \
                    filter(schema.Host.remove is False).count()
            if self.DirName.value != '' and count == 0:
                new_dir = schema.Host(name='{0}'.format(self.DirName.value),
                                      type=2,
                                      describe='{0}'.format(self.Desc.value),
                                      parent=self.Parent,
                                      remove=False,
                                      prefix=appParameters.user_info.prefix)
                with schema.db_edit(appParameters.engine) as db:
                    db.add(new_dir)
                    db.flush()
                    db.add(schema.Action(action_type=10,
                                         user=appParameters.aaa_user.uid,
                                         date=datetime.datetime.now(),
                                         message='Добавлена директория в host - id={0}'.format(new_dir.id)))
                    appParameters.log.debug('add directory id={0}'.format(new_dir.id))
                self.parentApp.switchFormPrevious()
            elif count > 0:
                npyscreen.notify_confirm('Данное имя уже существует!', title='Error', form_color='CRITICAL',
                                         wrap=True, wide=False, editw=0)
            else:
                npyscreen.notify_confirm('Имя не может быть пустым!', title='Error',
                                         form_color='CRITICAL', wrap=True, wide=False, editw=0)
        else:
            with schema.db_edit(appParameters.engine) as db:
                db.query(schema.Host).filter(schema.Host.id == self.Edit). \
                    update({schema.Host.name: self.DirName.value,
                            schema.Host.describe: self.Desc.value,
                            })
                db.add(schema.Action(action_type=11,
                                     user=appParameters.aaa_user.uid,
                                     date=datetime.datetime.now(),
                                     message='Внесены изменения в host - {0}'.format(self.Edit)))
            appParameters.log.debug('update directory {0}'.format(self.Edit))
            self.parentApp.switchFormPrevious()


class ErrorForm(npyscreen.FormBaseNew):
    error_text = ''
    text_error = None

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.framed = None
        self.text_error = self.add(npyscreen.FixedText)
        self.nextrely += 1
        self.add(npyscreen.ButtonPress, name='EXIT', when_pressed_function=self.exit)

    def while_editing(self, *args, **keywords):
        self.text_error.value = self.error_text
        self.text_error.highlight_color = 'DANGER'

    def exit(self):
        self.parentApp.switchForm(None)


class Interface(npyscreen.NPSAppManaged):
    appParameters = None
    keypress_timeout_default = 1

    def onStart(self):
        global appParameters
        appParameters = self.appParameters
        y, x = self.xy()
        appParameters.screen_size = {'y': y,
                                     'x': x}
        appParameters.log.debug('Запуск формы MAIN.')
        appParameters.log.debug('screen size: x = {0}, y = {1}'.format(x, y))
        if (x > 120 and y > 40) and appParameters.user_info.permissions.get('ShowHostInformation'):
            appParameters.log.info('Запуск в обычном режиме')
            self.addForm("MAIN", HostListDisplay)

        elif x >= 79 and y >= 24:
            appParameters.log.info('Запуск в упрощенном режиме')
            self.addForm("MAIN", HostListDisplay)
        else:
            appParameters.log.error('Размер терминала не поддерживется!')
            self.addForm("MAIN", ErrorForm)
            self.getForm("MAIN").error_text = 'Размер терминала не поддерживется!'
            return False

    @staticmethod
    def xy():
        max_y, max_x = curses.newwin(0, 0).getmaxyx()
        max_y -= 1
        max_x -= 1
        return max_y, max_x
