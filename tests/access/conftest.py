from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from pyrmalib.schema import AccessList, Base, Host, RequestAccess, User


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={'check_same_thread': False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    user = User(
        uid=1,
        login="user1",
        full_name="Тестовый Пользователь",
        email="user1@localhost",
        check=1,
        admin=True
    )
    host = Host(
        id=1,
        name="testhost",
        ip="127.0.0.1",
        parent=0
    )
    req = RequestAccess(
        id=1,
        user=1,
        host=1,
        date_request=datetime.now() - timedelta(days=1),
        date_access=datetime.now() + timedelta(days=1),
        status=0,
        ticket="TICKET-1",
        note="Тестовый запрос",
        connection=True,
        file_transfer=False,
        ipmi=False
    )
    acc = AccessList(
        t_subject=0,
        subject=1,
        t_object=0,
        object=1,
        date_disable=datetime.now() + timedelta(hours=1),
        note="Тестовый доступ",
        conn_access=1,
        user_access=1,
        status=1
    )
    session.add_all([user, host, req, acc])
    session.commit()
    session.close()

    return engine
