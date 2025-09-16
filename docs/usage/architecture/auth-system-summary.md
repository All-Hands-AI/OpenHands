# OpenHands AuthSystem Design - Executive Summary

## Goal
Design a flexible authentication system for OpenHands that supports three strategies:
- **None**: Current behavior (no auth, optional GitHub token)
- **SU (Single User)**: GitHub OAuth for personal use
- **MU (Multi User)**: Extension point for custom builds (not in base OH)

## Current Problems
- 339+ `user_id` occurrences scattered across 68 files
- No auth strategy abstraction
- `provider_tokens` dependency injection complexity
- No single-user GitHub OAuth support
- Mixed auth/business logic concerns

## Solution Architecture

### Core Components
1. **AuthStrategy Interface** - Pluggable auth strategies
2. **UserContext** - Immutable user data container
3. **TokenProvider** - Centralized token management
4. **StorageNamespace** - Clean storage path abstraction

### Auth Strategies
```python
# None Strategy (current behavior)
OH_AUTH_STRATEGY=none

# Single User - No Auth (virtual user)
OH_AUTH_STRATEGY=single_user
OH_ENABLE_SU_AUTH=false

# Single User - GitHub OAuth
OH_AUTH_STRATEGY=single_user
OH_ENABLE_SU_AUTH=true
OH_SU_GITHUB_USERNAME=your_username
OH_GITHUB_CLIENT_ID=your_client_id
OH_GITHUB_CLIENT_SECRET=your_client_secret
```

## 🔄 Key Changes

### Before (Current)
```python
# Route with complex dependencies
async def get_repositories(
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    user_id: str | None = Depends(get_user_id),
):
    client = ProviderHandler(
        provider_tokens=provider_tokens,
        external_auth_id=user_id,
    )

# Scattered path logic
def get_conversation_dir(sid: str, user_id: str | None = None) -> str:
    if user_id:
        return f'users/{user_id}/conversations/{sid}/'
    else:
        return f'sessions/{sid}/'
```

### After (Proposed)
```python
# Clean route signature
async def get_repositories(
    token_provider: TokenProvider = Depends(get_token_provider),
    user: Optional[UserContext] = Depends(get_current_user),
):
    client = ProviderHandler(token_provider=token_provider)

# Encapsulated storage logic
@dataclass(frozen=True)
class StorageNamespace:
    namespace: Optional[str]
    
    def get_conversation_dir(self, sid: str) -> str:
        if self.namespace:
            return f'users/{self.namespace}/conversations/{sid}/'
        return f'sessions/{sid}/'
```

## Architectural Benefits

### Codebase Cleanup
- Removes 7 redundant `if user_id` guards across the codebase
- Eliminates `provider_tokens` dependency injection complexity
- Reduces method signature complexity throughout the system
- Centralizes storage path logic in dedicated abstractions

### Extensibility
- Strategy pattern enables custom build extension points
- Token refresh/rotation patterns built-in
- Multi-tenancy ready without core changes
- Additional auth methods can be added without refactoring

### Code Organization
- Clear separation of auth and business logic
- Consistent patterns across all authentication modes
- Centralized token and credential management
- Immutable user context prevents state corruption

## Implementation Plan

### Phase 1: Foundation
- [ ] Auth strategy interfaces
- [ ] UserContext & StorageNamespace
- [ ] TokenProvider abstraction
- [ ] Core dependencies

### Phase 2: Strategies
- [ ] NoneStrategy (backward compatible)
- [ ] SingleUserStrategy
- [ ] Configuration support
- [ ] UserAuth integration

### Phase 3: Routes
- [ ] Update FastAPI dependencies
- [ ] Remove provider_tokens
- [ ] Update ProviderHandler
- [ ] Clean redundant guards

### Phase 4: Storage
- [ ] Replace path helpers
- [ ] Update conversation managers
- [ ] Migrate event stores
- [ ] Legacy cleanup

## Architecture Highlights

### Strategy Pattern
```python
class AuthStrategy(ABC):
    @abstractmethod
    async def authenticate(self, request: Request) -> Optional[UserContext]:
        pass
    
    @abstractmethod
    async def get_token_provider(self, request: Request) -> TokenProvider:
        pass
```

### Immutable User Context
```python
@dataclass(frozen=True)
class UserContext:
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_admin: bool = False
```

### Token Provider Interface
```python
class TokenProvider(ABC):
    @abstractmethod
    async def get_token(self, provider: ProviderType) -> Optional[ProviderToken]:
        pass
```

## 🔧 Configuration Examples

### Current Default (None)
```bash
# No configuration needed - maintains current behavior
```

### Personal Use (SU without auth)
```bash
OH_AUTH_STRATEGY=single_user
OH_ENABLE_SU_AUTH=false
# Creates virtual "local" user, uses secrets.json
```

### Personal Use (SU with GitHub)
```bash
OH_AUTH_STRATEGY=single_user
OH_ENABLE_SU_AUTH=true
OH_SU_GITHUB_USERNAME=myusername
OH_GITHUB_CLIENT_ID=abc123
OH_GITHUB_CLIENT_SECRET=secret456
# Requires GitHub OAuth, restricts to specific user
```

## Implementation Readiness

### Backward Compatibility
- None strategy maintains exact current behavior
- No breaking changes for existing users
- Gradual migration path available

### Code Quality Improvements
- Reduces complexity from 339 to ~50 user_id references
- Introduces clear abstractions and boundaries
- Enables better testing and maintainability

### Extensibility Foundation
- Custom builds can add authentication strategies
- Token refresh/rotation patterns built-in
- Multi-tenancy foundation without core changes

## Summary

This design provides a clean authentication architecture for OpenHands with three key outcomes:

1. **Maintains simplicity** - Current users see no changes
2. **Enables extension** - Custom builds can add authentication features
3. **Improves codebase** - Reduces scattered auth logic and complexity

The architecture is well-defined with a clear migration path.