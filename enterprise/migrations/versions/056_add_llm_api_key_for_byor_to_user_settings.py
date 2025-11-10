"""Add llm_api_key_for_byor column to user_settings table.

Revision ID: 056
Revises: 055
Create Date: 2025-07-09
"""

import sqlalchemy as sa
from alembic import op

revision = '056'
down_revision = '055'


def upgrade() -> None:
    op.add_column(
        'user_settings',
        sa.Column('llm_api_key_for_byor', sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_column('user_settings', 'llm_api_key_for_byor')
