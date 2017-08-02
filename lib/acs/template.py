footer = '\nACS'


def restore_password():
    msg = "Для вашей учетной записи {username}, запрошено восстановление пароля.\n" \
          "Просьба пройти по следующей ссылке {url_recovery}.\n" \
          "Если вы не запрашивали пароль просьба пройти по ссылке {url_deny}\n" \
          "и сообщить администратору системы!\n"
    return msg + footer


def restore_password_access():
    msg = "Пароль для учетной записи: {login} успешно сброшен.\n"
    return msg + footer
