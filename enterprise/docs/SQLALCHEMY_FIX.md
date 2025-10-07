# SQLAlchemy Relationship Resolution Fix

## Problem
When calling `get_user_by_keycloak_id` in `app/storage/user_store.py`, the following error occurred:

```
sqlalchemy.exc.InvalidRequestError: One or more mappers failed to initialize - can't proceed with initialization of other mappers. Triggering mapper: 'Mapper[User(user)]'. Original exception was: When initializing mapper Mapper[User(user)], expression 'Role' failed to locate a name ('Role'). If this is a class name, consider adding this relationship() to the <class 'storage.user.User'> class after both dependent classes have been defined.
```

## Root Cause
The error occurs because SQLAlchemy tries to resolve the relationship between `User` and `Role` models when the `User` model is imported, but the `Role` class hasn't been imported yet and is not available in the module registry.

The `User` model has:
```python
role = relationship('Role', back_populates='users')
```

And the `Role` model has:
```python
users = relationship('User', back_populates='role')
```

When `user_store.py` imports only the `User` model, SQLAlchemy cannot find the `Role` class to establish the relationship.

## Solution
Created a centralized model registration system by adding `storage/__init__.py` that imports all models:

1. **Created `storage/__init__.py`** - Imports all SQLAlchemy models to ensure they're registered with the declarative base
2. **Updated store files** - Added `import storage` to ensure all models are loaded before any database operations
3. **Updated migrations** - Added storage import to `migrations/env.py`
4. **Updated tests** - Added storage import to `tests/unit/conftest.py`

## Files Modified

### New Files
- `app/storage/__init__.py` - Central model registry
- `app/storage/README.md` - Documentation for the storage module

### Modified Files
- `app/storage/user_store.py` - Added `import storage`
- `app/storage/role_store.py` - Added `import storage`
- `app/storage/org_user_store.py` - Added `import storage`
- `app/storage/settings_store.py` - Added `import storage`
- `app/storage/org_store.py` - Added `import storage`
- `app/storage/saas_secrets_store.py` - Added `import storage`
- `app/storage/saas_settings_store.py` - Added `import storage`
- `app/migrations/env.py` - Added `import storage`
- `app/tests/unit/conftest.py` - Added `import storage`

## How It Works
By importing the `storage` module at the top of store files, all models are loaded and registered with SQLAlchemy's declarative base before any database operations occur. This ensures that all relationships can be properly resolved regardless of import order.

## Future Maintenance
When adding new models:
1. Create the model file in the storage directory
2. Add the import to `storage/__init__.py`
3. Add the model name to the `__all__` list in `__init__.py`
4. Use `import storage` in any store files that use the model

This pattern prevents similar relationship resolution errors in the future.
