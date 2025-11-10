"""Add github_user_id field and rename user_id to github_user_id.

This migration:
1. Renames the existing user_id column to github_user_id
2. Creates a new user_id column
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import Column, String

# revision identifiers, used by Alembic.
revision: str = '014'
down_revision: Union[str, None] = '013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # First rename the existing user_id column to github_user_id
    op.alter_column(
        'conversation_metadata',
        'user_id',
        nullable=True,
        new_column_name='github_user_id',
    )

    # Then add the new user_id column
    op.add_column('conversation_metadata', Column('user_id', String, nullable=True))


def downgrade():
    # Drop the new user_id column
    op.drop_column('conversation_metadata', 'user_id')

    # Rename github_user_id back to user_id
    op.alter_column(
        'conversation_metadata', 'github_user_id', new_column_name='user_id'
    )
