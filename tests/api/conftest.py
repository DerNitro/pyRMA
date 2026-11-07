import os
import tempfile
from logging import handlers

import pytest
import sqlalchemy
from sqlalchemy.pool import StaticPool

from pyrmalib import parameters, schema

# Перенаправляем RotatingFileHandler во временную директорию для тестов
log_dir = tempfile.mkdtemp()
original_rotating_init = handlers.RotatingFileHandler.__init__

def mocked_rotating_file_handler_init(self, filename, *args, **kwargs):
    if filename.startswith('/var/log/pyRMA/'):
        filename = os.path.join(log_dir, os.path.basename(filename))
    original_rotating_init(self, filename, *args, **kwargs)

handlers.RotatingFileHandler.__init__ = mocked_rotating_file_handler_init

# Мокируем create_engine, чтобы при импорте api.py создавался in-memory sqlite движок
original_create_engine = sqlalchemy.create_engine

def mocked_create_engine(*args, **kwargs):
    return original_create_engine("sqlite:///:memory:", connect_args={'check_same_thread': False}, poolclass=StaticPool)

sqlalchemy.create_engine = mocked_create_engine

# Создаем временный конфигурационный файл для тестов
fd, temp_conf_path = tempfile.mkstemp()
os.close(fd)
with open(temp_conf_path, 'w') as f:
    f.write("""[Main]
app_ip_address = 127.0.0.1

[DataBase]
provider = sqlite
dbhost = localhost
dbport = 5432
dbuser = acs
dbpass = acs
dbname = acs

[Web]
ip = localhost
port = 8080
template = web
""")

parameters.pathConfigFile = temp_conf_path


@pytest.fixture(scope="function")
def db_engine():
    engine = original_create_engine(
        "sqlite:///:memory:",
        connect_args={'check_same_thread': False},
        poolclass=StaticPool
    )
    schema.Base.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    admin_user = schema.User(
        uid=1,
        login="admin",
        full_name="Администратор",
        email="admin@localhost",
        ip="127.0.0.1",
        check=1,
        admin=True
    )
    regular_user = schema.User(
        uid=2,
        login="user",
        full_name="Пользователь",
        email="user@localhost",
        ip="127.0.0.1",
        check=1,
        admin=False
    )
    session.add_all([admin_user, regular_user])
    session.commit()
    session.close()

    return engine
