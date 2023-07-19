import datetime

from pyrmalib import schema

# Test worked mocked session
def test_mocked_session_access_request(mocked_session):
    access_request = mocked_session.query(schema.RequestAccess).all()
    assert len(access_request) > 0


def test_check_access_request(mocked_session):
    host_id = 1
    user_id = 1

    access_request = mocked_session.query(schema.RequestAccess).filter(
        schema.RequestAccess.host == host_id, 
        schema.RequestAccess.user == user_id,
        schema.RequestAccess.status == 0,
        schema.RequestAccess.date_access > datetime.datetime.now()
    ).one()

    assert access_request.host == host_id
    assert access_request.user == user_id
    assert access_request.status == 0
