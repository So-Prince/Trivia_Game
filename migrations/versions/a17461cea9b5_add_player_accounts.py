
"""Add player accounts

Revision ID: a17461cea9b5
Revises:
Create Date: 2026-11-04 15:22:03.664501
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'a17461cea9b5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('player', schema=None) as batch_op:

        batch_op.add_column(
            sa.Column('email', sa.String(length=120), nullable=True)
        )

        batch_op.add_column(
            sa.Column('password_hash', sa.String(length=255), nullable=True)
        )

        batch_op.create_unique_constraint(
            'uq_player_email',
            ['email']
        )


def downgrade():

    with op.batch_alter_table('player', schema=None) as batch_op:

        batch_op.drop_constraint(
            'uq_player_email',
            type_='unique'
        )

        batch_op.drop_column('password_hash')
        batch_op.drop_column('email')
