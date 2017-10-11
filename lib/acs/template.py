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
          '\te   - редактировать\n' \
          '\tl   - Подсветка\n' \
          '\tL   - Откллючить подсветку\n' \
          '\tn|p - Переходы по подсвеченным элементам\n'

    msg = textwrap.dedent(msg)

    return msg + footer