import datetime
import npyscreen
from acs import schema


class ButtonLine(npyscreen.FixedText):
    def display(self, *args, **keywords):
        self.value = ' '
        button = ['q - Выход',
                  'c - Подключится',
                  'f - Передача данных']

        if appParameters.user_info.permissions.get('EditDirectory') or \
                appParameters.user_info.permissions.get('Administrate'):
            button.append('d - Создать директорию')

        if appParameters.user_info.permissions.get('EditHostInformation') or \
                appParameters.user_info.permissions.get('Administrate'):
            button.append('a - Добавить Узел')

        if appParameters.user_info.permissions.get('EditHostInformation') or \
                appParameters.user_info.permissions.get('EditDirectory') or \
                appParameters.user_info.permissions.get('Administrate'):
            button.append('e - Редактировать')

        if appParameters.user_info.permissions.get('Administrate'):
            button.append('^A - Administrate')

        for value in button:
            self.value += '[{0}] '.format(value)


class RecordList(npyscreen.MultiLineAction):
    def display_value(self, vl):
        if type(vl) is schema.Host:
            if vl.type == 2:
                return '\t[{0:<20}]\t\t{1}'.format(vl.name, vl.note.split(';')[0] if vl.note else '')
            elif vl.type == 1:
                return '\t{0:<20}\t\t{1}'.format(vl.name, vl.note.split(';')[0] if vl.note else '')
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


class HostListDisplay(npyscreen.FormMutt):
    MAIN_WIDGET_CLASS = RecordList
    COMMAND_WIDGET_CLASS = ButtonLine
    Level = [0]
    History = []
    Filter = ''

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
            self.add_handlers({'d': self.add_folder})

    def update_list(self):
        if appParameters.user_info.permissions.get('Administrate'):
            with schema.db_select(appParameters.engine) as db:
                host = db.query(schema.Host).filter(schema.Host.parent == self.Level[-1]). \
                    filter(schema.Host.name.like('%{0}%'.format(self.Filter))). \
                    order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
        else:
            with schema.db_select(appParameters.engine) as db:
                host = db.query(schema.Host). \
                    filter(schema.Host.prefix.in_(appParameters.user_info.prefix)). \
                    filter(schema.Host.parent == self.Level[-1]). \
                    filter(schema.Host.name.like('%{0}%'.format(self.Filter))). \
                    order_by(schema.Host.type.desc()).order_by(schema.Host.name.desc()).all()

        appParameters.log.debug(host)

        if len(self.Level) == 1:
            self.wMain.values = host
        else:
            self.wMain.values = ['back'] + host
        self.wMain.display()
        self.wCommand.display()

    def app_exit(self, *args, **keywords):
        appParameters.log.debug('Выход из интерфейса.')
        self.parentApp.switchForm(None)

    def filter(self, *args, **keywords):
        self.parentApp.addForm('FILTER', Filter)
        self.parentApp.switchForm('FILTER')

    def connect(self, *args, **keywords):
        pass

    def file_transfer(self, *args, **keywords):
        pass

    def add_host(self, *args, **keywords):
        pass

    def add_folder(self, *args, **keywords):
        appParameters.log.debug('def add_folder: self.level[-1] = {0}'.format(self.level[-1]))
        self.parentApp.addForm('ADD_FOLDER', AddFolder)
        self.parentApp.getForm('ADD_FOLDER').Parent = self.level[-1]
        self.parentApp.switchForm('ADD_FOLDER')

    def edit_element(self, *args, **keywords):
        pass

    def delete_element(self, *args, **keywords):
        pass


class MyPopup(npyscreen.FormBaseNew):
    DEFAULT_LINES = 5
    DEFAULT_COLUMNS = 52
    SHOW_ATX = 20
    SHOW_ATY = 6


class Filter(MyPopup):
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.cycle_widgets = True
        self.FilterText = self.add(npyscreen.TitleText, name='Фильтр', max_width=40)
        self.ButtonOk = self.add(npyscreen.MiniButtonPress, name='OK',
                                 when_pressed_function=self.on_ok,
                                 relx=self.FilterText.relx + self.FilterText.max_width,
                                 rely=self.FilterText.rely)

    def create(self):
        self.name = 'Применить фильтр'

    def on_ok(self):
        appParameters.log.debug('set filter: {}'.format(self.FilterText.value))
        self.parentApp.getForm('MAIN').Filter = self.FilterText.value
        self.parentApp.switchFormPrevious()


class AddFolder(npyscreen.ActionPopup):
    Parent = 0
    Edit = 0
    GroupList = []

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.DirName = self.add(npyscreen.TitleText, name='Имя')
        self.Note = self.add(npyscreen.TitleText, name='Описание')
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
        if appParameters.user_info.permissions.get('EditDirectory'):
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
            self.Note.value = host.note

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
                                      note='{0}'.format(self.Note.value),
                                      parent=self.Parent,
                                      transit=False,
                                      remote=False,
                                      remove=False,
                                      prefix=self.Group.values[self.Group.value[0]])
                with schema.db_edit(appParameters.engine) as db:
                    db.add(new_dir)
                    db.flush()
                    db.add(schema.Action(action_type=10,
                                         user=appParameters.aaa_user.uid,
                                         date=datetime.datetime.now(),
                                         message='Добавлена директория в host - id={0}'.format(new_dir.id)))
                    self.parentApp.appParameters.log.debug('add directory id={0}'.format(new_dir.id))
                self.parentApp.switchFormPrevious()
            elif count > 0:
                npyscreen.notify_confirm('Данное имя уже существует!', title='Error', form_color='CRITICAL',
                                         wrap=True, wide=True, editw=0)
            else:
                npyscreen.notify_confirm('Имя не может быть пустым!', title='Error',
                                         form_color='CRITICAL', wrap=True, wide=True, editw=0)
        else:
            with schema.db_select(appParameters.engine) as db:
                db.query(schema.Host).filter(schema.Host.id == self.Edit). \
                    update({schema.Host.name: self.DirName.value,
                            schema.Host.note: self.Note.value,
                            schema.Host.prefix: self.Group.values[self.Group.value[0]]})
                db.add(schema.Action(action_type=11,
                                     user=appParameters.aaa_user.uid,
                                     date=datetime.datetime.now(),
                                     message='Внесены изменения в host - {0}'.format(self.Edit)))
            appParameters.log.debug('update directory {0}'.format(self.Edit))
            self.parentApp.switchFormPrevious()


class Interface(npyscreen.NPSAppManaged):
    appParameters = None
    keypress_timeout_default = 1

    def onStart(self):
        global appParameters
        appParameters = self.appParameters
        appParameters.log.debug('Запуск формы MAIN.')
        self.addForm("MAIN", HostListDisplay)
