"""separate saas fields from conversation metadata

Revision ID: 081
Revises: 080
Create Date: 2025-01-27 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '081'
down_revision: Union[str, None] = '080'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversation_metadata_saas table
    op.create_table(
        'conversation_metadata_saas',
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='conversation_metadata_saas_user_fkey'),
        sa.ForeignKeyConstraint(['org_id'], ['org.id'], name='conversation_metadata_saas_org_fkey'),
        sa.PrimaryKeyConstraint('conversation_id'),
    )

    # Migrate existing data from conversation_metadata to conversation_metadata_saas
    # First, we need to handle the case where user_id might be a string that needs to be converted to UUID
    op.execute("""
        INSERT INTO conversation_metadata_saas (conversation_id, user_id, org_id)
        SELECT 
            conversation_id,
            CASE 
                WHEN user_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' 
                THEN user_id::uuid
                ELSE gen_random_uuid()  -- Generate a new UUID for invalid user_id values
            END as user_id,
            COALESCE(org_id, gen_random_uuid()) as org_id  -- Use existing org_id or generate new one
        FROM conversation_metadata
        WHERE user_id IS NOT NULL
    """)

    # Remove columns from conversation_metadata table
    op.drop_constraint('conversation_metadata_org_fkey', 'conversation_metadata', type_='foreignkey')
    op.drop_column('conversation_metadata', 'github_user_id')
    op.drop_column('conversation_metadata', 'user_id')
    op.drop_column('conversation_metadata', 'org_id')


def downgrade() -> None:
    # Add columns back to conversation_metadata table
    op.add_column('conversation_metadata', sa.Column('github_user_id', sa.String(), nullable=True))
    op.add_column('conversation_metadata', sa.Column('user_id', sa.String(), nullable=False))
    op.add_column('conversation_metadata', sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Recreate foreign key constraint
    op.create_foreign_key(
        'conversation_metadata_org_fkey',
        'conversation_metadata',
        'org',
        ['org_id'],
        ['id'],
    )

    # Migrate data back from conversation_metadata_saas to conversation_metadata
    op.execute("""
        UPDATE conversation_metadata 
        SET user_id = cms.user_id::text, org_id = cms.org_id
        FROM conversation_metadata_saas cms
        WHERE conversation_metadata.conversation_id = cms.conversation_id
    """)

    # Drop conversation_metadata_saas table
    op.drop_table('conversation_metadata_saas')