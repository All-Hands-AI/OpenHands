# Organizational Structure

This document describes the new organizational structure implemented based on the pgAdmin ERD schema in `org_tables.pgerd`.

## Overview

The organizational structure introduces a multi-tenant system where users can belong to multiple organizations with different roles. This enables better access control, settings management, and organizational boundaries.

## Database Schema

### Tables

#### `role`
Defines user roles with hierarchical ranking.
- `id` (Primary Key): Unique role identifier
- `name`: Role name (e.g., "admin", "member", "viewer") - **Unique constraint**
- `rank`: Hierarchical rank (lower numbers = higher privileges)

#### `org`
Organizations that users can belong to.
- `id` (Primary Key): Unique organization identifier
- `name`: Organization name - **Unique constraint**
- `contact_name`: Primary contact person
- `contact_email`: Contact email address
- `conversation_expiration`: Conversation expiration time in seconds

#### `user`
Users in the system, linked to Keycloak.
- `id` (Primary Key): Unique user identifier
- `keycloak_user_id`: Keycloak user identifier - **Unique constraint**
- `role_id`: Global role assignment (Foreign Key to `role.id`)
- `accepted_tos`: Timestamp when user accepted terms of service
- `enable_sound_notifications`: User preference for sound notifications

#### `org_user`
Junction table for many-to-many relationship between organizations and users.
- `org_id` (Primary Key): Organization identifier (Foreign Key to `org.id`)
- `user_id` (Primary Key): User identifier (Foreign Key to `user.id`)
- `role_id`: Role within the organization (Foreign Key to `role.id`)
- `status`: Membership status (e.g., "active", "pending", "suspended")

#### `settings`
Configuration settings that can be user-specific or organization-specific.
- `id` (Primary Key): Unique settings identifier
- `org_id`: Organization these settings apply to (Foreign Key to `org.id`)
- `keycloak_user_id`: User these settings apply to (Foreign Key to `user.keycloak_user_id`)
- `settings_version`: Version of settings schema
- Various configuration fields (language, agent, llm_model, etc.)

### Relationships

1. **User ↔ Role**: Users have a global role assignment
2. **Organization ↔ User**: Many-to-many through `org_user` table
3. **Organization ↔ Settings**: Organizations can have specific settings
4. **User ↔ Settings**: Users can have personal settings
5. **Role ↔ OrgUser**: Users have roles within specific organizations

## Store Classes

The system provides store classes for managing each entity:

### `RoleStore`
- `create_role(name, rank)`: Create a new role
- `get_role_by_id(role_id)`: Get role by ID
- `get_role_by_name(name)`: Get role by name
- `list_roles()`: List all roles ordered by rank

### `OrgStore`
- `create_org(name, ...)`: Create a new organization
- `get_org_by_id(org_id)`: Get organization by ID
- `get_org_by_name(name)`: Get organization by name
- `list_orgs()`: List all organizations
- `update_org(org_id, ...)`: Update organization details

### `UserStore`
- `create_user(keycloak_user_id, ...)`: Create a new user
- `get_user_by_id(user_id)`: Get user by ID
- `get_user_by_keycloak_id(keycloak_user_id)`: Get user by Keycloak ID
- `list_users()`: List all users
- `update_user(user_id, ...)`: Update user details

### `OrgUserStore`
- `add_user_to_org(org_id, user_id, role_id, status)`: Add user to organization
- `get_org_user(org_id, user_id)`: Get organization-user relationship
- `get_user_orgs(user_id)`: Get all organizations for a user
- `get_org_users(org_id)`: Get all users in an organization
- `update_user_role_in_org(...)`: Update user's role in organization
- `remove_user_from_org(org_id, user_id)`: Remove user from organization

### `SettingsStore`
- `create_settings(...)`: Create new settings
- `get_settings_by_id(settings_id)`: Get settings by ID
- `get_user_settings(keycloak_user_id)`: Get user-specific settings
- `get_org_settings(org_id)`: Get organization-specific settings
- `update_settings(settings_id, ...)`: Update settings

## Migration

The migration `056_create_org_tables.py` creates all the necessary tables with proper foreign key constraints and indexes.

### Running the Migration

```bash
cd app
alembic upgrade head
```

### Rolling Back

```bash
cd app
alembic downgrade 055
```

## Usage Examples

See `app/examples/org_usage_example.py` for comprehensive usage examples.

### Basic Usage

```python
from storage.org_store import RoleStore, OrgStore, UserStore, OrgUserStore, SettingsStore

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
```

## Integration with Existing System

The new organizational structure is designed to coexist with the existing `user_settings` table. The new `settings` table provides more flexibility with organization-level settings while maintaining user-specific configurations.

### Migration Strategy

1. **Phase 1**: Deploy the new tables alongside existing ones
2. **Phase 2**: Migrate existing user data to the new structure
3. **Phase 3**: Update application code to use the new organizational model
4. **Phase 4**: Deprecate old user_settings table (if desired)

## Security Considerations

- All foreign key constraints are properly defined
- Unique constraints prevent duplicate relationships
- Role-based access control is enforced through the role hierarchy
- Organization boundaries are maintained through the org_user relationships

## Performance Considerations

- Indexes are created on frequently queried columns
- Foreign key relationships enable efficient joins
- The junction table pattern allows for scalable many-to-many relationships
