from unittest.mock import MagicMock, patch

from pyrmalib import mail, schema


class MockParam:
    def __init__(self):
        self.email = {
            'host': 'localhost',
            'port': 25,
            'type': 'smtp',
            'from': 'test@localhost'
        }
        class MockLog:
            def debug(self, msg): pass
            def exception(self, msg=""): pass
        self.log = MockLog()
        self.user_info = schema.User(uid=2, email="admin@localhost")


@patch('smtplib.SMTP')
def test_mail_class(mock_smtp_cls):
    mock_s = MagicMock()
    mock_smtp_cls.return_value = mock_s

    param = MockParam()
    m = mail.Mail(param)
    assert m.host == 'localhost'
    assert repr(m) is not None

    template = "Hello {name}"
    data = {"name": "World"}
    m.mail_to = ["user@localhost"]
    res = m.send(template, data)
    assert res is True
    mock_s.sendmail.assert_called_once()
    mock_s.quit.assert_called_once()


@patch('smtplib.SMTP')
def test_mail_send_exception(mock_smtp_cls):
    mock_smtp_cls.side_effect = Exception("SMTP connection error")

    param = MockParam()
    m = mail.Mail(param)
    m.mail_to = ["user@localhost"]
    res = m.send("Hello {name}", {"name": "World"})
    assert res is False


@patch('pyrmalib.mail.Mail.send', return_value=True)
def test_send_mail_single_user(mock_send):
    param = MockParam()
    user = schema.User(uid=1, email="user@localhost")
    res = mail.send_mail(param, "Test Subject", "Hello {name}", user, {"name": "Test"})
    assert res is True


@patch('pyrmalib.applib.get_admin_users', return_value=[schema.User(uid=2, email="admin@localhost")])
@patch('pyrmalib.mail.Mail.send', return_value=True)
def test_send_mail_list_users(mock_send, mock_get_admins):
    param = MockParam()
    users = [schema.User(uid=1, email="user1@localhost"), schema.User(uid=2, email="user2@localhost")]
    res = mail.send_mail(param, "Test Subject", "Hello {name}", users, {"name": "Test"}, admin_cc=True)
    assert res is True
