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
        "ticks",
        sa.Column("id", sa.String(30), primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("fxpair", sa.String(10), nullable=False),
        sa.Column("bid", sa.Float, nullable=False),
        sa.Column("ask", sa.Float, nullable=False),
        sa.Column("volume", sa.Integer, nullable=False),
    )


def downgrade():
    op.drop_table("ticks")
