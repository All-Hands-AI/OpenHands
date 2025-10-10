"""add_litellm_extra_body_to_user_settings

Revision ID: d8173a9ded6d
Revises: 075
Create Date: 2025-10-10 04:57:45.212299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8173a9ded6d'
down_revision: Union[str, None] = '075'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add litellm_extra_body column to user_settings table
    op.add_column('user_settings', sa.Column('litellm_extra_body', sa.String(), nullable=True))
    
    # Add litellm_extra_body column to settings table (legacy)
    op.add_column('settings', sa.Column('litellm_extra_body', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove litellm_extra_body column from user_settings table
    op.drop_column('user_settings', 'litellm_extra_body')
    
    # Remove litellm_extra_body column from settings table (legacy)
    op.drop_column('settings', 'litellm_extra_body')
