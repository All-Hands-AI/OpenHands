"""add status and updated_at to callback

Revision ID: 080
Revises: 079
Create Date: 2025-11-05 00:00:00.000000

"""

from enum import Enum
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '080'
down_revision: Union[str, None] = '079'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('event_callback', sa.Column('status', sa.String, nullable=False, server_default='ACTIVE'))
    op.add_column('event_callback', sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('event_callback', 'status')
    op.drop_column('event_callback', 'updated_at')
