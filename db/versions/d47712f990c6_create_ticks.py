"""create ticks

Revision ID: d47712f990c6
Revises:
Create Date: 2019-08-16 17:52:49.530563

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd47712f990c6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "historical",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("fxpair", sa.String(10), nullable=False),
        sa.Column("freq", sa.String(10), nullable=False),
        sa.Column("open", sa.Float, nullable=False),
        sa.Column("high", sa.Float, nullable=False),
        sa.Column("low", sa.Float, nullable=False),
        sa.Column("close", sa.Float, nullable=False),
    )


def downgrade():
    op.drop_table("historical")
