import datetime

from pyrmalib import schema

# Test worked mocked session
def test_mocked_session_access_list(mocked_session):
    access_list = mocked_session.query(schema.AccessList).all()
    assert len(access_list) > 0

    

def test_get_user_access_hid(mocked_session):
    uid = 1
    hid = 1

    access_list = mocked_session.query(schema.AccessList).filter(
        schema.AccessList.status == 1,
        schema.AccessList.t_subject == 0,
        schema.AccessList.subject == uid,
        schema.AccessList.t_object == 0,
        schema.AccessList.object == hid,
        schema.AccessList.date_disable > datetime.datetime.now()
    ).one()

    assert access_list.status == 1
    assert access_list.subject == uid
    assert access_list.object == hid


def test_get_user_access_witout_hid(mocked_session):
    uid = 1

    access_list = mocked_session.query(schema.AccessList).filter(
        schema.AccessList.status == 1,
        schema.AccessList.t_subject == 0,
        schema.AccessList.subject == uid,
        schema.AccessList.date_disable > datetime.datetime.now()
    ).all()

    assert len(access_list) == 1
