"""Sync DB with Models

Revision ID: 001
Revises:
Create Date: 2025-10-05 11:28:41.772294

"""

from enum import Enum
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from openhands.app_server.event_callback.event_callback_models import EventCallbackStatus

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, Sequence[str], None] = None
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
