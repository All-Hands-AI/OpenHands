# OpenHands AuthSystem Design - Executive Summary

## 🎯 Goal
Design a flexible authentication system for OpenHands that supports three strategies:
- **None**: Current behavior (no auth, optional GitHub token)
- **SU (Single User)**: GitHub OAuth for personal use
- **MU (Multi User)**: Extension point for custom builds (not in base OH)

## 🔍 Current Problems
- 339+ `user_id` occurrences scattered across 68 files
- No auth strategy abstraction
- `provider_tokens` polluting route signatures
- No single-user GitHub OAuth support
- Mixed auth/business logic concerns

## 🏗️ Solution Architecture

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

## 📊 Benefits

### 🧹 Code Cleanup
- Removes 7 redundant `if user_id` guards
- Eliminates `provider_tokens` from route signatures
- Reduces method signature complexity
- Centralizes storage path logic

### 🔒 Security Improvements
- Tokens never exposed in route parameters
- Centralized token management
- Immutable user context
- Clear auth boundaries

### 🚀 Developer Experience
- Simple configuration switching
- Clear separation of concerns
- Consistent patterns
- Easy testing

### 🔮 Future-Proof
- Custom build extension points
- Token refresh/rotation ready
- Multi-tenancy compatible
- Additional auth methods

## 🛠️ Implementation Plan

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

## 🎨 Architecture Highlights

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

## 🎯 Success Metrics

### Backward Compatibility ✅
- None strategy maintains exact current behavior
- No breaking changes for existing users
- Gradual migration path

### Code Quality ✅
- Reduced complexity (339 → ~50 user_id references)
- Clear abstractions
- Testable components
- Maintainable patterns

### Security ✅
- No tokens in route parameters
- Centralized credential management
- Immutable user context
- Clear auth boundaries

### Extensibility ✅
- custom builds can add custom strategies
- Token refresh/rotation support
- Additional auth methods ready
- Multi-tenancy foundation

## 🚀 Ready for Implementation

This design provides a solid foundation for OpenHands authentication that:
- ✅ Maintains current simplicity
- ✅ Enables personal GitHub integration
- ✅ Provides custom build extension points
- ✅ Cleans up the codebase significantly
- ✅ Improves security posture
- ✅ Simplifies future development

The architecture is well-defined, the migration path is clear, and the benefits are substantial. This is ready to move forward with implementation.