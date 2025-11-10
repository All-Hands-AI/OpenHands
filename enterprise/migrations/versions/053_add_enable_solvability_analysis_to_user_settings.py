"""Add enable_solvability_analysis column to user_settings table.

Revision ID: 053
Revises: 052
Create Date: 2025-06-27
"""

import sqlalchemy as sa
from alembic import op

revision = '053'
down_revision = '052'


def upgrade() -> None:
    op.add_column(
        'user_settings',
        sa.Column(
            'enable_solvability_analysis', sa.Boolean, nullable=True, default=False
        ),
    )


def downgrade() -> None:
    op.drop_column('user_settings', 'enable_solvability_analysis')
