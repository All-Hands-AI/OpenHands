# OpenHands Server Context Refactoring Plan

## Problem Statement

The current OpenHands architecture has globals in `server/shared.py` that are initialized at import time based on environment variables. This creates several issues for the SaaS version:

1. **Import-time dependencies**: All globals are created when modules are imported
2. **Hard to extend**: SaaS can't easily override or extend components
3. **CI/CD issues**: Everything depends on env vars being set correctly at import time
4. **Per-user behavior**: Difficult to implement per-user/per-request behavior
5. **Outside repo issues**: Hard to run SaaS from outside repo due to import dependencies

## Current Problematic Globals

From `openhands/server/shared.py`:
- `config: OpenHandsConfig` - Core app configuration
- `server_config: ServerConfig` - Server-specific configuration
- `file_store: FileStore` - File storage implementation
- `sio: socketio.AsyncServer` - Socket.IO server instance
- `conversation_manager` - Conversation management implementation
- `monitoring_listener` - Monitoring implementation
- `SettingsStoreImpl`, `SecretsStoreImpl`, `ConversationStoreImpl` - Storage implementations

## Solution: ServerContext Pattern

### 1. Create ServerContext Base Class

Create `openhands/server/context/server_context.py`:

```python
from abc import ABC, abstractmethod
from typing import Optional
import socketio
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.server.config.server_config import ServerConfig
from openhands.storage.files import FileStore
# ... other imports

class ServerContext(ABC):
    """Base class for server context that holds all server dependencies.

    This replaces the global variables in shared.py and allows for:
    - Dependency injection
    - Easy extensibility for SaaS
    - Per-request contexts
    - Testability
    """

    def __init__(self):
        self._config: Optional[OpenHandsConfig] = None
        self._server_config: Optional[ServerConfig] = None
        self._file_store: Optional[FileStore] = None
        # ... other cached instances

    @abstractmethod
    def get_config(self) -> OpenHandsConfig:
        """Get the OpenHands configuration"""

    @abstractmethod
    def get_server_config(self) -> ServerConfig:
        """Get the server configuration"""

    @abstractmethod
    def get_file_store(self) -> FileStore:
        """Get the file store implementation"""

    # ... other abstract methods for all current globals
```

### 2. Create Default Implementation

Create `openhands/server/context/default_server_context.py`:

```python
class DefaultServerContext(ServerContext):
    """Default implementation that maintains current behavior"""

    def get_config(self) -> OpenHandsConfig:
        if self._config is None:
            self._config = load_openhands_config()
        return self._config

    def get_server_config(self) -> ServerConfig:
        if self._server_config is None:
            self._server_config = load_server_config()
        return self._server_config

    # ... implement all methods with current logic
```

### 3. Context Provider System

Create `openhands/server/context/context_provider.py`:

```python
from fastapi import Request
from openhands.utils.import_utils import get_impl

_context_class: Optional[str] = None

def set_context_class(context_class: str):
    """Set the server context class to use"""
    global _context_class
    _context_class = context_class

async def get_server_context(request: Request) -> ServerContext:
    """Get server context from request, with caching"""
    context = getattr(request.state, 'server_context', None)
    if context:
        return context

    # Use configured context class or default
    context_cls_name = _context_class or 'openhands.server.context.default_server_context.DefaultServerContext'
    context_cls = get_impl(ServerContext, context_cls_name)
    context = context_cls()

    request.state.server_context = context
    return context
```

### 4. Update Shared.py (Backward Compatibility)

Keep `shared.py` for backward compatibility but make it use the context:

```python
# openhands/server/shared.py
from openhands.server.context.default_server_context import DefaultServerContext

# Create default context for backward compatibility
_default_context = DefaultServerContext()

# Expose globals for backward compatibility
config = _default_context.get_config()
server_config = _default_context.get_server_config()
file_store = _default_context.get_file_store()
# ... etc
```

### 5. Update Routes to Use Context

Update all route files to use dependency injection:

```python
# Example: openhands/server/routes/settings.py
from openhands.server.context import get_server_context

@app.get('/settings')
async def get_settings(
    request: Request,
    context: ServerContext = Depends(get_server_context)
):
    config = context.get_config()
    # ... use config instead of importing from shared
```

## Benefits for SaaS

### 1. Easy Extension

SaaS can create their own context:

```python
# In SaaS repo: saas/server_context.py
from openhands.server.context import ServerContext

class SaaSServerContext(ServerContext):
    def get_server_config(self) -> ServerConfig:
        # Return SaaS-specific config with enterprise features
        return SaaSServerConfig()

    def get_conversation_manager(self) -> ConversationManager:
        # Return multi-tenant conversation manager
        return MultiTenantConversationManager()
```

### 2. Per-Request Contexts

SaaS can implement per-user contexts:

```python
class PerUserServerContext(ServerContext):
    def __init__(self, user_id: str, org_id: str):
        super().__init__()
        self.user_id = user_id
        self.org_id = org_id

    def get_file_store(self) -> FileStore:
        # Return user-specific file store
        return UserFileStore(self.user_id, self.org_id)
```

### 3. No Import-Time Dependencies

SaaS can run without setting environment variables at import time:

```python
# In SaaS startup
from openhands.server.context import set_context_class
set_context_class('saas.server_context.SaaSServerContext')
```

## Migration Strategy

### Phase 1: Create Context System
1. Create ServerContext base class and default implementation
2. Create context provider system
3. Update shared.py for backward compatibility

### Phase 2: Update Routes Gradually
1. Update one route at a time to use context injection
2. Test each route to ensure no regressions
3. Keep backward compatibility during transition

### Phase 3: Clean Up
1. Remove globals from shared.py once all routes are updated
2. Update documentation
3. Create examples for SaaS extension

## Implementation Order

1. `openhands/server/context/server_context.py` - Base class
2. `openhands/server/context/default_server_context.py` - Default implementation
3. `openhands/server/context/context_provider.py` - Provider system
4. `openhands/server/context/__init__.py` - Public API
5. Update `openhands/server/shared.py` for backward compatibility
6. Update routes one by one to use context injection
7. Update tests to use context system
8. Documentation and examples

This approach provides a clean migration path while maintaining backward compatibility and enabling the SaaS extensibility requirements.
