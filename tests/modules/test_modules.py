from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from pyrmalib import modules, schema


@pytest.fixture(scope="function")
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={'check_same_thread': False},
        poolclass=StaticPool
    )
    schema.Base.metadata.create_all(eng)
    return eng


class MockAppParam:
    def __init__(self, engine):
        self.engine = engine
        class MockLog:
            def debug(self, msg): pass
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg, pr=False): pass
        self.log = MockLog()
        class MockUserInfo:
            uid = 1
        self.user_info = MockUserInfo()
        self.session = 123
        self.app_ip_address = "127.0.0.1"
        self.ssh_client_ip = "127.0.0.1"


def test_modules_base():
    m = modules.Modules()
    assert repr(m) is not None


@patch('pyrmalib.modules.SSHTunnelForwarder')
@patch('pyrmalib.applib.get_jump_host', return_value=None)
@patch('pyrmalib.applib.tcp_forward_connection_is_active', return_value=False)
@patch('pyrmalib.applib.tcp_forward_connection')
def test_connection_modules_lifecycle(mock_tcp_forward, mock_tcp_active, mock_get_jump, mock_ssh_tunnel, engine):
    mock_tunnel_instance = MagicMock()
    mock_tunnel_instance.tunnel_bindings = {('127.0.0.1', 80): ('127.0.0.1', 12345)}
    mock_ssh_tunnel.return_value = mock_tunnel_instance

    param = MockAppParam(engine)
    host = schema.Host(id=1, name="test", ip="192.168.1.10", tcp_port=22)

    cm = modules.ConnectionModules(param, host)
    cm.NAME = "SSH"
    cm.CONNECTION_TYPE = 1
    cm.SERVICE = [{'name': 'srv', 'remote_ip': '127.0.0.1', 'remote_port': 80, 'local_port': 8080, 'describe': 'test'}]
    cm.LOGIN = "user"
    cm.PASSWORD = "pass"

    assert repr(cm) is not None

    cm.run()
    assert cm.connection_id is not None

    cm.connection()
    cm.firewall('open')
    cm.close()
