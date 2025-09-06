"""Add cost and token metrics columns to conversation_metadata table.

Revision ID: 023
Revises: 022
Create Date: 2025-04-07

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade():
    # Add cost and token metrics columns to conversation_metadata table
    op.add_column(
        'conversation_metadata',
        sa.Column('accumulated_cost', sa.Float(), nullable=True, server_default='0.0'),
    )
    op.add_column(
        'conversation_metadata',
        sa.Column('prompt_tokens', sa.Integer(), nullable=True, server_default='0'),
    )
    op.add_column(
        'conversation_metadata',
        sa.Column('completion_tokens', sa.Integer(), nullable=True, server_default='0'),
    )
    op.add_column(
        'conversation_metadata',
        sa.Column('total_tokens', sa.Integer(), nullable=True, server_default='0'),
    )


def downgrade():
    # Remove cost and token metrics columns from conversation_metadata table
    op.drop_column('conversation_metadata', 'accumulated_cost')
    op.drop_column('conversation_metadata', 'prompt_tokens')
    op.drop_column('conversation_metadata', 'completion_tokens')
    op.drop_column('conversation_metadata', 'total_tokens')
