# Migration 056: Organizational Structure

## Summary

This migration creates a comprehensive organizational structure based on the pgAdmin ERD schema defined in `/docs/org_tables.pgerd`. It introduces multi-tenant capabilities with proper role-based access control.

## Files Created

### Migration
- `app/migrations/versions/056_create_org_tables.py` - Alembic migration to create the organizational tables

### Models
- `app/storage/org_models.py` - SQLAlchemy models for the organizational structure

### Store Classes
- `app/storage/org_store.py` - Store classes for managing organizational entities

### Documentation
- `docs/organizational_structure.md` - Comprehensive documentation of the new structure
- `docs/migration_056_summary.md` - This summary file

### Examples
- `app/examples/org_usage_example.py` - Usage examples and API demonstration

## Tables Created

1. **`role`** - User roles with hierarchical ranking
2. **`org`** - Organizations with contact information
3. **`user`** - Users linked to Keycloak with global roles
4. **`org_user`** - Junction table for organization-user relationships with roles
5. **`settings`** - Configuration settings (user-specific or organization-specific)

## Key Features

- **Multi-tenant architecture**: Users can belong to multiple organizations
- **Role-based access control**: Both global and organization-specific roles
- **Flexible settings**: Settings can be applied at user or organization level
- **Proper foreign key constraints**: Ensures data integrity
- **Indexed columns**: Optimized for common query patterns

## Relationships

- Users have global roles and can have different roles within organizations
- Organizations can have multiple users with different roles
- Settings can be tied to specific users or organizations
- All relationships are properly constrained with foreign keys

## Usage

```python
from storage.org_store import RoleStore, OrgStore, UserStore, OrgUserStore, SettingsStore

# Create organizational structure
admin_role = RoleStore.create_role("admin", rank=1)
org = OrgStore.create_org("My Company")
user = UserStore.create_user("keycloak_123", role_id=admin_role.id)
OrgUserStore.add_user_to_org(org.id, user.id, admin_role.id, status="active")
```

## Migration Commands

### Apply Migration
```bash
cd app
alembic upgrade head
```

### Rollback Migration
```bash
cd app
alembic downgrade 055
```

## Integration Notes

- The new `settings` table coexists with the existing `user_settings` table
- Foreign key to `user.keycloak_user_id` enables integration with existing Keycloak users
- The structure is designed to be backward compatible during transition period

## Testing

All code has been validated with:
- Syntax checking
- SQLAlchemy model validation
- Pre-commit hooks (ruff, mypy, formatting)
- Import testing

The migration is ready for deployment to development/staging environments for testing.
