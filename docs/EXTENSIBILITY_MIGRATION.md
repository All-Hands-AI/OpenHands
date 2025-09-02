# OpenHands Extensibility Migration Guide

This guide explains how to migrate from the old global variable approach to the new factory-based extensibility system.

## Overview

OpenHands has been refactored to eliminate import-time dependencies on environment variables and global state. This enables external repositories to cleanly extend OpenHands without configuration conflicts.

## The Problem We Solved

### Before (Problematic)
```python
# In OpenHands shared.py - loaded at import time
config = Config()  # Reads environment variables
server_config = ServerConfig()  # More environment variables

# External repos had to:
# 1. Set environment variables before importing OpenHands
# 2. Deal with global state conflicts
# 3. Couldn't easily override specific behaviors
```

### After (Clean)
```python
# External repos can now:
from openhands.server.factory import create_openhands_app

app = create_openhands_app(
    context_factory=lambda: MyCustomContext(),
    include_oss_routes=False
)
```

## Migration Paths

### 1. For External Repositories (Recommended)

**Old Way (Don't do this):**
```python
# external_repo/main.py
import os
os.environ['OPENHANDS_CONFIG_CLS'] = 'my_config.MyConfig'
os.environ['CONVERSATION_MANAGER_CLASS'] = 'my_manager.MyManager'

from openhands.server.app import app  # Imports with global state
```

**New Way (Recommended):**
```python
# external_repo/main.py
from openhands.server.factory import create_openhands_app
from external_repo.context import ExternalRepoContext

def create_app():
    return create_openhands_app(
        context_factory=lambda: ExternalRepoContext(),
        include_oss_routes=False,  # Skip OSS-specific routes
        title='My Enterprise Platform'
    )

app = create_app()

# Add your own routes
@app.get('/enterprise/dashboard')
async def dashboard():
    return {'status': 'enterprise'}
```

### 2. For OpenHands Core Development

**Old Way:**
```python
# In route handlers
from openhands.server.shared import config, server_config

@app.get('/example')
async def example_route():
    storage_path = config.workspace_base
    app_mode = server_config.app_mode
```

**New Way:**
```python
# In route handlers
from fastapi import Depends
from openhands.server.context import get_server_context, ServerContext

@app.get('/example')
async def example_route(
    context: ServerContext = Depends(get_server_context)
):
    config = context.get_config()
    server_config = context.get_server_config()
    storage_path = config.workspace_base
    app_mode = server_config.app_mode
```

## Custom Context Implementation

### Step 1: Create Your Context Class

```python
# my_extension/context.py
from openhands.server.context.server_context import ServerContext

class MyCustomContext(ServerContext):
    def __init__(self, tenant_id: str = 'default'):
        super().__init__()
        self.tenant_id = tenant_id
    
    def get_config(self):
        """Override with tenant-specific configuration."""
        config = super().get_config()
        config.workspace_base = f'/data/tenants/{self.tenant_id}/workspace'
        return config
    
    def get_server_config(self):
        """Override server configuration."""
        server_config = super().get_server_config()
        server_config.app_mode = 'ENTERPRISE'
        server_config.enable_billing = True
        return server_config
```

### Step 2: Create Your FastAPI App

```python
# my_extension/app.py
from openhands.server.factory import create_openhands_app
from my_extension.context import MyCustomContext

def create_my_app():
    # Option A: Extend OpenHands app directly
    app = create_openhands_app(
        context_factory=lambda: MyCustomContext(),
        title='My Enterprise Platform'
    )
    
    # Add your routes
    @app.get('/enterprise/status')
    async def enterprise_status():
        return {'mode': 'enterprise'}
    
    return app

# Option B: Create your own app and mount OpenHands
from fastapi import FastAPI

def create_my_app_with_mount():
    main_app = FastAPI(title='My Platform')
    
    openhands_app = create_openhands_app(
        context_factory=lambda: MyCustomContext()
    )
    
    main_app.mount('/openhands', openhands_app)
    
    @main_app.get('/my-dashboard')
    async def dashboard():
        return {'dashboard': 'data'}
    
    return main_app
```

### Step 3: Run Your Application

```python
# my_extension/main.py
import uvicorn
from my_extension.app import create_my_app

if __name__ == '__main__':
    app = create_my_app()
    uvicorn.run(app, host='0.0.0.0', port=8000)
```

## Advanced Patterns

### Multi-Tenant Context

```python
class MultiTenantContext(ServerContext):
    def __init__(self, request: Request):
        super().__init__()
        # Extract tenant from request
        self.tenant_id = request.headers.get('X-Tenant-ID', 'default')
    
    def get_file_store(self):
        # Return tenant-isolated file store
        return TenantFileStore(tenant_id=self.tenant_id)

# Use with factory
def create_tenant_context(request: Request):
    return MultiTenantContext(request)

app = create_openhands_app(
    context_factory=create_tenant_context
)
```

### Custom Lifespan Management

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def my_lifespan(app: FastAPI):
    # Startup
    print("Starting my custom services...")
    await initialize_my_database()
    
    yield
    
    # Shutdown
    print("Shutting down my custom services...")
    await cleanup_my_database()

app = create_openhands_app(
    context_factory=MyContext,
    custom_lifespan=my_lifespan
)
```

## Testing Your Extension

```python
# tests/test_my_extension.py
from fastapi.testclient import TestClient
from my_extension.app import create_my_app

def test_my_extension():
    app = create_my_app()
    client = TestClient(app)
    
    # Test your custom routes
    response = client.get('/enterprise/status')
    assert response.status_code == 200
    assert response.json()['mode'] == 'enterprise'
    
    # Test OpenHands routes still work
    response = client.get('/api/health')
    assert response.status_code == 200
```

## Benefits of the New Approach

1. **No Environment Variables**: Configuration is done through code, not environment variables
2. **Clean Separation**: External repos don't modify OpenHands globals
3. **Dependency Injection**: Proper FastAPI dependency injection patterns
4. **Testability**: Easy to mock contexts for testing
5. **Flexibility**: Can create multiple apps with different configurations
6. **No Import-Time Side Effects**: Safe to import OpenHands modules

## Backward Compatibility

The old `openhands.server.shared` module still works but is deprecated. It will show deprecation warnings and should be migrated to the new context system.

## Common Pitfalls

1. **Don't set environment variables**: Use the factory pattern instead
2. **Don't import `openhands.server.app` directly**: Use the factory to create your own app
3. **Don't modify global state**: Use dependency injection through contexts
4. **Don't forget to override dependencies**: Use `app.dependency_overrides` if needed

## Getting Help

If you need help migrating your extension, please:
1. Check the examples in `examples/external_repo_extension.py`
2. Look at the test cases for patterns
3. Open an issue with your specific use case

The new system is designed to be more flexible and maintainable while enabling clean extensibility for all types of OpenHands deployments.