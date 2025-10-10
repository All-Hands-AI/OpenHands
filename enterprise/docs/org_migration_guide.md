# Organizational Structure Migration Guide

This guide covers the complete migration process from the existing `user_settings` table to the new organizational structure.

## Overview

The migration consists of two parts:
1. **Migration 056**: Creates the new organizational tables (role, org, user, org_user, settings)
2. **Migration 057**: Migrates existing data from `user_settings` to the new structure

## Migration Process

### Prerequisites

1. **Backup your database** before running any migrations
2. Ensure you have access to the database and proper permissions
3. Test the migration on a staging environment first

### Step 1: Apply Schema Migration (056)

This creates the new tables without any data:

```bash
cd app
alembic upgrade 056
```

**What this does:**
- Creates `role` table for user roles
- Creates `org` table for organizations
- Creates `user` table linked to Keycloak
- Creates `org_user` junction table for user-organization relationships
- Creates `settings` table for configuration (user or org specific)
- Adds all necessary foreign keys, indexes, and constraints

### Step 2: Apply Data Migration (057)

This migrates existing user data to the new structure using batched processing:

```bash
cd app
alembic upgrade 057
```

**What this does:**
1. **Creates default roles:**
   - `admin` role with rank 1 (highest privilege)
   - `user` role with rank 1000 (standard privilege)

2. **Processes users in batches of 500** to avoid memory issues and long transactions

3. **For each user in `user_settings` table:**
   - Creates an organization named `user_{user_settings.id}_org`
   - Creates a user entry with `accepted_tos` and `enable_sound_notifications` from user_settings
   - Links the user to their organization with `admin` role
   - Creates organization-level settings with all fields from user_settings

**Performance Features:**
- Batched processing (500 users per batch) for large datasets
- Progress reporting during migration
- Error handling with detailed logging
- Optimized for 23,000+ user records

### Step 3: Verify Migration

After running both migrations, verify the data:

```sql
-- Check that roles were created
SELECT * FROM role ORDER BY rank;

-- Check that users were migrated
SELECT COUNT(*) FROM "user";
SELECT COUNT(*) FROM user_settings WHERE keycloak_user_id IS NOT NULL;
-- These counts should match

-- Check that organizations were created (one per user)
SELECT COUNT(*) FROM org;

-- Check that user-org relationships exist
SELECT COUNT(*) FROM org_user;

-- Check that settings were migrated
SELECT COUNT(*) FROM settings;

-- Sample data verification
SELECT
    u.keycloak_user_id,
    o.name as org_name,
    r.name as role_name,
    ou.status,
    s.language,
    s.agent
FROM "user" u
JOIN org_user ou ON u.id = ou.user_id
JOIN org o ON ou.org_id = o.id
JOIN role r ON ou.role_id = r.id
LEFT JOIN settings s ON s.org_id = o.id
LIMIT 5;
```

## Post-Migration Structure

After migration, each user will have:

1. **Personal Organization**: Named `user_{original_id}_org`
2. **Admin Role**: In their personal organization
3. **User Entry**: With Keycloak ID and TOS acceptance status
4. **Organization Settings**: All their original user_settings as org-level settings

## Rollback Process

If you need to rollback the migrations:

```bash
# Rollback data migration first
cd app
alembic downgrade 056

# Then rollback schema migration
alembic downgrade 055
```

**Warning**: Rolling back migration 057 will delete all organizational data. The original `user_settings` table remains unchanged, so user data is preserved.

## Migration Strategy Options

### Option 1: Direct Migration (Recommended for smaller datasets)
Run both migrations in sequence as described above.

### Option 2: Gradual Migration (For large datasets)
1. Apply migration 056 (schema only)
2. Run migration 057 during low-traffic periods (already batched internally)
3. Monitor database performance during migration
4. Migration automatically processes 500 users per batch with progress reporting

### Option 3: Blue-Green Deployment
1. Set up parallel environment with new schema
2. Migrate data offline
3. Switch traffic to new environment
4. Keep old environment as backup

## Application Code Updates

After migration, update application code to use the new organizational structure:

### Before (using user_settings)
```python
from storage.user_settings import UserSettingsStore

settings = UserSettingsStore.get_user_settings(keycloak_user_id)
```

### After (using organizational structure)
```python
from storage.org_store import UserStore, SettingsStore

# Get user and their organization settings
user = UserStore.get_user_by_keycloak_id(keycloak_user_id)
user_orgs = OrgUserStore.get_user_orgs(user.id)
org_settings = SettingsStore.get_org_settings(user_orgs[0].org_id)
```

## Monitoring and Validation

### Key Metrics to Monitor
- Migration execution time
- Database size changes
- Query performance on new tables
- Application error rates during transition

### Validation Queries
```sql
-- Ensure no data loss
SELECT
    (SELECT COUNT(*) FROM user_settings WHERE keycloak_user_id IS NOT NULL) as original_users,
    (SELECT COUNT(*) FROM "user") as migrated_users,
    (SELECT COUNT(*) FROM org) as created_orgs,
    (SELECT COUNT(*) FROM settings) as migrated_settings;

-- Check for orphaned records
SELECT COUNT(*) FROM org_user ou
LEFT JOIN "user" u ON ou.user_id = u.id
WHERE u.id IS NULL;

-- Verify role assignments
SELECT r.name, COUNT(*) as user_count
FROM org_user ou
JOIN role r ON ou.role_id = r.id
GROUP BY r.name;
```

## Troubleshooting

### Common Issues

1. **Foreign Key Violations**
   - Ensure migration 056 completed successfully before running 057
   - Check that all referenced tables exist

2. **Duplicate Key Errors**
   - May occur if migration 057 is run multiple times
   - Check for existing data before re-running

3. **Performance Issues**
   - For large datasets, consider running migration in batches
   - Monitor database connections and memory usage

### Recovery Steps

If migration fails partway through:

1. **Check migration status:**
   ```bash
   cd app
   alembic current
   alembic history
   ```

2. **Identify failed point:**
   - Check database logs
   - Look for partially created records

3. **Clean up and retry:**
   ```bash
   # Rollback to clean state
   alembic downgrade 055

   # Re-apply migrations
   alembic upgrade 057
   ```

## Performance Considerations

### Before Migration
- Analyze current `user_settings` table size
- Estimate migration time (typically 1-2 seconds per 1000 users, batched processing)
- Plan maintenance window accordingly (for 23,000 users: ~45-90 seconds)
- Migration processes 500 users per batch automatically

### During Migration
- Monitor database CPU and memory usage
- Watch for lock contention
- Consider running during low-traffic periods

### After Migration
- Update application connection pools if needed
- Monitor query performance on new tables
- Consider adding additional indexes based on usage patterns

## Security Considerations

- Ensure database backup is encrypted
- Verify that foreign key constraints maintain data integrity
- Test role-based access control after migration
- Validate that user permissions are preserved

## Support and Rollback Plan

### Emergency Rollback
If critical issues arise post-migration:

1. **Immediate**: Switch application to read from `user_settings` table
2. **Short-term**: Rollback migrations to restore original state
3. **Long-term**: Investigate issues and plan re-migration

### Data Validation
After migration, run comprehensive tests to ensure:
- All users can log in
- Settings are preserved correctly
- Role assignments work as expected
- No data corruption occurred

This migration enables the transition to a multi-tenant organizational structure while preserving all existing user data and maintaining backward compatibility during the transition period.
