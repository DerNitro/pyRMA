import datetime
import npyscreen
from acs import schema


class ButtonLine(npyscreen.FixedText):
    def display(self, *args, **keywords):
        self.value = ' '
        button = ['q - Выход',
                  'c - Подключится',
                  'f - Передача данных']
        btn_manager = ['a - Добавить узел',
                       'e - Редактировать',
                       'd - Добавить директорию']
        btn_admin = ['^D - Удалить']

        for value in button:
            self.value += '[{0}] '.format(value)

        if 'all' in self.parent.parentApp.appParameters.user_info.permissions.split(';') \
                or 'edit_host' in self.parent.parentApp.appParameters.user_info.permissions.split(';'):
            for value in btn_manager:
                self.value += '[{0}] '.format(value)

        if 'all' in self.parent.parentApp.appParameters.user_info.permissions.split(';') \
                or 'admin' in self.parent.parentApp.appParameters.user_info.permissions.split(';'):
            for value in btn_admin:
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

    def actionHighlighted(self, act_on_this, key_press):
        pass


class HostListDisplay(npyscreen.FormMutt):
    MAIN_WIDGET_CLASS = RecordList
    COMMAND_WIDGET_CLASS = ButtonLine
    level = [0]

    def beforeEditing(self):
        self.wStatus1.value = ' {0} - {1} '.format(self.parentApp.appParameters.program,
                                                   self.parentApp.appParameters.version)
        self.wStatus2.value = ' Управление: '
        self.keypress_timeout = 30
        self.update_list()

        self.add_handlers({'q': self.app_exit,
                           'c': self.connect,
                           'f': self.file_transfer})

        if 'all' in self.parentApp.appParameters.user_info.permissions.split(';') \
                or 'edit_host' in self.parentApp.appParameters.user_info.permissions.split(';'):
            self.add_handlers({'a': self.add_host,
                               'd': self.add_folder,
                               'e': self.edit_element})

        if 'all' in self.parentApp.appParameters.user_info.permissions.split(';') \
                or 'admin' in self.parentApp.appParameters.user_info.permissions.split(';'):
            self.add_handlers({'^D': self.delete_element})

    def update_list(self):
        if 'ALL' in self.parentApp.appParameters.user_info.group.split(';'):
            with schema.db_select(self.parentApp.appParameters.engine) as db:
                host = db.query(schema.Host).filter(schema.Host.parent == self.level[-1]). \
                    order_by(schema.Host.type.desc()).order_by(schema.Host.name).all()
        else:
            with schema.db_select(self.parentApp.appParameters.engine) as db:
                host = db.query(schema.Host). \
                    filter(schema.Host.group.in_(self.parentApp.appParameters.user_info.group.split(';'))). \
                    filter(schema.Host.parent == self.level[-1]). \
                    order_by(schema.Host.type.desc()).order_by(schema.Host.name.desc()).all()

        self.parentApp.appParameters.log.debug(host)
        if len(self.level) == 1:
            self.wMain.values = host
        else:
            self.wMain.values = ['back'] + host
        self.wMain.display()
        self.wCommand.display()

    def app_exit(self, *args, **keywords):
        self.parentApp.appParameters.log.debug('Выход из интерфейса.')
        self.parentApp.switchForm(None)

    def connect(self, *args, **keywords):
        pass

    def file_transfer(self, *args, **keywords):
        pass

    def add_host(self, *args, **keywords):
        pass

    def add_folder(self, *args, **keywords):
        self.parentApp.appParameters.log.debug('def add_folder: self.level[-1] = {0}'.format(self.level[-1]))
        self.parentApp.addForm('ADD_FOLDER', AddFolder)
        self.parentApp.getForm('ADD_FOLDER').Parent = self.level[-1]
        self.parentApp.switchForm('ADD_FOLDER')

    def edit_element(self, *args, **keywords):
        pass

    def delete_element(self, *args, **keywords):
        pass


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
        if self.parentApp.appParameters.user_info.group == 'ALL':
            with schema.db_select(self.parentApp.appParameters.engine) as db:
                groups = db.query(schema.Group).all()
            for group in groups:
                self.GroupList.append(group.name)
        else:
            self.GroupList.append(self.parentApp.appParameters.user_info.group)

    def beforeEditing(self):
        if self.parentApp.appParameters.user_info.group == 'ALL':
            self.Group.hidden = False
            self.Group.value = 0
        else:
            self.Group.value = 0
        if self.Edit == 0:
            self.name = 'Создать новую директорию'
        else:
            self.name = 'Редактировать'
            with schema.db_select(self.parentApp.appParameters.engine) as db:
                host = db.query(schema.Host).filter(schema.Host.id == self.Edit).one()
            self.DirName.value = host.name
            self.Note.value = host.note

    def on_cancel(self):
        self.parentApp.switchFormPrevious()

    def on_ok(self):
        if self.Edit == 0:
            with schema.db_select(self.parentApp.appParameters.engine) as db:
                count = db.query(schema.Host).filter(schema.Host.name == self.DirName.value). \
                    filter(schema.Host.type == 2). \
                    filter(schema.Host.group == self.Group.values[self.Group.value[0]]).count()
            if self.DirName.value != '' and count == 0:
                new_dir = schema.Host(name='{0}'.format(self.DirName.value),
                                      type=2,
                                      note='{0}'.format(self.Note.value),
                                      parent=self.Parent,
                                      transit=False,
                                      remote=False,
                                      remove=False,
                                      group=self.Group.values[self.Group.value[0]])
                with schema.db_edit(self.parentApp.appParameters.engine) as db:
                    db.add(new_dir)
                    db.flush()
                    db.add(schema.Action(action_type=10,
                                         user=self.parentApp.appParameters.aaa_user.uid,
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
            with schema.db_select(self.parentApp.appParameters.engine) as db:
                db.query(schema.Host).filter(schema.Host.id == self.Edit). \
                    update({schema.Host.name: self.DirName.value,
                            schema.Host.note: self.Note.value,
                            schema.Host.group: self.Group.values[self.Group.value[0]]})
                db.add(schema.Action(action_type=11,
                                     user=self.parentApp.appParameters.aaa_user.uid,
                                     date=datetime.datetime.now(),
                                     message='Внесены изменения в host - {0}'.format(self.Edit)))
            self.parentApp.appParameters.log.debug('update directory {0}'.format(self.Edit))
            self.parentApp.switchFormPrevious()


class Interface(npyscreen.NPSAppManaged):
    appParameters = None
    keypress_timeout_default = 1

    def onStart(self):
        self.appParameters.log.debug('Запуск формы MAIN.')
        self.addForm("MAIN", HostListDisplay)
