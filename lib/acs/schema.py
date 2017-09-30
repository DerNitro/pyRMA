import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime
from contextlib import contextmanager

Base = declarative_base()


@contextmanager
def db_select(engine):
    cl_session = sessionmaker(bind=engine)
    session = cl_session()
    try:
        yield session
    except:
        raise
    finally:
        session.close()


@contextmanager
def db_edit(engine):
    cl_session = sessionmaker(bind=engine)
    session = cl_session()
    try:
        yield session
        session.commit()
    except:
        raise
    finally:
        session.close()


def install(engine):
    """
    Создаем таблицы
    """
    User.__table__.create(bind=engine)
    AAAUser.__table__.create(bind=engine)
    AAAGroup.__table__.create(bind=engine)
    AAAGroupList.__table__.create(bind=engine)
    Action.__table__.create(bind=engine)
    Parameter.__table__.create(bind=engine)
    RestorePassword.__table__.create(bind=engine)

    # Добавляем необходимые данные в таблицу
    cl_session = sessionmaker(bind=engine)
    session = cl_session()
    session.add(AAAUser(username='administrator',
                        uid=5000,
                        homedir='/home/acs/',
                        shell='/acs.sh',
                        password='admin'))

    session.add(User(login=5000,
                     full_name='Super Administrator',
                     permissions='all',
                     ip='0.0.0.0/0',
                     prefix='JANUARY'))

    session.add(AAAGroup(gid=5000, name='acs'))

    session.add(AAAGroupList(gid=5000, username='administrator'))

    session.add(Parameter(name='PASSWORD', value='0'))
    session.add(Parameter(name='CHECK_IP', value='0'))

    session.commit()
    session.close()


class User(Base):
    """
    Таблица пользователй системой доступа.
    """
    __tablename__ = 'user'

    login = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, unique=True)
    full_name = sqlalchemy.Column(sqlalchemy.String(256))
    permissions = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    date_create = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    disable = sqlalchemy.Column(sqlalchemy.BOOLEAN(), default=False)
    date_disable = sqlalchemy.Column(sqlalchemy.DateTime)
    ip = sqlalchemy.Column(sqlalchemy.String(256))
    email = sqlalchemy.Column(sqlalchemy.String(256), unique=True)
    prefix = sqlalchemy.Column(sqlalchemy.String(100))

    def __repr__(self):
        return "{0}".format(self.__dict__)


class AAAUser(Base):
    """
    Таблица для авторизации пользователей SSH PAM
    """
    __tablename__ = 'aaa_user'

    username = sqlalchemy.Column(sqlalchemy.String(16), unique=True)
    uid = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    gid = sqlalchemy.Column(sqlalchemy.Integer, default=5000)
    gecos = sqlalchemy.Column(sqlalchemy.String(128))
    homedir = sqlalchemy.Column(sqlalchemy.String(255))
    shell = sqlalchemy.Column(sqlalchemy.String(64))
    password = sqlalchemy.Column(sqlalchemy.String(34))
    lstchg = sqlalchemy.Column(sqlalchemy.BIGINT)
    min = sqlalchemy.Column(sqlalchemy.BIGINT, default=0)
    max = sqlalchemy.Column(sqlalchemy.BIGINT, default=99999)
    warn = sqlalchemy.Column(sqlalchemy.BIGINT, default=0)
    inact = sqlalchemy.Column(sqlalchemy.BIGINT, default=0)
    expire = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    flag = sqlalchemy.Column(sqlalchemy.BIGINT)

    def __repr__(self):
        return "{0}".format(self.__dict__)


class AAAGroup(Base):
    """
    Список групп PAM
    """
    __tablename__ = 'aaa_group'

    gid = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(16), default='', unique=True)
    password = sqlalchemy.Column(sqlalchemy.String(34))

    def __repr__(self):
        return "{0}".format(self.__dict__)


class AAAGroupList(Base):
    """
    Включение пользователей в группы PAM
    """
    __tablename__ = 'aaa_grouplist'

    rowid = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    gid = sqlalchemy.Column(sqlalchemy.Integer)
    username = sqlalchemy.Column(sqlalchemy.String(16))

    def __repr__(self):
        return "{0}".format(self.__dict__)


class Action(Base):
    """
    Логирование действий пользователей в системе
    int action_type:
        1 - Вход в систему доступа
        10 - Создание директории
        11 - Редактирование директории
        12 - Удаление директории
        20 - Создание хоста
        21 - Редактирование хоста
        22 - Удаление хоста
        50 - Восстановление пароля.
        51 - Изменение правил доступа.
    """
    __tablename__ = 'action'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    action_type = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    message = sqlalchemy.Column(sqlalchemy.String(256))


class Parameter(Base):
    """
    Параметры приложения.
    """
    __tablename__ = 'parameter'
    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True, unique=True)
    value = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)


class Host(Base):
    """
    Информация о узлах сети
    """
    __tablename__ = 'host'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(50))
    ip = sqlalchemy.Column(sqlalchemy.String())
    # type:
    # 1 - Директория
    # 2 - Хост
    type = sqlalchemy.Column(sqlalchemy.Integer)
    note = sqlalchemy.Column(sqlalchemy.String)
    ilo = sqlalchemy.Column(sqlalchemy.String)
    parent = sqlalchemy.Column(sqlalchemy.Integer)
    transit = sqlalchemy.Column(sqlalchemy.Boolean)
    remote = sqlalchemy.Column(sqlalchemy.Boolean)
    remove = sqlalchemy.Column(sqlalchemy.Boolean)
    default_login = sqlalchemy.Column(sqlalchemy.String)
    default_password = sqlalchemy.Column(sqlalchemy.String)
    tcp_port = sqlalchemy.Column(sqlalchemy.Integer)
    group = sqlalchemy.Column(sqlalchemy.String)


class Group(Base):
    """
    Список групп пользователей.
    """
    __tablename__ = 'group'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    note = sqlalchemy.Column(sqlalchemy.String)


class RestorePassword(Base):
    """
    Таблица запросов восстановления паролей.
    status:
    0 - Отклонен
    1 - Запрос смены пароля
    2 - Запрос выполнен
    """
    # TODO: в демон добавить контроль активных запросов.

    __tablename__ = 'restore_password'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, primary_key=True)
    status = sqlalchemy.Column(sqlalchemy.Integer)
    date = sqlalchemy.Column(sqlalchemy.DateTime)
    date_complete = sqlalchemy.Column(sqlalchemy.DateTime)
    key = sqlalchemy.Column(sqlalchemy.String)


if __name__ == '__main__':
    engine = create_engine('{0}://{1}:{2}@{3}:{4}/{5}'.format('postgresql',
                                                              'acs',
                                                              'acs',
                                                              'localhost',
                                                              '5432',
                                                              'acs'
                                                              ))
    # RestorePassword.__table__.create(bind=engine)