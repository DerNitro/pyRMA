import pytest
from datetime import datetime, timedelta
from pyrmalib.schema import Base


@pytest.fixture(scope="function")
def sqlalchemy_declarative_base():
    return Base

@pytest.fixture(scope="function")
def sqlalchemy_mock_config():
    return [("request_access", [
        {
            "user":             1,
            "host":             1,
            "date_request":     datetime.now() - timedelta(days=1),
            "date_access":      datetime.now() + timedelta(days=1),
            "status":           1,
            "ticket":           "TEST1",
            "note":             "Test: check_access_request,  date_access: plus 1 day",
            "connection":       True,
            "file_transfer":    False,
            "ipmi":             False
        },
        # interface.py/AccessRequest
        {
            "user":             1,
            "host":             1,
            "date_request":     datetime.now() - timedelta(days=1),
            "date_access":      datetime.now() + timedelta(days=1),
            "status":           0,
            "ticket":           "TEST2",
            "note":             "Test: check_access_request,  date_access: plus 1 day",
            "connection":       True,
            "file_transfer":    False,
            "ipmi":             False
        },
        # interface.py/AccessRequest stink 
        {
            "user":             1,
            "host":             1,
            "date_request":     datetime.now() - timedelta(days=2),
            "date_access":      datetime.now() - timedelta(days=1),
            "status":           0,
            "ticket":           "TEST2",
            "note":             "Test: check_access_request, date_access: minus 1 day",
            "connection":       True,
            "file_transfer":    False,
            "ipmi":             False
        },
    ])]
