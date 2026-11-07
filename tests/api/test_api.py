from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from pyrmalib import api, error


class MockLog:
    def debug(self, msg): pass
    def critical(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass


@pytest.fixture
def api_app(db_engine):
    app = Flask(__name__)
    api.apiParameters.engine = db_engine
    api.apiParameters.log = MockLog()
    return app


@patch('pam.authenticate')
def test_verify_password_success(mock_auth, db_engine, api_app):
    mock_auth.return_value = True
    api.apiParameters.engine = db_engine
    api.apiParameters.log = MockLog()
    api.apiParameters.check_source_ip = '0'

    with api_app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
        res = api.verify_password('admin', 'correct_password')
        assert res is True
        assert api.apiParameters.user_info.login == 'admin'


@patch('pam.authenticate')
def test_verify_password_pam_fail(mock_auth, db_engine, api_app):
    mock_auth.return_value = False
    api.apiParameters.engine = db_engine
    api.apiParameters.log = MockLog()

    with api_app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
        res = api.verify_password('admin', 'wrong_password')
        assert res is False


@patch('pam.authenticate')
def test_verify_password_user_not_found(mock_auth, db_engine, api_app):
    mock_auth.return_value = True
    api.apiParameters.engine = db_engine
    api.apiParameters.log = MockLog()

    with api_app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
        res = api.verify_password('nonexistent', 'password')
        assert res is False


@patch('pam.authenticate')
def test_verify_password_not_admin(mock_auth, db_engine, api_app):
    mock_auth.return_value = True
    api.apiParameters.engine = db_engine
    api.apiParameters.log = MockLog()

    with api_app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
        res = api.verify_password('user', 'password')
        assert res is False


@patch('pam.authenticate')
def test_verify_password_ip_check_fail(mock_auth, db_engine, api_app):
    mock_auth.return_value = True
    api.apiParameters.engine = db_engine
    api.apiParameters.log = MockLog()
    api.apiParameters.check_source_ip = '1'

    with api_app.test_request_context(environ_base={'REMOTE_ADDR': '192.168.1.100'}):
        res = api.verify_password('admin', 'password')
        assert res is False


def test_unauthorized(api_app):
    api.apiParameters.log = MockLog()
    with api_app.app_context():
        resp = api.unauthorized()
        assert resp.status_code == 403
        assert resp.json == {'message': 'Unauthorized access'}


@patch('pyrmalib.applib.get_connections', return_value=[1, 2])
@patch('pyrmalib.applib.get_new_user', return_value=[])
@patch('pyrmalib.applib.get_access_request', return_value=[1])
def test_monitoring_get(mock_get_req, mock_get_new, mock_get_conn, api_app):
    api.apiParameters.log = MockLog()
    monitoring = api.Monitoring()
    result, status_code = monitoring.get()
    assert status_code == 200
    assert result == {
        "active_connection": 2,
        "new_user": 0,
        "access_request": 1
    }


@patch('pyrmalib.applib.add_hosts_file', return_value=(2, 1, 0))
def test_host_upload_post_success(mock_add_hosts, api_app):
    api.apiParameters.log = MockLog()
    host_upload = api.HostUpload()

    mock_file = MagicMock()
    mock_file.filename = 'hosts.csv'

    with api_app.test_request_context():
        with patch('pyrmalib.api.request') as mock_req:
            mock_req.files = {'file': mock_file}
            result, status_code = host_upload.post()
            assert status_code == 200
            assert result == {
                'status': 'success',
                'created host': 2,
                'updated host': 1,
                'skipped host': 0
            }
            mock_file.save.assert_called_once()


@patch('pyrmalib.applib.add_hosts_file', side_effect=error.WTF('Invalid file format'))
def test_host_upload_post_error(mock_add_hosts, api_app):
    api.apiParameters.log = MockLog()
    host_upload = api.HostUpload()

    mock_file = MagicMock()
    mock_file.filename = 'bad.csv'

    with api_app.test_request_context():
        with patch('pyrmalib.api.request') as mock_req:
            mock_req.files = {'file': mock_file}
            result, status_code = host_upload.post()
            assert status_code == 500
            assert result == {
                'status': 'error',
                'error': 'Invalid file format'
            }
