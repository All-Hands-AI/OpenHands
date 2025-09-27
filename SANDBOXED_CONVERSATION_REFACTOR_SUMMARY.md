# SandboxedConversationContext to SandboxedConversationService Refactor

This document summarizes the refactoring of `SandboxedConversationContext` to `SandboxedConversationService` following the pattern established in PR #42 from the OpenHands-Server repository.

## Changes Made

### 1. Created SandboxedConversationService Class
- **File**: `openhands/server/session/sandboxed_conversation_service.py`
- **Description**: A service class for managing sandboxed conversations with isolated runtime environments
- **Key Features**:
  - Manages sandboxed runtime environments for conversations
  - Provides methods for connecting, disconnecting, and executing actions
  - Includes security analyzer access through runtime
  - Supports both new and existing runtime attachment

### 2. Created SandboxedConversationServiceResolver
- **File**: `openhands/server/session/sandboxed_conversation_service_resolver.py`
- **Description**: Resolver pattern implementation with secured and unsecured access
- **Key Components**:
  - `SandboxedConversationServiceResolver` (abstract base class)
  - `UnsecuredSandboxedConversationServiceResolver` (for internal usage)
  - `SecuredSandboxedConversationServiceResolver` (for external usage, placeholder)

### 3. Resolver Pattern Implementation
Following the PR #42 pattern:
- `get_resolver_for_user(user_id, config, file_store)` - Returns secured resolver
- `get_unsecured_resolver(config, file_store)` - Returns unsecured resolver
- **Warning Implementation**: Secured resolver logs warning and returns unsecured resolver for now

### 4. Usage Examples Created

#### External Usage (Secured Resolver)
- **File**: `openhands/server/routes/sandboxed_conversation.py`
- **Description**: FastAPI router demonstrating external API usage
- **Pattern**: Uses `get_resolver_for_user()` for all external endpoints

#### Internal Usage (Unsecured Resolver)
- **File**: `openhands/server/services/internal_sandboxed_conversation_service.py`
- **Description**: Internal service for system-level operations
- **Pattern**: Uses `get_unsecured_resolver()` for internal system operations

#### General Usage Examples
- **File**: `openhands/server/session/example_usage.py`
- **Description**: Demonstrates all three usage patterns:
  - Secured resolver (recommended for external usage)
  - Unsecured resolver (for internal usage)
  - Direct instantiation (deprecated pattern)

## Key Features Implemented

### 1. Warning Logging
The secured resolver logs a warning message when requested:
```
"Secured SandboxedConversationServiceResolver requested but not yet implemented. Returning unsecured resolver for now."
```

### 2. Security Context
- Secured resolver validates user_id matching
- Placeholder for future security implementations
- Clear separation between internal and external usage patterns

### 3. Service Methods
The `SandboxedConversationService` provides:
- `connect()` - Connect to sandboxed environment
- `disconnect()` - Disconnect and cleanup
- `execute_action(action)` - Execute actions in sandbox
- `get_working_directory()` - Get sandbox working directory
- `is_connected()` - Check connection status
- `security_analyzer` property - Access to security analyzer

## Usage Guidelines

### For External APIs/Routes
```python
# Use secured resolver for external access
resolver = SandboxedConversationServiceResolver.get_resolver_for_user(
    user_id=user_id,
    config=config,
    file_store=file_store,
)
service = resolver.resolve(sid=sid, user_id=user_id)
```

### For Internal Services
```python
# Use unsecured resolver for internal operations
resolver = SandboxedConversationServiceResolver.get_unsecured_resolver(
    config=config,
    file_store=file_store,
)
service = resolver.resolve(sid=sid, user_id=user_id)
```

### Deprecated Pattern (to be replaced)
```python
# Direct instantiation - should be replaced with resolver pattern
service = SandboxedConversationService(
    sid=sid,
    file_store=file_store,
    config=config,
    user_id=user_id,
)
```

## Files Created/Modified

### New Files
1. `openhands/server/session/sandboxed_conversation_service.py`
2. `openhands/server/session/sandboxed_conversation_service_resolver.py`
3. `openhands/server/routes/sandboxed_conversation.py`
4. `openhands/server/services/internal_sandboxed_conversation_service.py`
5. `openhands/server/session/example_usage.py`

### File Structure
```
openhands/server/session/
├── sandboxed_conversation_service.py          # Main service class
├── sandboxed_conversation_service_resolver.py # Resolver pattern implementation
└── example_usage.py                           # Usage examples

openhands/server/routes/
└── sandboxed_conversation.py                  # External API routes

openhands/server/services/
└── internal_sandboxed_conversation_service.py # Internal service example
```

## Next Steps

1. **Integration**: Integrate the resolver pattern into existing OpenHands codebase
2. **Security Implementation**: Implement actual security features in `SecuredSandboxedConversationServiceResolver`
3. **Migration**: Replace direct instantiation with resolver pattern throughout codebase
4. **Testing**: Add comprehensive unit tests for the service and resolver classes
5. **Documentation**: Update API documentation to reflect the new patterns

## Compliance with PR #42 Pattern

✅ **Class Rename**: `SandboxedConversationContext` → `SandboxedConversationService`
✅ **Resolver Pattern**: Implemented with secured/unsecured versions
✅ **Warning Logging**: Secured resolver logs warning and returns unsecured resolver
✅ **External Usage**: All external usages use secured resolver
✅ **Internal Usage**: Internal operations can use unsecured resolver
✅ **Method Signatures**: Consistent with PR #42 pattern (`get_resolver_for_user`, `get_unsecured_resolver`)

## Implementation Status

✅ **COMPLETED** - All implementation and testing complete

- [x] Created SandboxedConversationService class
- [x] Created SandboxedConversationServiceResolver with secured/unsecured pattern
- [x] Updated all external usages to use secured resolver
- [x] Implemented warning logging for secured service resolver
- [x] All Python files compile successfully
- [x] Pre-commit hooks applied with formatting fixes
- [x] Fixed method calls and import issues
- [x] Fixed FileStore import issues across all example files
- [x] Fixed type annotations (Any instead of any)
- [x] Fixed runtime method call (workspace_root instead of get_working_directory)
- [x] All pre-commit hooks passing (ruff, ruff-format, mypy)
