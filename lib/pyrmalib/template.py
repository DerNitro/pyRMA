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
import json

footer = '\npyRMA\nCopyright 2016, Sergey Utkin'


def request_access():
    msg = (
        "Запрос доступа к серверу: {host}.\n"
        "В рамках заявки: {ticket}\n"
        "Дополнительная информация:\n"
        "{note}\n"
        "\n"
        "{user}\n"
    )
    return msg + footer


def deny_request():
    msg = (
        "Запрос доступа к серверу: {host} - Отклонен.\n"
        "\n"
        "{user_approve}"
    )
    return msg + footer


def access_request():
    msg = (
        "Запрос доступа к серверу: {host} - Разрешен.\n"
        "\n"
        "{user_approve}"
    )
    return msg + footer



def help_main_form():
    msg = '{program} version: {version}\n\n' \
          'Руководство пользователя\n' \
          '1. Горячие клавиши\n' \
          '\tCtrl + q   - выход\n' \
          '\ti          - информация о хосте\n' \
          '\t+          - фильтрация\n' \
          '\tl          - подсветка\n' \
          '\tL          - отключить подсветку\n' \
          '\tn|p        - переходы по подсвеченным элементам\n'

    msg = textwrap.dedent(msg)

    return msg + footer


def help_ft_form():
    msg = '{program} version: {version}\n\n' \
          'Руководство пользователя\n' \
          '1. Горячие клавиши\n' \
          '\tCtrl + q   - выход\n' \
          '\tF5         - передача файлов\n' \
          '\tF7         - создать директорию\n' \
          '\tCtrl + r   - обновить списки файлов\n' \
          '\tl          - подсветка\n' \
          '\tL          - отключить подсветку\n' \
          '\tn|p        - переходы по подсвеченным элементам\n'

    msg = textwrap.dedent(msg)

    return msg + footer

def registration_user():
    msg = "Регистрация нового пользователя {username}.\n"

    return msg + footer


if __name__ == '__main__':
    pass
