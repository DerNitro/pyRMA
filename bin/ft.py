#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8
# PYTHONPATH=./lib/ ./bin/pyrma.py


"""
       Copyright 2022, Sergey Utkin mailto:utkins01@gmail.com

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

import sys
import os
import shutil
import stat
import time
import argparse
import tarfile
from checksumdir import dirhash
import tempfile
from pyrmalib import parameters, template, error, applib, utils
import npyscreen
import curses
import pysftp
from paramiko import ssh_exception, SFTPAttributes
from paramiko.py3compat import strftime
from sqlalchemy import create_engine

__author__ = 'Sergey Utkin'
__email__ = 'utkins01@gmail.com'
__version__ = "1.0.2"
__status__ = "Stable"
__maintainer__ = "Sergey Utkin"
__copyright__ = "Copyright 2016, Sergey Utkin"
__program__ = 'pyRMA'

ftParameters = parameters.FileTransfer()

engine = create_engine(
    '{0}://{1}:{2}@{3}:{4}/{5}'.format(
        ftParameters.dbase,
        ftParameters.dbase_param["user"],
        ftParameters.dbase_param["password"],
        ftParameters.dbase_param["host"],
        ftParameters.dbase_param["port"],
        ftParameters.dbase_param["database"]
    )
)
ftParameters.engine = engine

ftParameters.log.info('запуск модуля передачи файлов - {} v.{}'.format(__program__, __version__))

parser = argparse.ArgumentParser(description='Модуль передачи файлов pyRMA')
parser.add_argument('--host', help='Узел для подключения', required=True)
parser.add_argument('--port', help='Порт подключения', required=True)
parser.add_argument('--user', help='Имя пользователя', required=True)
parser.add_argument('--password', help='Пароль пользователя', required=True)
parser.add_argument('--id',   help='ID подключения', required=True)

args = parser.parse_args()

exit_flag = 0

ftParameters.connection = applib.get_connection(ftParameters, args.id)

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
cinfo = {
    'host': args.host, 
    'username': args.user, 
    'password': args.password, 
    'port': int(args.port), 
    'cnopts': cnopts
}

ftParameters.log.info('параметры запуска: {}:{} user {}'.format(args.host, args.port, args.user))

local_path = []
remote_path = []
local_path.append(os.path.join(ftParameters.data_dir, ftParameters.file_transfer_folder))


class File(object):
    st_mode = None
    st_uid = None
    st_gid = None
    st_size = None
    st_mtime = None
    name = None

    def __init__(self, file: os.stat_result or SFTPAttributes, name=None) -> None:
        if isinstance(file, SFTPAttributes) and not name:
            self.name = file.filename
        else:
            self.name = name
        self.st_mode = file.st_mode
        self.st_uid = file.st_uid
        self.st_gid = file.st_gid
        self.st_size = file.st_size
        self.st_mtime = file.st_mtime

    def str_size(self) -> str:
        size = ''
        st_size = self.st_size
        while st_size > 1024:
            if size == '':
                size = 'K'
            elif size == 'K':
                size = 'M'
            elif size == 'M':
                size = 'G'
            elif size == 'G':
                break
            st_size = st_size // 1024

        return(str('{}{}'.format(st_size, size)))

    @staticmethod
    def _rwx(n, suid, sticky=False):
        # Copy past from paramiko import SFTPAttributes
        if suid:
            suid = 2
        out = "-r"[n >> 2] + "-w"[(n >> 1) & 1]
        if sticky:
            out += "-xTt"[suid + (n & 1)]
        else:
            out += "-xSs"[suid + (n & 1)]
        return out

    def str_mode(self) -> str:
        # Copy past from paramiko import SFTPAttributes
        kind = stat.S_IFMT(self.st_mode)
        if kind == stat.S_IFIFO:
            ks = "p"
        elif kind == stat.S_IFCHR:
            ks = "c"
        elif kind == stat.S_IFDIR:
            ks = "d"
        elif kind == stat.S_IFBLK:
            ks = "b"
        elif kind == stat.S_IFREG:
            ks = "-"
        elif kind == stat.S_IFLNK:
            ks = "l"
        elif kind == stat.S_IFSOCK:
            ks = "s"
        else:
            ks = "?"
        ks += self._rwx(
            (self.st_mode & 448) >> 6, self.st_mode & stat.S_ISUID
        )
        ks += self._rwx(
            (self.st_mode & 56) >> 3, self.st_mode & stat.S_ISGID
        )
        ks += self._rwx(
            self.st_mode & 7, self.st_mode & stat.S_ISVTX, True
        )
        return ks
    
    def __str__(self) -> str:
        # Copy past from paramiko import SFTPAttributes
        if (self.st_mtime is None):
            datestr = "(unknown date)"
        else:
            time_tuple = time.localtime(self.st_mtime)
            if abs(time.time() - self.st_mtime) > 15552000:
                datestr = strftime("%d %b %Y", time_tuple)
            else:
                datestr = strftime("%d %b %H:%M", time_tuple)

        return "%s  %-8d %-8d %6s %-12s %s" % (
            self.str_mode(),
            int(self.st_uid),
            int(self.st_gid),
            self.str_size(),
            datestr,
            self.name,
        )

    def __repr__(self) -> str:
        return str(self.__dict__)


class Mkdir(npyscreen.ActionPopup):
    is_ok = False
    
    def on_ok(self):
        self.is_ok = True
        return False

class LocalMultiLineAction (npyscreen.MultiLineAction):
    def display_value(self, vl):
        return str(vl)

    def actionHighlighted(self, record, keypress):
        ftParameters.log.debug('LocalMultiLineAction(actionHighlighted): {}'.format(str(record.name)))
        global local_path
        if stat.S_IFMT(record.st_mode) == stat.S_IFDIR and record.name != '..':
            local_path.append(record.name)
        if stat.S_IFMT(record.st_mode) == stat.S_IFDIR and record.name == '..':
            local_path.pop()

        ftParameters.log.debug('local_path: {}'.format(local_path))
        self.parent.update_files()

class RemoteMultiLineAction (npyscreen.MultiLineAction):
    def display_value(self, vl):
        return str(vl)

    def actionHighlighted(self, record, keypress):
        ftParameters.log.debug('RemoteMultiLineAction(actionHighlighted): {}'.format(str(record.name)))
        global remote_path
        if stat.S_IFMT(record.st_mode) == stat.S_IFDIR and record.name != '..':
            remote_path.append(record.name)
        if stat.S_IFMT(record.st_mode) == stat.S_IFDIR and record.name == '..':
            remote_path.pop()

        ftParameters.log.debug('remote_path: {}'.format(remote_path))
        self.parent.update_files()

class LocalBoxBasic(npyscreen.BoxTitle):
    bx_width = 0
    _contained_widget = LocalMultiLineAction

class RemoteBoxBasic(npyscreen.BoxTitle):
    bx_width = 0
    _contained_widget = RemoteMultiLineAction

class FT(npyscreen.FormBaseNew):
    @staticmethod
    def xy():
        max_y, max_x = curses.newwin(0, 0).getmaxyx()
        max_y -= 1
        max_x -= 1
        return max_y, max_x

    def app_exit(self, *args, **keywords):
        global exit_flag
        exit_flag = 1
        self.parentApp.switchForm(None)

    def create(self):
        self.cycle_widgets = True
        lines, columns = self.xy()
        self.bx_width = (columns // 2) - 2
        
        self.source = self.add(LocalBoxBasic, name = 'acs', max_width=self.bx_width)
        self.dest = self.add(
            RemoteBoxBasic, 
            name = ftParameters.connection['host'].name, rely=2, max_width=self.bx_width, relx=self.bx_width + 2
        )


    def update_files(self, *args, **keywords):
        lines, columns = self.xy()
        
        if self.bx_width != (columns // 2) - 2:
            self.parentApp.switchForm(None)

        try:
            self.source.values = self.get_local_files(os.path.join(*local_path))
        except error.ErrorGetListFiles as e:
            local_path.pop()
            ftParameters.log.warning(e)
        self.source.update()

        try:
            self.dest.values = self.get_remote_files()
        except error.ErrorGetListFiles as e:
            remote_path.pop()
            ftParameters.log.warning(e)
        self.dest.update()

    def mkdir(self, *args, **keywords):
        form = Mkdir()
        path = form.add_widget(npyscreen.TitleText, name='Имя')
        form.edit()
        ftParameters.log.debug('FT(mkdir) form: {}'.format(str(form.__dict__)))
        if self.source.editing and form.is_ok:
            if os.path.isdir(os.path.join(*local_path, path.value)):
                ftParameters.log.warning(
                    'не возможно создать директорию {} - уже существует'.format(
                        str(os.path.join(*local_path, path.value))
                    )
                )
                npyscreen.notify_confirm("Директория уже существует", title="Создание директории", wide=True)
            else:
                try:
                    os.mkdir(os.path.join(*local_path, path.value))
                    ftParameters.log.info(
                            "создана директория: {}".format(str(os.path.join(*local_path, path.value)))
                        )
                except OSError as e:
                    ftParameters.log.warning("{}".format(str(e)))
                    npyscreen.notify_confirm("{}".format(str(e)), title="Создание директории", wide=True)
        
        if self.dest.editing and form.is_ok:
            with pysftp.Connection(**cinfo) as sftp:
                if sftp.isdir(os.path.join(*remote_path, path.value)):
                    ftParameters.log.warning(
                        'не возможно создать директорию {} - уже существует'.format(
                            str(os.path.join(*remote_path, path.value))
                        )
                    )
                    npyscreen.notify_confirm("Директория уже существует", title="Создание директории", wide=True)
                else:
                    try:
                        sftp.mkdir(os.path.join(*remote_path, path.value))
                        ftParameters.log.info(
                            "создана директория: {}".format(str(os.path.join(*remote_path, path.value)))
                        )
                    except OSError as e:
                        ftParameters.log.warning("{}".format(str(e)))
                        npyscreen.notify_confirm("{}".format(str(e)), title="Создание директории", wide=True)
        self.update_files()

    def beforeEditing(self):
        self.add_handlers(
            {
                '^Q': self.app_exit,
                '^R': self.update_files,
                "KEY_F(5)": self.transfer,
                curses.KEY_F5: self.transfer,
                "KEY_F(7)": self.mkdir,
                curses.KEY_F7: self.mkdir
            }
        )
        self.help = template.help_ft_form().format(program=__program__, version=__version__)

        try:
            self.source.values = self.get_local_files(os.path.join(*local_path))
        except PermissionError:
            error.WTF('Нет доступа к локальной директории')
            ftParameters.log.error(
                'Нет доступа к локальной директории передачи файлов: {}'.format(str(os.path.join(*local_path)))
            )
            sys.exit('PermissionError: '.format(str(os.path.join(*local_path))))
        self.dest.values = self.get_remote_files()

    def get_local_files(self, path=os.path.join(ftParameters.data_dir, ftParameters.file_transfer_folder)):
        file_list = []
        if not path == os.path.join(ftParameters.data_dir, ftParameters.file_transfer_folder):
            file_list.append(
                File(os.stat(os.path.join(path)), name='..')
            )

        try:
            dirs = [d for d in sorted(os.listdir(path)) if os.path.isdir(os.path.join(path, d))]
            files = [f for f in sorted(os.listdir(path)) if os.path.isfile(os.path.join(path, f))]
        except PermissionError as e:
            npyscreen.notify_confirm(
                "Ошибка получения списка файлов\n" + e.strerror,
                title="Передача данных", wide=True)
            raise error.ErrorGetListFiles('Ошибка получения списка файлов: {}'.format(path))
        
        allList = sorted(dirs) + sorted(files)

        for f in allList:
            file_list.append(
                File(os.stat(os.path.join(path, f)), name=f)
            )
            
        ftParameters.log.debug('FT(get_local_files): {}'.format(file_list))
        return file_list

    def get_remote_files(self):
        file_list = []
        with pysftp.Connection(**cinfo) as sftp:
            parent_folder = sftp.stat(remotepath=os.path.join(*remote_path))
            try:
                remote_files = sftp.listdir_attr(remotepath=os.path.join(*remote_path))
                dirs = [d for d in remote_files if sftp.isdir(remotepath=os.path.join(*remote_path, d.filename))]
                files = [f for f in remote_files if sftp.isfile(remotepath=os.path.join(*remote_path, f.filename))]
            except PermissionError as e:
                npyscreen.notify_confirm(
                    "Ошибка получения списка файлов\n" + e.strerror,
                    title="Передача данных", wide=True)
                raise error.ErrorGetListFiles(
                    'Ошибка получения списка файлов удаленного узла: {}'.format(os.path.join(*remote_path))
                )

        allList = dirs + files

        if len(remote_path) > 1:
            file_list.append(File(parent_folder, name='..'))
        
        for f in allList:
            file_list.append(File(f))
        ftParameters.log.debug('FT(get_remote_files): - {}'.format(file_list))
        return file_list
    
    def transfer(self, *args, **keywords):
        try:
            if self.source.editing:
                for widget in self.source._my_widgets:
                    if isinstance(widget, LocalMultiLineAction):
                        selected = self.source.values[widget.cursor_line]
                        break
                ftParameters.log.debug('FT(transfer): upload - {}'.format(str(os.path.join(*local_path, selected.name))))
                with pysftp.Connection(**cinfo) as sftp:
                    if stat.S_IFMT(selected.st_mode) == stat.S_IFDIR:
                        self.notify('start')
                        try:
                            if not sftp.isdir(os.path.join(*remote_path, selected.name)):
                                sftp.mkdir(remotepath=os.path.join(*remote_path, selected.name))
                            sftp.put_r(
                                os.path.join(*local_path, selected.name), remotepath=os.path.join(*remote_path, selected.name)
                            )
                            self.store_backup_file(os.path.join(*local_path, selected.name), 'upload')
                            self.notify('stop')
                            ftParameters.log.info('передана директория: {}'.format(str(os.path.join(*local_path, selected.name))))
                        except PermissionError:
                            npyscreen.notify_confirm(
                                'PermissionError',
                                title="Ошибка передачи файла", wide=True)
                            ftParameters.log.warning('Ошибка передачи файла PermissionError: {}'.format(str(os.path.join(*local_path, selected.name))))
                    if stat.S_IFMT(selected.st_mode) == stat.S_IFREG:
                        self.notify('start')
                        try:
                            sftp.put(
                                os.path.join(*local_path, selected.name), remotepath=os.path.join(*remote_path, selected.name)
                            )
                            self.store_backup_file(os.path.join(*local_path, selected.name), 'upload')
                            self.notify('stop')
                            ftParameters.log.info('передан файл: {}'.format(str(os.path.join(*local_path, selected.name))))
                        except PermissionError:
                            npyscreen.notify_confirm(
                                'PermissionError',
                                title="Ошибка передачи файла", wide=True)
                            ftParameters.log.warning('Ошибка передачи файла PermissionError: {}'.format(str(os.path.join(*local_path, selected.name))))
            
            if self.dest.editing:
                for widget in self.dest._my_widgets:
                    if isinstance(widget, RemoteMultiLineAction):
                        selected = self.dest.values[widget.cursor_line]
                        break
                ftParameters.log.debug('FT(transfer): download - {}'.format(str(os.path.join(*remote_path, selected.name))))
                with pysftp.Connection(**cinfo) as sftp:
                    if stat.S_IFMT(selected.st_mode) == stat.S_IFDIR:
                        self.notify('start')
                        sftp.cwd(os.path.join(*remote_path))
                        try:
                            sftp.get_r(
                                os.path.join(selected.name), localdir=os.path.join(*local_path)
                            )
                            self.store_backup_file(os.path.join(*local_path, selected.name), 'download')
                            self.notify('stop')
                            ftParameters.log.info('загружена директория: {}'.format(str(os.path.join(*local_path, selected.name))))
                        except PermissionError:
                            npyscreen.notify_confirm(
                                'PermissionError',
                                title="Ошибка передачи файла", wide=True)
                            ftParameters.log.warning('Ошибка передачи файла PermissionError: {}'.format(str(os.path.join(*remote_path, selected.name))))
                    if stat.S_IFMT(selected.st_mode) == stat.S_IFREG:
                        self.notify('start')
                        try:
                            sftp.get(
                                os.path.join(*remote_path, selected.name), localpath=os.path.join(*local_path, selected.name)
                            )
                            self.store_backup_file(os.path.join(*local_path, selected.name), 'download')
                            self.notify('stop')
                            ftParameters.log.info('загружен файл: {}'.format(str(os.path.join(*local_path, selected.name))))
                        except PermissionError:
                            npyscreen.notify_confirm(
                                'PermissionError',
                                title="Ошибка передачи файла", wide=True)
                            ftParameters.log.warning('Ошибка передачи файла PermissionError: {}'.format(str(os.path.join(*remote_path, selected.name))))
        except FileExistsError as e:
            npyscreen.notify_confirm(e.strerror, title="Передача данных", wide=True)
            ftParameters.log.warning('Ошибка передачи файлов ' + str(e))
        self.update_files()

    def store_backup_file(self, path, direction):
        backup_folder = '{}'.format(
            os.path.join(
                ftParameters.data_dir, 
                ftParameters.file_transfer_backup_folder,
                ftParameters.connection['host'].name)
        )

        if os.path.isfile(path):
            md5 = utils.md5(os.path.join(path))
        if os.path.isdir(path):
            md5 = dirhash(path, 'md5')

        if not os.path.isdir(backup_folder):
            os.mkdir(backup_folder)
        tar_name = '{}_{}.tar'.format(args.id, os.path.basename(path))
        with tempfile.TemporaryDirectory() as tmpdirname:
            tar = tarfile.open(os.path.join(tmpdirname, tar_name), "w")
            tar.add(path)
            tar.close()
            backup_files = applib.get_file_transfer(ftParameters, md5=md5)
            if len(backup_files) == 0:
                shutil.move(os.path.join(tmpdirname, tar_name), os.path.join(backup_folder, tar_name))
            else:
                hardlink = False
                for backup_file in backup_files:
                    if os.path.isfile(backup_file.file_name_tgz) \
                    and backup_file.file_name_tgz != str(os.path.join(backup_folder, tar_name)):
                        os.link(backup_file.file_name_tgz, os.path.join(backup_folder, tar_name))
                        hardlink = True
                        break
                if not hardlink:
                    shutil.move(os.path.join(tmpdirname, tar_name), os.path.join(backup_folder, tar_name))
        applib.set_file_transfer(
            ftParameters, 
            args.id,
            os.path.basename(path),
            os.path.join(ftParameters.file_transfer_backup_folder, ftParameters.connection['host'].name, tar_name),
            md5,
            direction
        )
        pass

    def notify(self, action):
        if action == 'start':
            npyscreen.notify_wait("Началась передача данных", title="Передача данных",)
        elif action == 'stop':
            npyscreen.notify_wait("Закончилась передача данных", title="Передача данных",)


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


class UserApp(npyscreen.NPSAppManaged):
    keypress_timeout_default = 1
    def onStart(self):
        if not connection_error:
            self.addForm("MAIN", FT)
        else:
            self.addForm("MAIN", ErrorForm)
            self.getForm("MAIN").error_text = str(e)
            ftParameters.log.error('Ошибка подключения к узлу: {}'.format(e), pr=True)

connection_error = False
try:
    sftp = pysftp.Connection(**cinfo)
    remote_path.append('/')
    for f in sftp.pwd.split('/'):
        if f != '':
            remote_path.append(f)
    sftp.close()
except (ssh_exception.AuthenticationException, ssh_exception.SSHException) as e:
    connection_error = True

while exit_flag == 0:
    ftParameters.log.debug('exit_flag: {}'.format(exit_flag))
    App = UserApp()
    App.run()

ftParameters.log.info('завершение приложения')
sys.exit(0)
