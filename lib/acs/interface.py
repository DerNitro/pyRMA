import weakref
import datetime
import npyscreen
import curses.ascii

import sys

from acs import schema, template


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
                return '\t{0:<20}\t\t{1}'.format(vl.name, vl.describe[0] if vl.describe else '')
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
    SelectHost = None
    Host = None

    def beforeEditing(self):
        self.wStatus1.value = ' {0} - {1} '.format(appParameters.program,
                                                   appParameters.version)
        self.wStatus2.value = ' Управление: '
        self.keypress_timeout = 30
        self.update_list()

        self.add_handlers({'q': self.app_exit,
                           'c': self.connect,
                           'f': self.file_transfer,
                           '+': self.filter})

        if appParameters.user_info.permissions.get('EditDirectory') or \
                appParameters.user_info.permissions.get('Administrate'):
            self.add_handlers({'d': self.add_folder,
                               'e': self.edit_element,
                               'a': self.add_host})

        self.help = template.help_main_form().format(program=appParameters.program,
                                                     version=appParameters.version)

    def update_list(self):
        if appParameters.user_info.permissions.get('Administrate'):
            with schema.db_select(appParameters.engine) as db:
                self.Host = db.query(schema.Host).filter(schema.Host.parent == self.Level[-1]). \
                    filter(schema.Host.name.like('%{0}%'.format(self.Filter))). \
                    order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
        else:
            with schema.db_select(appParameters.engine) as db:
                self.Host = db.query(schema.Host). \
                    filter(schema.Host.prefix.in_(appParameters.user_info.prefix)). \
                    filter(schema.Host.parent == self.Level[-1]). \
                    filter(schema.Host.name.like('%{0}%'.format(self.Filter))). \
                    order_by(schema.Host.type.desc()).order_by(schema.Host.name.desc()).all()

        appParameters.log.debug(self.Host)

        if len(self.Level) == 1:
            self.wMain.values = self.Host
        else:
            self.wMain.values = ['back'] + self.Host
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
        self.update_list()

    def connect(self, *args, **keywords):
        pass

    def file_transfer(self, *args, **keywords):
        pass

    def add_host(self, *args, **keywords):
        appParameters.log.debug('def add_host: self.level[-1] = {0}'.format(self.Level[-1]))
        self.parentApp.addForm('HOST', HostForm)
        self.parentApp.getForm('HOST').Parent = self.Level[-1]
        self.parentApp.switchForm('HOST')

    def add_folder(self, *args, **keywords):
        appParameters.log.debug('def add_folder: self.level[-1] = {0}'.format(self.Level[-1]))
        self.parentApp.addForm('FOLDER', FolderForm)
        self.parentApp.getForm('FOLDER').Parent = self.Level[-1]
        self.parentApp.switchForm('FOLDER')

    def edit_element(self, *args, **keywords):
        if self.SelectHost.type == 2:
            appParameters.log.debug('def add_folder: self.level[-1] = {0}'.format(self.Level[-1]))
            self.parentApp.addForm('FOLDER', FolderForm)
            self.parentApp.getForm('FOLDER').Parent = self.Level[-1]
            self.parentApp.getForm('FOLDER').Edit = self.SelectHost.id
            self.parentApp.switchForm('FOLDER')
        pass

    def delete_element(self, *args, **keywords):
        pass


class HostForm(npyscreen.ActionFormV2):
    Parent = 0
    Edit = 0

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.HostName = self.add(npyscreen.TitleText, name='Имя хоста')
        self.Description = self.add(npyscreen.TitleText, name='Description')
        self.HostIP = self.add(npyscreen.TitleText, name='IP адрес')
        self.HostILO = self.add(npyscreen.TitleText, name='IP адрес iLo')
        self.Login = self.add(npyscreen.TitleText, name='Логин')
        self.Password = self.add(npyscreen.TitleText, name='Пароль')

        self.ConnectionTypeButton = self.add(npyscreen.TitleFixedText,
                                             name='Тип подключения',
                                             use_two_lines=False)

        self.ConnectionTypeButton.add_handlers({curses.ascii.NL: self.select_ctype,
                                                curses.ascii.CR: self.select_ctype})
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

    def select_ctype(self, *args, **keywords):
        pass

    def route_map(self, *args, **keywords):
        pass

    def service_list(self, *args, **keywords):
        pass

    def create(self):
        super(HostForm, self).create()
        self.cycle_widgets = True

    def on_cancel(self):
        self.parentApp.switchFormPrevious()

    def on_ok(self):
        self.parentApp.switchFormPrevious()


class Filter(npyscreen.Popup):
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.owner = None
        self.FilterText = self.add(npyscreen.TitleText, name='Фильтр:', )
        self.nextrely += 1
        self.Status_Line = self.add(npyscreen.Textfield, color='LABEL', editable=False)

    def update_status(self):
        host = self.owner.Host
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


class FolderForm(npyscreen.ActionPopup):
    Parent = 0
    Edit = 0
    GroupList = []

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.DirName = self.add(npyscreen.TitleText, name='Имя')
        self.Desc = self.add(npyscreen.TitleText, name='Описание')
        self.Group = self.add(npyscreen.TitleSelectOne, name='Группа', hidden=True,
                              values=self.GroupList, value=self.GroupList[0])

    def create(self):
        self.cycle_widgets = True
        self.GroupList.clear()
        if appParameters.user_info.permissions.get('Administrate'):
            with schema.db_select(appParameters.engine) as db:
                groups = db.query(schema.Prefix).all()
            for group in groups:
                self.GroupList.append(group.name)
        else:
            self.GroupList.append(appParameters.user_info.prefix)

    def beforeEditing(self):
        if appParameters.user_info.permissions.get('Administrate'):
            self.Group.hidden = False
            self.Group.value = 0
        else:
            self.Group.value = 0
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
                    filter(schema.Host.type == 2). \
                    filter(schema.Host.prefix == self.Group.values[self.Group.value[0]]).count()
            if self.DirName.value != '' and count == 0:
                new_dir = schema.Host(name='{0}'.format(self.DirName.value),
                                      type=2,
                                      describe='{0}'.format(self.Desc.value),
                                      parent=self.Parent,
                                      remove=False,
                                      prefix=self.Group.values[self.Group.value[0]])
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
                                         wrap=True, wide=True, editw=0)
            else:
                npyscreen.notify_confirm('Имя не может быть пустым!', title='Error',
                                         form_color='CRITICAL', wrap=True, wide=True, editw=0)
        else:
            with schema.db_edit(appParameters.engine) as db:
                db.query(schema.Host).filter(schema.Host.id == self.Edit). \
                    update({schema.Host.name: self.DirName.value,
                            schema.Host.describe: self.Desc.value,
                            schema.Host.prefix: self.Group.values[self.Group.value[0]]})
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
