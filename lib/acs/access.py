"""
Модуль контроля и проверки правил доступа.
"""
from acs import schema
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

user_access_map = {'ShowHostInformation': 0,
                   'EditHostInformation': 1,
                   'EditDirectory': 2,
                   'EditPrefixHost': 3,
                   'DisableShowLoginPassword': 4,
                   'FileTransfer': 5,
                   'UsableService': 6,
                   'UsableOnlyService': 7,
                   'ShowAllSession': 8,
                   'ShowAllGroupSession': 9,
                   'ShowUserSession': 10,
                   'Administrate': 11}


class Access:
    map = {}

    def __init__(self, n_access):
        """
        Формируем мапинг правил доступа
        :param n_access: текущее значение доступа int
        """
        bin_str = '{0:b}'.format(n_access)[::-1].zfill(len(user_access_map))
        for access, n in user_access_map.items():
            self.map[access] = bin_str[n]

    def change(self, access, set_access=False):
        """
        Установка правила для доступа
        :param access: Правило доступа из access_map
        :param set_access: Статус правила, по умолчанию запрещен
        """
        self.map[access] = str(int(set_access))

    def get(self, access):
        """
        Возвращает значение правила доступа.
        :param access: Правило доступа из access_map
        :return: bool
        """
        return bool(int(self.map[access]))

    def get_int(self):
        """
        Воззвращает десятичное представление мапинга правил доступа
        :return: int
        """
        bin_str = []
        for i in sorted(user_access_map, key=user_access_map.get):
            bin_str.append(self.map[i])
        s = ''.join(bin_str)
        return int(s.lstrip('0')[::-1], 2)


def check_access(engine, user_id, access):
    """
    Возвращает True|False по разрещенному доступу
    :param engine: Подключение к BD в формате sqlalchemy create_engine
    :param user_id: ID пользователя в СУБД
    :param access: Правило доступа из access_map
    :return: bool
    """
    with schema.db_select(engine) as db:
        try:
            user = db.query(schema.User).filter(schema.User.login == user_id).one()
        except NoResultFound:
            return False
        except MultipleResultsFound:
            return False

    return Access(user.permissions).get(access)


def change_access(engine, user_id, access, set_access=False):
    """
    Установка правила доступа с записью в СУБД
    :param set_access: bool(), по умолчанию запретить
    :param engine: Подключение к BD в формате sqlalchemy create_engine
    :param user_id: ID пользователя в СУБД
    :param access: Правило доступа из access_map
    """
    try:
        with schema.db_select(engine) as db:
            user = db.query(schema.User).filter(schema.User.login == user_id).one()
    except NoResultFound:
        return False
    except MultipleResultsFound:
        return False

    change = Access(user.permissions)
    change.change(access, set_access=set_access)
    with schema.db_edit(engine) as db:
        db.query(schema.User).filter(schema.User.login == user_id).update({schema.User.permissions: change.get_int()})
