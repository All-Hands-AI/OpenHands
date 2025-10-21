"""create org tables from pgerd schema

Revision ID: 077
Revises: 076
Create Date: 2025-01-07 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '077'
down_revision: Union[str, None] = '076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto;')
    # Remove current settings table
    op.execute('DROP TABLE IF EXISTS settings')

    # Create role table
    op.create_table(
        'role',
        sa.Column('id', sa.Integer, sa.Identity(), primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('rank', sa.Integer, nullable=False),
        sa.UniqueConstraint('name', name='role_name_unique'),
    )

    # 1. Create default roles
    print('Creating default roles...')
    op.execute(
        sa.text("""
        INSERT INTO role (name, rank) VALUES ('admin', 1), ('user', 1000)
        ON CONFLICT (name) DO NOTHING;
    """)
    )

    # Create org table with settings fields
    op.create_table(
        'org',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('contact_name', sa.String, nullable=True),
        sa.Column('contact_email', sa.String, nullable=True),
        sa.Column('conversation_expiration', sa.Integer, nullable=True),
        # Settings fields moved to org table
        sa.Column('agent', sa.String, nullable=True),
        sa.Column('default_max_iterations', sa.Integer, nullable=True),
        sa.Column('security_analyzer', sa.String, nullable=True),
        sa.Column('confirmation_mode', sa.Boolean, nullable=True, default=False),
        sa.Column('default_llm_model', sa.String, nullable=True),
        sa.Column('_default_llm_api_key_for_byor', sa.String, nullable=True),
        sa.Column('default_llm_base_url', sa.String, nullable=True),
        sa.Column('remote_runtime_resource_factor', sa.Integer, nullable=True),
        sa.Column('enable_default_condenser', sa.Boolean, nullable=False, default=True),
        sa.Column('billing_margin', sa.Float, nullable=True),
        sa.Column(
            'enable_proactive_conversation_starters',
            sa.Boolean,
            nullable=False,
            default=True,
        ),
        sa.Column('sandbox_base_container_image', sa.String, nullable=True),
        sa.Column('sandbox_runtime_container_image', sa.String, nullable=True),
        sa.Column('org_version', sa.Integer, nullable=False, default=0),
        sa.Column('mcp_config', sa.JSON, nullable=True),
        sa.Column('_search_api_key', sa.String, nullable=True),
        sa.Column('_sandbox_api_key', sa.String, nullable=True),
        sa.Column('max_budget_per_task', sa.Float, nullable=True),
        sa.Column(
            'enable_solvability_analysis', sa.Boolean, nullable=True, default=False
        ),
        sa.UniqueConstraint('name', name='org_name_unique'),
    )

    # Create user table with user-specific settings fields
    op.create_table(
        'user',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('current_org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', sa.Integer, nullable=True),
        sa.Column('accepted_tos', sa.DateTime, nullable=True),
        sa.Column(
            'enable_sound_notifications', sa.Boolean, nullable=True, default=False
        ),
        sa.Column('language', sa.String, nullable=True),
        sa.Column('user_consents_to_analytics', sa.Boolean, nullable=True),
        sa.Column('email', sa.String, nullable=True),
        sa.Column('email_verified', sa.Boolean, nullable=True),
        sa.ForeignKeyConstraint(
            ['current_org_id'], ['org.id'], name='current_org_fkey'
        ),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], name='user_role_fkey'),
    )

    # Create org_member table (junction table for many-to-many relationship)
    op.create_table(
        'org_member',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', sa.Integer, nullable=False),
        sa.Column('_llm_api_key', sa.String, nullable=False),
        sa.Column('max_iterations', sa.Integer, nullable=True),
        sa.Column('llm_model', sa.String, nullable=True),
        sa.Column('_llm_api_key_for_byor', sa.String, nullable=True),
        sa.Column('llm_base_url', sa.String, nullable=True),
        sa.Column('status', sa.String, nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['org.id'], name='om_org_fkey'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='om_user_fkey'),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], name='om_role_fkey'),
        sa.PrimaryKeyConstraint('org_id', 'user_id'),
    )

    # Add org_id column to existing tables
    # billing_sessions
    op.add_column(
        'billing_sessions',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'billing_sessions_org_fkey', 'billing_sessions', 'org', ['org_id'], ['id']
    )

    # conversation_metadata
    op.add_column(
        'conversation_metadata',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'conversation_metadata_org_fkey',
        'conversation_metadata',
        'org',
        ['org_id'],
        ['id'],
    )

    # user_secrets
    op.add_column(
        'user_secrets',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'user_secrets_org_fkey', 'user_secrets', 'org', ['org_id'], ['id']
    )

    # api_keys
    op.add_column(
        'api_keys', sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key('api_keys_org_fkey', 'api_keys', 'org', ['org_id'], ['id'])



    # slack_conversation
    op.add_column(
        'slack_conversation',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'slack_conversation_org_fkey', 'slack_conversation', 'org', ['org_id'], ['id']
    )

    # slack_users
    op.add_column(
        'slack_users', sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'slack_users_org_fkey', 'slack_users', 'org', ['org_id'], ['id']
    )

    # stripe_customers
    op.alter_column(
        'stripe_customers',
        'keycloak_user_id',
        existing_type=sa.String(),
        nullable=True,
    )
    op.add_column(
        'stripe_customers',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'stripe_customers_org_fkey', 'stripe_customers', 'org', ['org_id'], ['id']
    )




def downgrade() -> None:
    # Drop foreign keys and columns added to existing tables
    op.drop_constraint(
        'stripe_customers_org_fkey', 'stripe_customers', type_='foreignkey'
    )
    op.drop_column('stripe_customers', 'org_id')
    op.alter_column(
        'stripe_customers',
        'keycloak_user_id',
        existing_type=sa.String(),
        nullable=False,
    )

    op.drop_constraint('slack_users_org_fkey', 'slack_users', type_='foreignkey')
    op.drop_column('slack_users', 'org_id')

    op.drop_constraint(
        'slack_conversation_org_fkey', 'slack_conversation', type_='foreignkey'
    )
    op.drop_column('slack_conversation', 'org_id')

    op.drop_constraint('api_keys_org_fkey', 'api_keys', type_='foreignkey')
    op.drop_column('api_keys', 'org_id')

    op.drop_constraint('user_secrets_org_fkey', 'user_secrets', type_='foreignkey')
    op.drop_column('user_secrets', 'org_id')

    op.drop_constraint(
        'conversation_metadata_org_fkey', 'conversation_metadata', type_='foreignkey'
    )
    op.drop_column('conversation_metadata', 'org_id')

    op.drop_constraint(
        'billing_sessions_org_fkey', 'billing_sessions', type_='foreignkey'
    )
    op.drop_column('billing_sessions', 'org_id')

    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('org_member')
    op.drop_table('user')
    op.drop_table('org')
    op.drop_table('role')
