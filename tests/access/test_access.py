from datetime import datetime, timedelta
from unittest.mock import patch

from pyrmalib import access, schema


class MockParameters:
    """Мок-класс параметров приложения для тестирования access.py"""
    def __init__(self, engine):
        self.engine = engine
        class MockLog:
            def debug(self, msg): pass
            def critical(self, msg): pass
            def info(self, msg): pass
        self.log = MockLog()
        class MockUserInfo:
            uid = 1
            full_name = "Администратор"
        self.user_info = MockUserInfo()


def test_user_access_class():
    """Тестирование класса UserAccess"""
    u_acc = access.UserAccess(0)
    assert u_acc.get('ShowHostInformation') is False
    u_acc.change('ShowHostInformation', set_access=True)
    assert u_acc.get('ShowHostInformation') is True
    assert u_acc.get_int() >= 0
    assert repr(u_acc) is not None


def test_connection_access_class():
    """Тестирование класса ConnectionAccess"""
    c_acc = access.ConnectionAccess(0)
    assert c_acc.get('Connection') is False
    c_acc.change('Connection', set_access=True)
    assert c_acc.get('Connection') is True


def test_get_user_access(db_engine):
    """Тестирование функции get_user_access"""
    param = MockParameters(db_engine)
    with schema.db_select(db_engine) as db:
        host = db.query(schema.Host).filter(schema.Host.id == 1).one()
        user = db.query(schema.User).filter(schema.User.uid == 1).one()

    user_acc_int, conn_acc_int = access.get_user_access(param, user.uid, host)
    assert isinstance(user_acc_int, int)
    assert isinstance(conn_acc_int, int)


def test_check_access(db_engine):
    """Тестирование функции check_access"""
    param = MockParameters(db_engine)
    with schema.db_select(db_engine) as db:
        host = db.query(schema.Host).filter(schema.Host.id == 1).one()

    # Проверка доступа
    res = access.check_access(param, 'ShowHostInformation', h_object=host, user=1)
    assert isinstance(res, bool)


def test_users_access_list(db_engine):
    """Тестирование функции users_access_list"""
    param = MockParameters(db_engine)
    users = access.users_access_list(param, 'ShowHostInformation')
    assert users is None or isinstance(users, list)


@patch('pyrmalib.mail.send_mail')
def test_request_access(mock_send_mail, db_engine):
    """Тестирование функции request_access"""
    mock_send_mail.return_value = True
    param = MockParameters(db_engine)
    with schema.db_edit(db_engine) as db:
        req = schema.RequestAccess(
            user=1,
            host=1,
            ticket="TEST-TICKET",
            note="Запрос на тест",
            date_request=datetime.now(),
            date_access=datetime.now() + timedelta(days=1),
            status=0,
            connection=True,
            file_transfer=False,
            ipmi=False
        )
        db.add(req)
        db.flush()

    res = access.request_access(param, req)
    assert res is True


@patch('pyrmalib.access.get_user_access', return_value=(0, 0))
@patch('pyrmalib.mail.send_mail')
def test_access_request(mock_send_mail, mock_get_user_access, db_engine):
    """Тестирование функции access_request"""
    mock_send_mail.return_value = True
    param = MockParameters(db_engine)
    with schema.db_edit(db_engine) as db:
        user = db.query(schema.User).filter(schema.User.uid == 1).one()
        host = db.query(schema.Host).filter(schema.Host.id == 1).one()
        req = schema.RequestAccess(
            user=1,
            host=1,
            ticket="TEST-TICKET",
            note="Тестовый запрос",
            date_request=datetime.now(),
            date_access=datetime.now() + timedelta(days=1),
            status=0,
            connection=True,
            file_transfer=False,
            ipmi=False
        )
        db.add(req)
        db.flush()
        req_id = req.id

    with schema.db_select(db_engine) as db:
        req_loaded = db.query(schema.RequestAccess).filter(schema.RequestAccess.id == req_id).one()

    access_dict = {
        'access': req_loaded,
        'user': user,
        'host': host
    }

    access.access_request(param, access_dict)

    with schema.db_select(db_engine) as db:
        updated_req = db.query(schema.RequestAccess).filter(schema.RequestAccess.id == req_id).one()
        assert updated_req.status == 1


@patch('pyrmalib.mail.send_mail')
def test_deny_request(mock_send_mail, db_engine):
    """Тестирование функции deny_request"""
    mock_send_mail.return_value = True
    param = MockParameters(db_engine)
    with schema.db_edit(db_engine) as db:
        user = db.query(schema.User).filter(schema.User.uid == 1).one()
        host = db.query(schema.Host).filter(schema.Host.id == 1).one()
        req = schema.RequestAccess(
            user=1,
            host=1,
            ticket="TEST-TICKET-2",
            note="Запрос на отклонение",
            date_request=datetime.now(),
            date_access=datetime.now() + timedelta(days=1),
            status=0,
            connection=True,
            file_transfer=False,
            ipmi=False
        )
        db.add(req)
        db.flush()
        req_id = req.id

    with schema.db_select(db_engine) as db:
        req_loaded = db.query(schema.RequestAccess).filter(schema.RequestAccess.id == req_id).one()

    access_dict = {
        'access': req_loaded,
        'user': user,
        'host': host
    }

    access.deny_request(param, access_dict)

    with schema.db_select(db_engine) as db:
        updated_req = db.query(schema.RequestAccess).filter(schema.RequestAccess.id == req_id).one()
        assert updated_req.status == 2
