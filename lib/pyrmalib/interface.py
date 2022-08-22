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
import os
import datetime
import weakref
import npyscreen
import curses.ascii
from pyrmalib import schema, template, access, parameters, utils, applib, connection

appParameters = parameters.AppParameters()  # type: parameters.AppParameters
connection_host = None


def echo_form(text):
    f = npyscreen.PopupWide()
    f.add(npyscreen.FixedText, value=text)
    f.edit()
    del f


class MultiLineEditableBoxed(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEditable


class ButtonLine(npyscreen.FixedText):
    def display(self, *args, **keywords):
        self.value = 'Используйте F1 или CTRL + o для просмотра списка команд.'


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
                self.parent.update_list()
        else:
            self.parent.Filter = ''
            self.parent.Level.pop()
            if len(self.parent.History) > 0:
                self.cursor_line = self.parent.History.pop()
            else:
                self.cursor_line = 0
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
        self.keypress_timeout = 1
        self.update_list()

        self.add_handlers(
            {
                '^Q': self.app_exit,
                '+': self.filter,
                'i': self.show_host_information,
                'f': self.find
            }
        )

        self.help = template.help_main_form().format(
            program=appParameters.program,
            version=appParameters.version
        )

    def update_list(self):
        if self.Level[-1] == 'Find':
            pass
        else:
            if appParameters.user_info.admin:
                with schema.db_select(appParameters.engine) as db:
                    self.HostList = db.query(schema.Host).filter(schema.Host.parent == self.Level[-1]). \
                        filter(schema.Host.name.like('%{0}%'.format(self.Filter)),
                               schema.Host.remove.is_(False)). \
                        order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
            else:
                with schema.db_select(appParameters.engine) as db:
                    self.HostList = db.query(schema.Host). \
                        filter(schema.Host.prefix == appParameters.user_info.prefix,
                               schema.Host.parent == self.Level[-1],
                               schema.Host.name.like('%{0}%'.format(self.Filter)),
                               schema.Host.remove.is_(False)). \
                        order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()

        appParameters.log.debug("HostListDisplay.update_list - {}".format(self.HostList))

        if len(self.Level) == 1:
            self.wMain.values = self.HostList
        else:
            self.wMain.values = ['back'] + self.HostList

        if len(self.HostList) == 0:
            self.wMain.values = ['empty']

        if connection_host:
            self.app_exit()

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

    def show_host_information(self, *args, **keywords):
        if access.check_access(appParameters, 'ShowHostInformation', h_object=self.SelectHost) or \
                appParameters.user_info.admin:
            host_form_information = InformationForm(host=self.SelectHost)
            host_form_information.edit()
        else:
            npyscreen.notify_confirm('Нет прав доступа для операции', title='Ошибка', form_color='DANGER')
        pass

    def find(self, *args, **keywords):
        find_form = Find()
        find_form.owner = weakref.proxy(self)
        find_form.display()
        find_form.FindText.edit()
        del find_form
        self.Level.append('Find')
        self.update_list()


class Find(npyscreen.Popup):
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.owner = None
        self.FindText = self.add(npyscreen.TitleText, name='Поиск:')

    def create(self):
        super(Find, self).create()

    def adjust_widgets(self):
        self.owner.HostList = applib.search(appParameters, self.FindText.value)


class AccessRequest(npyscreen.ActionForm):
    OK_BUTTON_TEXT = "Отправить"
    CANCEL_BUTTON_TEXT = "Отмена"
    CANCEL_BUTTON_BR_OFFSET = (2, 18)
    host = None

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.add_handlers({'^Q': self.exit_editing})
        self.name = 'Запрос доступа к узлу: {0}'.format(keywords['name'])
        self.date_disable = self.add(
            npyscreen.TitleDateCombo,
            name="Доступ до даты",
            value=datetime.date.today() + datetime.timedelta(days=1),
            begin_entry_at=20
        )
        self.ticket = self.add(npyscreen.TitleText, name='Номер Заявки', begin_entry_at=20)
        self.access = self.add(
            npyscreen.TitleMultiSelect, 
            name='Доступы', 
            max_height=4, 
            values=keywords['access_list'],
            begin_entry_at=20
        )
        self.note = self.add(npyscreen.MultiLineEditableBoxed, name='Дополнительное Описание', editable=True)

    def create(self):
        super(AccessRequest, self).create()
        self.cycle_widgets = True

    def on_ok(self):
        access_list = [self.access.values[i] for i in self.access.value]
        request = schema.RequestAccess(
            user=appParameters.user_info.uid,
            host=self.host.id,
            status=0,
            date_request=datetime.datetime.now(),
            date_access=self.date_disable.value,
            ticket=self.ticket.value,
            note="\n".join(self.note.values),
            connection=True if 'Подключение' in access_list else False,
            file_transfer=True if 'Передача файлов' in access_list else False,
            ipmi=True if 'IPMI' in access_list else False
        )
        if not access.request_access(appParameters, request):
            echo_form('Ошибка выполнения запроса доступа, просьба обратится к администратору системы!')
        else:
            echo_form('Запрос доступа отправлен!')


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


class ConnectionForm(npyscreen.Form):
    OK_BUTTON_TEXT = 'Закрыть'
    ip_address = None
    description = None
    login = None
    password = None
    service = None
    login_password = None
    save_pass = None
    btn_connection = None
    btn_file_transfer = None
    btn_ipmi = None
    button_line_relx = 0

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.host = keywords['host']  # type: schema.Host
        self.name = 'Подключение к узлу: {0}'.format(self.host.name)
        self.add_handlers({'^Q': self.exit_editing})
        self.fill_values()

    def create(self):
        super(ConnectionForm, self).create()
        self.cycle_widgets = True
        self.ip_address = self.add(npyscreen.TitleFixedText, name='IP адрес')
        self.description = self.add(npyscreen.TitleFixedText, name='Описание')
        self.login = self.add(npyscreen.TitleText, name='Login', hidden=True)
        self.password = self.add(npyscreen.TitlePassword, name='Password', hidden=True)
        self.save_pass = self.add(npyscreen.MultiSelect, max_height=2, values=["Сохранить пароль?"], hidden=True)
        self.service = self.add(npyscreen.BoxTitle, name='Service', max_height=7)
        self.add(npyscreen.FixedText)
        self.btn_connection = self.add(
            npyscreen.ButtonPress, name='Подключение',
            when_pressed_function=self.connection
        )
        self.button_line_relx += self._widgets__[-1].label_width + 2
        self.btn_file_transfer = self.add(
            npyscreen.ButtonPress, name='Передача файлов',
            rely=self._widgets__[-1].rely,
            relx=self.button_line_relx,
            when_pressed_function=self.file_transfer,
            hidden=True
        )
        self.button_line_relx += self._widgets__[-1].label_width + 2
        self.btn_ipmi = self.add(
            npyscreen.ButtonPress, name='IPMI',
            rely=self._widgets__[-1].rely,
            relx=self.button_line_relx,
            when_pressed_function=self.connection_ilo,
            hidden=True)
        pass

    def fill_values(self):
        self.ip_address.value = self.host.ip
        self.description.value = self.host.describe
        self.login_password = applib.get_password(appParameters, self.host.id)
        if isinstance(self.login_password, schema.PasswordList):
            self.login.value = self.login_password.login
            self.password.value = '*' * len(self.login_password.password)
        else:
            self.login.value = self.host.default_login
            if self.host.default_password is not None:
                self.password.value = '*' * len(self.host.default_password)
        services = applib.get_service(appParameters, self.host.id)
        service_types = applib.get_service_type(appParameters, raw=True)
        if access.check_access(appParameters, 'EditCredential', h_object=self.host):
            self.login.hidden = False
            self.password.hidden = False
            self.save_pass.hidden = False
        if self.host.ilo_type:
            self.btn_ipmi.hidden = False
        if self.host.file_transfer_type:
            self.btn_file_transfer.hidden = False
        if len(services) > 0 and (
            access.check_access(appParameters, 'ConnectionService', h_object=self.host) or 
            access.check_access(appParameters, 'ConnectionOnlyService', h_object=self.host)
        ):
            service_string_list = []
            for s in services:
                service_type = None
                for st in service_types:
                    if s.type == st.default_port:
                        service_type = st.name
                        break
                service_string_list.append(
                    '{service_type}: {acs_ip}:{s.local_port} -> {s.remote_ip}:{s.remote_port} {s.describe}'.format(
                        s=s,
                        acs_ip=appParameters.app_ip_address,
                        service_type=service_type
                    )
                )
            self.service.values = service_string_list
        self.DISPLAY()
        pass

    def connection(self):
        global connection_host

        if access.check_access(appParameters, "Connection", h_object=self.host):
            if not self.save_pass.hidden and len(self.save_pass.value) > 0:
                applib.save_password(appParameters, self.host.id, self.login.value, self.password.value)
            conn_type = applib.get_connection_type(appParameters)
            conn_type_name = None
            for type_id, name in conn_type:
                if type_id == self.host.connection_type:
                    conn_type_name = name
            if conn_type_name == 'SSH':
                connection_host = connection.SSH(appParameters, self.host)
            elif conn_type_name == 'TELNET':
                connection_host = connection.TELNET(appParameters, self.host)
            connection_host.LOGIN = self.login.value

            if isinstance(self.login_password, schema.PasswordList) \
                    and self.password.value == '*' * len(self.login_password.password):
                connection_host.PASSWORD = utils.password(self.login_password.password, self.host.id, mask=False)
            elif self.password.value == '*' * len(self.host.default_password):
                connection_host.PASSWORD = utils.password(self.host.default_password, self.host.id, mask=False)
            else:
                connection_host.PASSWORD = self.password.value

            self.editing = False
        elif access.check_access(appParameters, "ConnectionOnlyService", h_object=self.host):
            # connection only service
            connection_host = connection.SERVICE(appParameters, self.host)
            connection_host.LOGIN = self.login.value
            if isinstance(self.login_password, schema.PasswordList) \
                    and self.password.value == '*' * len(self.login_password.password):
                connection_host.PASSWORD = utils.password(self.login_password.password, self.host.id, mask=False)
            elif self.password.value == '*' * len(self.host.default_password):
                connection_host.PASSWORD = utils.password(self.host.default_password, self.host.id, mask=False)
            else:
                connection_host.PASSWORD = self.password.value
            self.editing = False
        else:
            access_list = ['Подключение']
            if not self.btn_file_transfer.hidden:
                access_list.append('Передача файлов')
            if not self.btn_ipmi.hidden:
                access_list.append('IPMI')
            access_form = AccessRequest(name=self.host.name, access_list=access_list)
            access_form.host = self.host
            access_form.edit()

    def file_transfer(self):
        global connection_host
        if access.check_access(appParameters, "FileTransfer", h_object=self.host):
            if not self.save_pass.hidden and len(self.save_pass.value) > 0:
                applib.save_password(appParameters, self.host.id, self.login.value, self.password.value)
            conn_type = applib.get_file_transfer_type(appParameters)
            conn_type_name = None
            for type_id, name in conn_type:
                if type_id == self.host.file_transfer_type:
                    conn_type_name = name
            if conn_type_name == 'SFTP':
                connection_host = connection.SFTP(appParameters, self.host)
            connection_host.LOGIN = self.login.value

            if isinstance(self.login_password, schema.PasswordList) \
                    and self.password.value == '*' * len(self.login_password.password):
                connection_host.PASSWORD = utils.password(self.login_password.password, self.host.id, mask=False)
            elif self.password.value == '*' * len(self.host.default_password):
                connection_host.PASSWORD = utils.password(self.host.default_password, self.host.id, mask=False)
            else:
                connection_host.PASSWORD = self.password.value
            connection_host.ft_bin = os.path.join(appParameters.app_folder, 'bin', 'ft.py')
            self.editing = False
        else:
            access_list = ['Подключение']
            if not self.btn_file_transfer.hidden:
                access_list.append('Передача файлов')
            if not self.btn_ipmi.hidden:
                access_list.append('IPMI')
            access_form = AccessRequest(name=self.host.name, access_list=access_list)
            access_form.host = self.host
            access_form.edit()

    def connection_ilo(self):
        global connection_host

        if access.check_access(appParameters, "ConnectionIlo", h_object=self.host):
            connection_host = connection.IPMI(appParameters, self.host)
            self.editing = False
        else:
            access_list = ['Подключение']
            if not self.btn_file_transfer.hidden:
                access_list.append('Передача файлов')
            if not self.btn_ipmi.hidden:
                access_list.append('IPMI')
            access_form = AccessRequest(name=self.host.name, access_list=access_list)
            access_form.host = self.host
            access_form.edit()


class InformationForm(npyscreen.Form):
    ip_address = None
    description = None
    login = None
    password = None
    service = None
    note = None

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.host = keywords['host']  # type: schema.Host
        self.name = 'Информация о узле {name}'.format(name=self.host.name)

    def create(self):
        self.cycle_widgets = True
        self.ip_address = self.add(npyscreen.TitleFixedText, name='IP адрес')
        self.description = self.add(npyscreen.TitleFixedText, name='Описание')
        self.login = self.add(npyscreen.TitleFixedText, name='Login')
        self.password = self.add(npyscreen.TitleFixedText, name='Password')
        self.service = self.add(npyscreen.BoxTitle, name='Service', max_height=7)
        self.note = self.add(npyscreen.BoxTitle, name='Note')
        pass

    def while_editing(self, *args, **keywords):
        self.add_handlers({'^Q': self.exit_editing})
        self.fill_values()
        pass

    def fill_values(self):
        self.ip_address.value = self.host.ip
        self.description.value = self.host.describe
        login_password = applib.get_password(appParameters, self.host.id)
        if access.check_access(appParameters, 'ShowLogin', h_object=self.host) or appParameters.user_info.admin:
            if isinstance(login_password, schema.PasswordList):
                self.login.value = login_password.login
                if access.check_access(appParameters, 'ShowPassword', h_object=self.host):
                    if self.host.default_password is not None:
                        self.password.value = utils.password(login_password.password, self.host.id, False)
                else:
                    self.password.value = '*' * 10
            else:
                self.login.value = self.host.default_login
                if access.check_access(appParameters, 'ShowPassword', h_object=self.host) or appParameters.user_info.admin:
                    self.password.value = utils.password(self.host.default_password, self.host.id, False)
                else:
                    self.password.value = '*' * 10
        else:
            self.login.value = '*' * 10
            self.password.value = '*' * 10
        services = applib.get_service(appParameters, self.host.id)
        service_types = applib.get_service_type(appParameters, raw=True)
        if len(services) > 0:
            service_string_list = []
            for s in services:
                service_type = None
                for st in service_types:
                    if s.type == st.default_port:
                        service_type = st.name
                        break
                service_string_list.append(
                    '{service_type}: {acs_ip}:{s.local_port} -> {s.remote_ip}:{s.remote_port} {s.describe}'.format(
                        s=s,
                        service_type=service_type,
                        acs_ip=appParameters.app_ip_address
                    )
                )
            self.service.values = service_string_list
        self.note.values = self.host.note.split('\n')
        self.DISPLAY()
        pass


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
    keypress_timeout_default = 1

    def __init__(self, app_param: parameters.AppParameters):
        super().__init__()
        self.appParameters = app_param

    def onStart(self):
        global appParameters
        appParameters = self.appParameters
        y, x = self.xy()
        appParameters.screen_size = {
            'y': y,
            'x': x
        }
        appParameters.log.debug('Запуск формы MAIN.')
        appParameters.log.debug('screen size: x = {0}, y = {1}'.format(x, y))
        if not appParameters.user_info.check:
            self.addForm("MAIN", ErrorForm)
            self.getForm("MAIN").error_text = 'Пользователь проходит проверку администратором!'
        elif x >= 80 and y >= 24:
            appParameters.log.info('Запуск в обычном режиме')
            self.addForm("MAIN", HostListDisplay)
        else:
            appParameters.log.error('Размер терминала не поддерживается!')
            self.addForm("MAIN", ErrorForm)
            self.getForm("MAIN").error_text = 'Размер терминала не поддерживается!'

    def run(self, fork=None):
        super(Interface, self).run(fork=None)
        return connection_host

    @staticmethod
    def xy():
        max_y, max_x = curses.newwin(0, 0).getmaxyx()
        return max_y, max_x
