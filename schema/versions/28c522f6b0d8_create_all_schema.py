"""create all schema

Revision ID: 28c522f6b0d8
Revises: 
Create Date: 2022-08-04 06:42:57.714014

run: PYTHONPATH='lib':$PYTHONPATH alembic revision -m ""
"""
from alembic import op
from sqlalchemy.engine.reflection import Inspector
from pyrmalib import schema, dict

# revision identifiers, used by Alembic.
revision = '28c522f6b0d8'
down_revision = None
branch_labels = None
depends_on = None

engine = op.get_bind()
inspector = Inspector.from_engine(engine)


def upgrade() -> None:
    pass
    tables = [
        schema.AccessList,
        schema.Action,
        schema.ActionType,
        schema.Connection,
        schema.ConnectionType,
        schema.FileTransferType,
        schema.Group,
        schema.GroupHost,
        schema.GroupUser,
        schema.Host,
        schema.IPMIType,
        schema.PasswordList,
        schema.Permission,
        schema.Prefix,
        schema.RequestAccess,
        schema.JumpHost,
        schema.Service,
        schema.ServiceType,
        schema.Session,
        schema.User,
        schema.ForwardTCP,
        schema.FileTransfer,
        schema.CaptureTraffic,
    ]

    for table in tables:
        if table.__tablename__ not in inspector.get_table_names():
            table.__table__.create(bind=engine)

    with schema.db_select(engine) as db:
        action_type = db.query(schema.ActionType).all()
        groups = db.query(schema.Group).all()
        connection_type = db.query(schema.ConnectionType).all()

    if len(action_type) == 0:
        for key, value in dict.action_type.items():
            with schema.db_edit(engine) as db:
                db.add(schema.ActionType(id=key, name=value))
                db.flush()

    if len(groups) == 0:
        with schema.db_edit(engine) as db:
            db.add(schema.Group(id=0, name='ALL'))
            db.flush()

    if len(connection_type) == 0:
        with schema.db_edit(engine) as db:
            db.add(schema.ConnectionType(name='SSH'))
            db.add(schema.ConnectionType(name='TELNET'))
            db.add(schema.FileTransferType(name='SFTP'))
            db.flush()


def downgrade() -> None:
    pass
