"""Add SETTING_UP_SKILLS to appconversationstarttaskstatus enum

Revision ID: 004
Revises: 003
Create Date: 2025-11-19 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, Sequence[str], None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add SETTING_UP_SKILLS enum value to appconversationstarttaskstatus."""
    # Add the new enum value to the existing enum type
    op.execute(
        "ALTER TYPE appconversationstarttaskstatus ADD VALUE 'SETTING_UP_SKILLS'"
    )


def downgrade() -> None:
    """Remove SETTING_UP_SKILLS enum value from appconversationstarttaskstatus.

    Note: PostgreSQL doesn't support removing enum values directly.
    This would require recreating the enum type and updating all references.
    For safety, this downgrade is not implemented.
    """
    # PostgreSQL doesn't support removing enum values directly
    # This would require a complex migration to recreate the enum
    # For now, we'll leave this as a no-op since removing enum values
    # is rarely needed and can be dangerous
    pass
