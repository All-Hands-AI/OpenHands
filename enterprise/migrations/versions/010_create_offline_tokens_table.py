"""create offline tokens table.

Revision ID: 010
Revises: 009_fix_enable_sound_notifications_column
Create Date: 2024-03-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'offline_tokens',
        sa.Column('user_id', sa.String(length=255), primary_key=True),
        sa.Column('offline_token', sa.String(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            onupdate=sa.text('now()'),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table('offline_tokens')
