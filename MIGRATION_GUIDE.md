# Migration Guide: From Shared Globals to Context System

This guide explains how to migrate from the deprecated `openhands.server.shared` globals to the new context system.

## Overview

The new context system replaces global variables with dependency injection, providing:

- **Better testability**: Easy to mock dependencies in tests
- **SaaS extensibility**: Custom contexts for multi-tenant scenarios
- **Per-request contexts**: Different configurations per request
- **No import-time side effects**: Lazy initialization of dependencies
- **Type safety**: Better IDE support and type checking

## Quick Migration

### Before (Deprecated)
```python
from openhands.server.shared import config, server_config, file_store, sio

def my_function():
    # Use global variables
    workspace_dir = config.workspace_dir
    app_mode = server_config.app_mode
    file_store.save_file(...)
```

### After (Recommended)
```python
from fastapi import Depends, Request
from openhands.server.context import get_server_context, ServerContext

@app.get('/my-endpoint')
async def my_endpoint(
    request: Request,
    context: ServerContext = Depends(get_server_context)
):
    # Use context instead of globals
    config = context.get_config()
    server_config = context.get_server_config()
    file_store = context.get_file_store()

    workspace_dir = config.workspace_dir
    app_mode = server_config.app_mode
    file_store.save_file(...)
```

## Detailed Migration Steps

### 1. Route Handlers

**Before:**
```python
from openhands.server.shared import config, conversation_manager

@app.post('/conversations')
async def create_conversation(request: ConversationRequest):
    conversation = conversation_manager.create_conversation(
        request.user_id,
        config.default_agent
    )
    return conversation
```

**After:**
```python
from fastapi import Depends
from openhands.server.context import get_server_context, ServerContext

@app.post('/conversations')
async def create_conversation(
    request: ConversationRequest,
    context: ServerContext = Depends(get_server_context)
):
    config = context.get_config()
    conversation_manager = context.get_conversation_manager()

    conversation = conversation_manager.create_conversation(
        request.user_id,
        config.default_agent
    )
    return conversation
```

### 2. Service Classes

**Before:**
```python
from openhands.server.shared import file_store, monitoring_listener

class MyService:
    def process_file(self, file_path: str):
        content = file_store.read(file_path)
        monitoring_listener.log_event('file_processed')
        return content
```

**After:**
```python
from openhands.server.context import ServerContext

class MyService:
    def __init__(self, context: ServerContext):
        self.context = context

    def process_file(self, file_path: str):
        file_store = self.context.get_file_store()
        monitoring_listener = self.context.get_monitoring_listener()

        content = file_store.read(file_path)
        monitoring_listener.log_event('file_processed')
        return content

# In route handler:
@app.post('/process')
async def process_endpoint(
    request: ProcessRequest,
    context: ServerContext = Depends(get_server_context)
):
    service = MyService(context)
    return service.process_file(request.file_path)
```

### 3. Store Classes

**Before:**
```python
from openhands.server.shared import SettingsStoreImpl

def get_user_settings(user_id: str):
    store = SettingsStoreImpl(user_id)
    return store.load()
```

**After:**
```python
from openhands.server.context import ServerContext

def get_user_settings(user_id: str, context: ServerContext):
    SettingsStoreClass = context.get_settings_store_class()
    store = SettingsStoreClass(user_id)
    return store.load()

# In route handler:
@app.get('/settings/{user_id}')
async def get_settings(
    user_id: str,
    context: ServerContext = Depends(get_server_context)
):
    return get_user_settings(user_id, context)
```

### 4. Testing

**Before:**
```python
import pytest
from unittest.mock import patch

def test_my_function():
    with patch('openhands.server.shared.config') as mock_config:
        mock_config.workspace_dir = '/test'
        result = my_function()
        assert result == expected
```

**After:**
```python
import pytest
from openhands.server.context import create_server_context

class MockServerContext:
    def get_config(self):
        mock_config = Mock()
        mock_config.workspace_dir = '/test'
        return mock_config

def test_my_function():
    context = MockServerContext()
    result = my_function(context)
    assert result == expected
```

## SaaS Extension Example

The new context system makes it easy to extend OpenHands for SaaS scenarios:

```python
from openhands.server.context import ServerContext, set_context_class

class SaaSServerContext(ServerContext):
    def __init__(self, user_id: str, org_id: str):
        self.user_id = user_id
        self.org_id = org_id

    def get_file_store(self):
        # Return tenant-isolated file store
        return MultiTenantFileStore(self.user_id, self.org_id)

    def get_server_config(self):
        # Return SaaS-specific configuration
        return SaaSServerConfig(org_id=self.org_id)

# Configure globally
set_context_class('myapp.context.SaaSServerContext')

# Use in routes with tenant context
@app.get('/tenant/{org_id}/files')
async def get_tenant_files(
    org_id: str,
    context: SaaSServerContext = Depends(get_server_context)
):
    file_store = context.get_file_store()
    return file_store.list_files()
```

## Migration Checklist

- [ ] Replace `from openhands.server.shared import ...` with context injection
- [ ] Update route handlers to use `Depends(get_server_context)`
- [ ] Modify service classes to accept `ServerContext` parameter
- [ ] Update tests to use mock contexts instead of patching globals
- [ ] Remove direct imports of shared globals
- [ ] Test that all functionality still works

## Backward Compatibility

The old `openhands.server.shared` module still works but is deprecated. It will show deprecation warnings when imported. The globals are now implemented using the new context system internally.

## Benefits After Migration

1. **Better Testing**: Easy to mock dependencies without patching globals
2. **Type Safety**: Better IDE support and type checking
3. **Extensibility**: Easy to create custom contexts for different scenarios
4. **Performance**: Lazy initialization reduces startup time
5. **Maintainability**: Clear dependency relationships

## Common Issues

### Issue: Import errors during migration
**Solution**: Make sure to import the context system correctly:
```python
from openhands.server.context import get_server_context, ServerContext
```

### Issue: Context not available in non-route functions
**Solution**: Pass the context as a parameter:
```python
def helper_function(data: str, context: ServerContext):
    config = context.get_config()
    # ... use config
```

### Issue: Testing becomes more complex
**Solution**: Create reusable mock contexts:
```python
# test_utils.py
class TestServerContext(ServerContext):
    def __init__(self):
        self.mock_config = create_mock_config()
        self.mock_file_store = create_mock_file_store()

    def get_config(self):
        return self.mock_config

    def get_file_store(self):
        return self.mock_file_store
```

## Getting Help

If you encounter issues during migration:

1. Check the examples in `examples/saas_extension.py`
2. Look at the implementation in `openhands/server/context/`
3. Review existing route handlers that have been migrated
4. Create an issue if you find bugs or need clarification
