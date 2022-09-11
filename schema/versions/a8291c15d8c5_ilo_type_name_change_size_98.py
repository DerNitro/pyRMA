"""ilo_type.name change size 98

Revision ID: a8291c15d8c5
Revises: 28c522f6b0d8
Create Date: 2022-08-05 07:57:57.452935

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8291c15d8c5'
down_revision = '28c522f6b0d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'ilo_type',
        'name',
        existing_type=sa.String(length=10),
        type_=sa.String(length=256),
        existing_nullable=False
    )


def downgrade() -> None:
    pass
