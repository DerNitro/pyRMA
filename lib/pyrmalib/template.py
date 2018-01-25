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

import textwrap

footer = '\nACS\nCopyright 2016, Sergey Utkin'


def restore_password():
    msg = "Для вашей учетной записи {username}, запрошено восстановление пароля.\n" \
          "Просьба пройти по следующей ссылке {url_recovery}.\n" \
          "Если вы не запрашивали пароль просьба пройти по ссылке {url_deny}\n" \
          "и сообщить администратору системы!\n"
    return msg + footer


def restore_password_access():
    msg = "Пароль для учетной записи: {login} успешно сброшен.\n"
    return msg + footer


def help_main_form():
    msg = '{program} version: {version}\n\n' \
          'Руководсво пользователя\n' \
          '1. Горячиие клавиши\n' \
          '\tq   - выход\n' \
          '\t+   - фильтрация\n' \
          '\td   - Добавить директорию\n' \
          '\ta   - Добавить новый узел\n' \
          '\te   - редактировать\n' \
          '\tl   - Подсветка\n' \
          '\tL   - Откллючить подсветку\n' \
          '\tn|p - Переходы по подсвеченным элементам\n'

    msg = textwrap.dedent(msg)

    return msg + footer
