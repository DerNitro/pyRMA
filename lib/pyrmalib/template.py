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
          'Руководсво пользователя\n' \
          '1. Горячиие клавиши\n' \
          '\tCtrl + Q   - выход\n' \
          '\ti          - информация о хосте\n' \
          '\t+          - фильтрация\n' \
          '\tl          - Подсветка\n' \
          '\tL          - Отключить подсветку\n' \
          '\tn|p        - Переходы по подсвеченным элементам\n'

    msg = textwrap.dedent(msg)

    return msg + footer


def information_host(note):
    msg = ''
    if not isinstance(note, dict) and note:
        note = json.loads(note)
    else:
        note = note
    for key in sorted(note):
        msg += "{key}\n".format(key=key)
        msg += "{header}\n".format(header="=" * len(key))
        value = note[key]
        if len(value) > 100:
            line = ''
            for word in value.split():
                line += "{} ".format(word)
                if len(line) > 100:
                    msg += "{}\n".format(line)
                    line = ''
            msg += "{}\n\n".format(line)
        else:
            msg += "{value}\n\n".format(value=value)
        pass

    return msg


def registration_user():
    msg = "Регистрация нового пользователя {username}.\n"

    return msg + footer


if __name__ == '__main__':
    pass
