"""Add email and email_verified columns to user_settings table.

Revision ID: 054
Revises: 053
Create Date: 2025-07-02
"""

import sqlalchemy as sa
from alembic import op

revision = '054'
down_revision = '053'


def upgrade() -> None:
    op.add_column(
        'user_settings',
        sa.Column('email', sa.String, nullable=True),
    )
    op.add_column(
        'user_settings',
        sa.Column('email_verified', sa.Boolean, nullable=True),
    )


def downgrade() -> None:
    op.drop_column('user_settings', 'email_verified')
    op.drop_column('user_settings', 'email')
