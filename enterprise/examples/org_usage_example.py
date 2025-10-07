"""
Example usage of the organizational structure.

This script demonstrates how to use the new organizational tables
and store classes to manage users, roles, organizations, and settings.
"""

import sys

sys.path.append('.')

from enterprise.storage.org_store import OrgStore
from enterprise.storage.org_user_store import OrgUserStore
from enterprise.storage.role_store import RoleStore
from enterprise.storage.settings_store import SettingsStore
from enterprise.storage.user_store import UserStore


def example_usage():
    """Demonstrate the organizational structure usage."""
    print('=== Organizational Structure Example ===\n')

    # 1. Create roles
    print('1. Creating roles...')
    admin_role = RoleStore.create_role('admin', rank=1)
    member_role = RoleStore.create_role('member', rank=2)
    viewer_role = RoleStore.create_role('viewer', rank=3)
    print(
        f'   Created roles: {admin_role.name}, {member_role.name}, {viewer_role.name}'
    )

    # 2. Create organizations
    print('\n2. Creating organizations...')
    org1 = OrgStore.create_org(
        name='Acme Corp',
        contact_name='John Doe',
        contact_email='john@acme.com',
        conversation_expiration=7200,  # 2 hours
    )
    org2 = OrgStore.create_org(
        name='Tech Startup',
        contact_name='Jane Smith',
        contact_email='jane@techstartup.com',
    )
    print(f'   Created organizations: {org1.name}, {org2.name}')

    # 3. Create users
    print('\n3. Creating users...')
    user1 = UserStore.create_user(
        keycloak_user_id='user123',
        role_id=admin_role.id,
        enable_sound_notifications=True,
    )
    user2 = UserStore.create_user(
        keycloak_user_id='user456',
        role_id=member_role.id,
        enable_sound_notifications=False,
    )
    print(
        f'   Created users with Keycloak IDs: {user1.keycloak_user_id}, {user2.keycloak_user_id}'
    )

    # 4. Add users to organizations
    print('\n4. Adding users to organizations...')
    # User1 as admin in org1
    OrgUserStore.add_user_to_org(
        org_id=org1.id, user_id=user1.id, role_id=admin_role.id, status='active'
    )
    # User2 as member in org1
    OrgUserStore.add_user_to_org(
        org_id=org1.id, user_id=user2.id, role_id=member_role.id, status='active'
    )
    # User1 as viewer in org2
    OrgUserStore.add_user_to_org(
        org_id=org2.id, user_id=user1.id, role_id=viewer_role.id, status='pending'
    )
    print('   Added user relationships to organizations')

    # 5. Create settings
    print('\n5. Creating settings...')
    # User-specific settings
    SettingsStore.create_settings(
        keycloak_user_id=user1.keycloak_user_id,
        language='en',
        agent='CodeActAgent',
        max_iterations=50,
        confirmation_mode=True,
        llm_model='gpt-4',
        enable_default_condenser=True,
        enable_proactive_conversation_starters=True,
    )
    # Organization-specific settings
    SettingsStore.create_settings(
        org_id=org1.id,
        language='en',
        agent='CodeActAgent',
        max_iterations=100,
        security_analyzer='bandit',
        billing_margin=0.2,
        enable_default_condenser=False,
    )
    print('   Created user and organization settings')

    # 6. Query examples
    print('\n6. Query examples...')

    # Get user's organizations
    user_orgs = OrgUserStore.get_user_orgs(user1.id)
    print(
        f'   User {user1.keycloak_user_id} belongs to {len(user_orgs)} organizations:'
    )
    for uo in user_orgs:
        org = OrgStore.get_org_by_id(uo.org_id)
        role = RoleStore.get_role_by_id(uo.role_id)
        print(f'     - {org.name} as {role.name} ({uo.status})')

    # Get organization users
    org_users = OrgUserStore.get_org_users(org1.id)
    print(f'   Organization {org1.name} has {len(org_users)} users:')
    for ou in org_users:
        user = UserStore.get_user_by_id(ou.user_id)
        role = RoleStore.get_role_by_id(ou.role_id)
        print(f'     - {user.keycloak_user_id} as {role.name} ({ou.status})')

    # Get user settings
    user_settings_retrieved = SettingsStore.get_user_settings(user1.keycloak_user_id)
    if user_settings_retrieved:
        print(
            f'   User {user1.keycloak_user_id} settings: agent={user_settings_retrieved.agent}, '
            f'max_iterations={user_settings_retrieved.max_iterations}'
        )

    print('\n=== Example completed successfully! ===')


if __name__ == '__main__':
    # Note: This example would require a database connection to run
    # It's provided as a demonstration of the API usage
    print('This is a usage example. To run it, you would need:')
    print('1. A configured database connection')
    print('2. The migration applied to create the tables')
    print('3. Proper environment setup')
    print('\nExample API usage:')
    print("""
    # Create a role
    admin_role = RoleStore.create_role("admin", rank=1)

    # Create an organization
    org = OrgStore.create_org("My Company", contact_email="admin@company.com")

    # Create a user
    user = UserStore.create_user("keycloak_user_123", role_id=admin_role.id)

    # Add user to organization
    OrgUserStore.add_user_to_org(org.id, user.id, admin_role.id, status="active")

    # Create settings
    settings = SettingsStore.create_settings(
        keycloak_user_id=user.keycloak_user_id,
        org_id=org.id,
        language="en",
        agent="CodeActAgent"
    )
    """)
