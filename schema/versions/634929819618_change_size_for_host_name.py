"""Change size for Host.name

Revision ID: 634929819618
Revises: a8291c15d8c5
Create Date: 2022-09-09 08:28:46.899405

"""
from alembic import op
import sqlalchemy as sa
from pyrmalib import schema
from sqlalchemy.orm.exc import NoResultFound

engine = op.get_bind()

# revision identifiers, used by Alembic.
revision = '634929819618'
down_revision = 'a8291c15d8c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'host',
        'name',
        existing_type=sa.String(length=50),
        type_=sa.String(length=512),
        existing_nullable=False
    )

    with schema.db_select(engine) as db:
        try:
            action_type = db.query(schema.ActionType).filter(schema.ActionType.id == 27).one()
        except NoResultFound:
            action_type = None

    if not action_type:
        with schema.db_edit(engine) as db:
            db.add(schema.ActionType(id=27, name="Загрузка списка хостов"))
            db.flush()

def downgrade() -> None:
    pass
