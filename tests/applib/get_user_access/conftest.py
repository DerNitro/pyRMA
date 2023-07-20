import pytest
from datetime import datetime, timedelta
from pyrmalib.schema import Base


@pytest.fixture(scope="function")
def sqlalchemy_declarative_base():
    return Base

@pytest.fixture(scope="function")
def sqlalchemy_mock_config():
    return [("access_list", [
        {
            "t_subject":    0,
            "subject":      1,
            "t_object":     0,
            "object":       1,
            "date_disable": datetime.now() + timedelta(hours=1),
            "note":         "pytest: subject=1 object=1 date_disable=+1hour status=1",
            "conn_access":  0,
            "user_access":  0,
            "status":       1
        }
    ])]
