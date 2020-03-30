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
import npyscreen
import curses.ascii
from pyrmalib import schema, template, access, parameters, utils, pyrmalib


def echo_form(text):
    # Для ддебага форма.
    f = npyscreen.Popup()
    f.add(npyscreen.FixedText, value=text)
    f.edit()


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
                if True:
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
        self.keypress_timeout = 1
        self.update_list()

        self.add_handlers({'^Q': self.app_exit,
                           '+': self.filter,
                           'i': self.show_host_information,
                           'f': self.find
                           })

        self.help = template.help_main_form().format(program=appParameters.program,
                                                     version=appParameters.version)

    def update_list(self):
        if access.check_access(appParameters, 'Administrate'):
            with schema.db_select(appParameters.engine) as db:
                self.HostList = db.query(schema.Host).filter(schema.Host.parent == self.Level[-1]). \
                    filter(schema.Host.name.like('%{0}%'.format(self.Filter)),
                           schema.Host.remove.is_(False)).\
                    order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
        else:
            with schema.db_select(appParameters.engine) as db:
                # TODO. Разобратся с префиксами
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
                access.check_access(appParameters, 'Administrate'):
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
        self.DISPLAY()


class Find(npyscreen.Popup):
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.owner = None
        self.FindText = self.add(npyscreen.TitleText, name='Поиск:')

    def create(self):
        super(Find, self).create()

    # def on_ok(self):
    #     with schema.db_select(appParameters.engine) as db:
    #         host_list = db.query(schema.Host).filter(
    #             or_(
    #                 schema.Host.name.like('%{0}%'.format(self.FindText.value)),
    #                 schema.Host.ip.like('%{0}%'.format(self.FindText.value))
    #             )).order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
    #     self.owner.HostList = [ None ] + host_list
    #     self.owner.History.append('Find')


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
    DEFAULT_LINES = 20
    DEFAULT_COLUMNS = 80
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
        self.login = self.add(npyscreen.TitleText, name='Login')
        self.password = self.add(npyscreen.TitlePassword, name='Password')
        self.save_pass = self.add(npyscreen.MultiSelect, max_height=2, values=["Сохранить пароль?"])
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
            npyscreen.ButtonPress, name='iLo|IPMI',
            rely=self._widgets__[-1].rely,
            relx=self.button_line_relx,
            when_pressed_function=self.connection_ilo,
            hidden=True)
        pass

    def fill_values(self):
        self.ip_address.value = self.host.ip
        self.description.value = self.host.describe
        self.login_password = pyrmalib.get_password(appParameters, self.host.id)
        if isinstance(self.login_password, schema.PasswordList):
            self.login.value = self.login_password.login
            self.password.value = '*' * len(self.login_password.password)
        else:
            self.login.value = self.host.default_login
            if self.host.default_password is not None:
                self.password.value = '*' * len(self.host.default_password)
        services = pyrmalib.get_service(appParameters, self.host.id)
        service_types = pyrmalib.get_service_type(appParameters, raw=True)
        if self.host.ilo_type:
            self.btn_ipmi.hidden = False
        if self.host.file_transfer_type:
            self.btn_file_transfer.hidden = False
        if len(services) > 0:
            service_string_list = []
            for s in services:
                service_type = None
                for st in service_types:
                    if s.type == st.id:
                        service_type = st.name
                        break
                service_string_list.append(
                    '{service_type}: {s.local_port} -> {s.remote_ip}:{s.remote_port} {s.describe}'.format(
                        s=s,
                        service_type=service_type
                    )
                )
            self.service.values = service_string_list
        self.DISPLAY()
        pass

    def connection(self):
        if len(self.save_pass.value) > 0:
            pyrmalib.save_password(appParameters, self.host.id, self.login.value, self.password.value)

    def file_transfer(self):
        pass

    def connection_ilo(self):
        pass


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
        login_password = access.get_password(appParameters, appParameters.user_info.login, self.host.id)
        if access.check_access(appParameters, 'ShowLogin', h_object=self.host):
            if isinstance(login_password, schema.PasswordList):
                self.login.value = login_password.login
                if access.check_access(appParameters, 'ShowPassword', h_object=self.host):
                    if self.host.default_password is not None:
                        self.password.value = utils.password(login_password.password, self.host.id, False)
                else:
                    self.password.value = '*' * 10
            else:
                self.login.value = self.host.default_login
                if access.check_access(appParameters, 'ShowPassword', h_object=self.host):
                    self.password.value = utils.password(self.host.default_password, self.host.id, False)
                else:
                    self.password.value = '*' * 10
        else:
            self.login.value = '*' * 10
            self.password.value = '*' * 10
        services = pyrmalib.get_service(appParameters, self.host.id)
        service_types = pyrmalib.get_service_type(appParameters, raw=True)
        if len(services) > 0:
            service_string_list = []
            for s in services:
                service_type = None
                for st in service_types:
                    if s.type == st.id:
                        service_type = st.name
                        break
                service_string_list.append(
                    '{service_type}: {s.local_port} -> {s.remote_ip}:{s.remote_port} {s.describe}'.format(
                        s=s,
                        service_type=service_type
                    )
                )
            self.service.values = service_string_list
        self.note.values = template.information_host(self.host.note).split('\n')
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
    appParameters = None  # type: parameters.AppParameters
    keypress_timeout_default = 1

    def __init__(self, app_param: parameters.AppParameters):
        super().__init__()
        self.appParameters = app_param

    def onStart(self):
        global appParameters
        appParameters = self.appParameters
        y, x = self.xy()
        appParameters.screen_size = {'y': y,
                                     'x': x}
        appParameters.log.debug('Запуск формы MAIN.')
        appParameters.log.debug('screen size: x = {0}, y = {1}'.format(x, y))
        if x > 120 and y > 40:
            appParameters.log.info('Запуск в обычном режиме')
            self.addForm("MAIN", HostListDisplay)

        # elif x >= 79 and y >= 24:
        #     appParameters.log.info('Запуск в упрощенном режиме')
        #     self.addForm("MAIN", HostListDisplay)
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
