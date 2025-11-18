"""Add v1_enabled column to user_settings

Revision ID: 082
Revises: 081
Create Date: 2025-11-18 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '082'
down_revision: Union[str, None] = '081'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add v1_enabled column to user_settings table."""
    op.add_column(
        'user_settings',
        sa.Column('v1_enabled', sa.Boolean(), nullable=False, default=False),
    )


def downgrade() -> None:
    """Remove v1_enabled column from user_settings table."""
    op.drop_column('user_settings', 'v1_enabled')