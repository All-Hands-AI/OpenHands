# Enterprise Auth System Analysis

## Executive Summary

The OpenHands Enterprise authentication system is built around **Keycloak** as the primary identity provider, with a sophisticated multi-provider token management system. The system handles **1,022 occurrences** of various user_id forms across the enterprise codebase, serving multiple purposes from authentication to resource scoping and cross-platform user linking.

## Core Authentication System

### Primary Components

1. **SaasUserAuth** ([`/enterprise/server/auth/saas_user_auth.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/auth/saas_user_auth.py))
   - Main authentication class extending base UserAuth
   - Handles both cookie-based and API key authentication
   - Manages token refresh and provider token retrieval

2. **TokenManager** ([`/enterprise/server/auth/token_manager.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/auth/token_manager.py))
   - Manages Keycloak tokens and provider-specific tokens
   - Handles token encryption/decryption
   - Orchestrates OAuth flows for GitHub, GitLab, Bitbucket

3. **Auth Routes** ([`/enterprise/server/routes/auth.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/routes/auth.py))
   - OAuth callback handlers
   - Authentication endpoints
   - Token refresh endpoints

### Authentication Flow

```
1. User initiates OAuth → Keycloak
2. Keycloak callback → TokenManager.get_keycloak_tokens()
3. Store provider tokens → TokenManager.store_idp_tokens()
4. Create signed JWT cookie → set_response_cookie()
5. Subsequent requests → SaasUserAuth.get_instance()
```

## User Registration and Login Flow

### New User Journey

**There is no traditional "registration" system** - OpenHands Enterprise uses **OAuth-based authentication** with automatic user provisioning:

#### 1. **Initial Access**
- New users visit the OpenHands application
- System displays [`AuthModal`](https://github.com/All-Hands-AI/OpenHands/blob/main/frontend/src/components/features/waitlist/auth-modal.tsx) with provider options:
  - **GitHub** (most common)
  - **GitLab**
  - **Bitbucket**
  - **Enterprise SSO** (SAML/OIDC)

#### 2. **OAuth Authentication Flow**
- User clicks provider button → redirects to Keycloak OAuth URL
- OAuth URL format: `https://auth.{domain}/realms/allhands/protocol/openid-connect/auth`
- Parameters include: `client_id=allhands`, `kc_idp_hint={provider}`, `response_type=code`
- User authenticates with chosen provider (GitHub, GitLab, etc.)
- Provider redirects back to [`/oauth/keycloak/callback`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/routes/auth.py#L98)

#### 3. **User Provisioning** (Automatic)
- [`keycloak_callback()`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/routes/auth.py#L98) processes OAuth response
- Extracts user info: `user_id` (Keycloak sub), `preferred_username`, `identity_provider`
- **No explicit registration** - user record created automatically on first login
- Stores provider tokens via [`TokenManager.store_idp_tokens()`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/auth/token_manager.py)

#### 4. **Waitlist Verification** (Optional)
- [`UserVerifier`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/auth/auth_utils.py#L8) checks if user is allowed
- Configured via `GITHUB_USER_LIST_FILE` or `GITHUB_USERS_SHEET_ID`
- Can be disabled with `DISABLE_WAITLIST=true`
- If not on waitlist: returns `401 Unauthorized`

#### 5. **Terms of Service Acceptance**
- System checks if user has accepted TOS in [`UserSettings`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/user_settings.py)
- If not accepted: redirects to [`/accept-tos`](https://github.com/All-Hands-AI/OpenHands/blob/main/frontend/src/routes/accept-tos.tsx) page
- User must check TOS checkbox and click "Continue"
- [`/api/accept_tos`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/routes/auth.py#L324) endpoint records acceptance

#### 6. **Session Establishment**
- Creates signed JWT cookie with Keycloak tokens
- Cookie name: `keycloak_auth`
- Contains: `access_token`, `refresh_token`, `accepted_tos` flag
- Sets up PostHog analytics tracking
- Redirects user to application

### Key Characteristics

- **No Username/Password**: Pure OAuth-based authentication
- **No Email Verification**: Relies on provider's email verification
- **Automatic Provisioning**: Users created on first successful OAuth login
- **Provider Flexibility**: Supports multiple OAuth providers simultaneously
- **Waitlist Control**: Optional user access control via external lists
- **TOS Enforcement**: Mandatory terms acceptance before app access

### Authentication States

1. **Unauthenticated**: Shows AuthModal with provider options
2. **Authenticated but No TOS**: Redirects to TOS acceptance page
3. **Fully Authenticated**: Access to full application functionality
4. **Waitlisted**: Shows "Not authorized via waitlist" error

### Session Management

- **Access Tokens**: Short-lived (minutes), used for API calls
- **Refresh Tokens**: Long-lived (hours/days), used to refresh access tokens
- **Offline Tokens**: Stored for provider API access (GitHub, GitLab, etc.)
- **Cookie Security**: HttpOnly, Secure, SameSite protection
- **Logout**: [`/api/logout`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/routes/auth.py#L383) clears cookies and revokes tokens

## User ID Forms and Occurrences

### Total Count: 1,022 occurrences across enterprise codebase

### User ID Types and Purposes

#### 1. **keycloak_user_id** (Primary Identity)
- **Purpose**: Primary user identifier from Keycloak SSO
- **Usage**: Authentication, resource scoping, primary key for user data
- **Key Files**:
  - [`storage/auth_tokens.py:8`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/auth_tokens.py#L8) - Links auth tokens to users
  - [`storage/user_settings.py:9`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/user_settings.py#L9) - User preferences and settings
  - [`storage/slack_user.py:8`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/slack_user.py#L8) - Links Slack users to Keycloak users
  - [`storage/jira_user.py:8`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/jira_user.py#L8) - Links Jira users to Keycloak users
  - [`storage/linear_user.py:8`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/linear_user.py#L8) - Links Linear users to Keycloak users

#### 2. **user_id** (Generic/Context-dependent)
- **Purpose**: Often aliases keycloak_user_id, sometimes refers to provider-specific IDs
- **Usage**: API parameters, function arguments, database queries
- **Key Files**:
  - [`storage/api_key.py:13`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/api_key.py#L13) - Links API keys to users
  - [`storage/stored_conversation_metadata.py:14`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/stored_conversation_metadata.py#L14) - Conversation ownership
  - [`server/auth/saas_user_auth.py:45`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/auth/saas_user_auth.py#L45) - Auth class user identifier

#### 3. **github_user_id** (GitHub Integration)
- **Purpose**: GitHub-specific user identifier for repository access
- **Usage**: Repository permissions, GitHub API calls, PR management
- **Key Files**:
  - [`storage/stored_conversation_metadata.py:13`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/stored_conversation_metadata.py#L13) - GitHub user for conversations
  - [`integrations/github/`](https://github.com/All-Hands-AI/OpenHands/tree/main/enterprise/integrations/github) - GitHub service integration

#### 4. **slack_user_id** (Slack Integration)
- **Purpose**: Slack-specific user identifier for workspace integration
- **Usage**: Slack bot interactions, message routing, user mapping
- **Key Files**:
  - [`storage/slack_user.py:9`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/slack_user.py#L9) - Slack user mapping
  - [`storage/slack_conversation.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/slack_conversation.py) - Slack conversation management

#### 5. **jira_user_id** (Jira Integration)
- **Purpose**: Jira-specific user identifier for issue management
- **Usage**: Issue assignment, Jira API calls, workspace permissions
- **Key Files**:
  - [`storage/jira_user.py:9`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/jira_user.py#L9) - Jira user mapping
  - [`storage/jira_conversation.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/jira_conversation.py) - Jira conversation management

#### 6. **linear_user_id** (Linear Integration)
- **Purpose**: Linear-specific user identifier for issue tracking
- **Usage**: Issue management, Linear API calls, workspace access
- **Key Files**:
  - [`storage/linear_user.py:9`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/linear_user.py#L9) - Linear user mapping
  - [`storage/linear_conversation.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/linear_conversation.py) - Linear conversation management

#### 7. **gitlab_user_id** (GitLab Integration)
- **Purpose**: GitLab-specific user identifier for repository access
- **Usage**: GitLab API calls, repository permissions, MR management

#### 8. **bitbucket_user_id** (Bitbucket Integration)
- **Purpose**: Bitbucket-specific user identifier for repository access
- **Usage**: Bitbucket API calls, repository permissions

## API Route Dependencies

### Primary Dependency Functions ([`/openhands/server/user_auth/__init__.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/server/user_auth/__init__.py))

```python
async def get_user_id(request: Request) -> str | None
async def get_access_token(request: Request) -> SecretStr | None
async def get_provider_tokens(request: Request) -> PROVIDER_TOKEN_TYPE | None
async def get_user_settings(request: Request) -> Settings | None
async def get_user_secrets(request: Request) -> UserSecrets | None
async def get_secrets_store(request: Request) -> SecretsStore
async def get_user_settings_store(request: Request) -> SettingsStore | None
async def get_auth_type(request: Request) -> AuthType | None
```

### Usage in API Routes

All enterprise API routes use `Depends(get_user_id)` for user identification:

- **Billing Routes** ([`server/routes/billing.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/routes/billing.py)): Credit management, payment processing
- **API Key Routes** ([`server/routes/api_keys.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/routes/api_keys.py)): API key CRUD operations
- **User Routes** ([`server/routes/user.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/routes/user.py)): User profile and settings
- **Integration Routes** ([`server/routes/integration/`](https://github.com/All-Hands-AI/OpenHands/tree/main/enterprise/server/routes/integration)): Provider-specific operations

## Data Structures and Storage Models

### Core Auth Models

#### AuthTokens ([`storage/auth_tokens.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/auth_tokens.py))
```python
class AuthTokens(Base):
    keycloak_user_id = Column(String, nullable=False, index=True)
    identity_provider = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
```

#### ApiKey ([`storage/api_key.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/api_key.py))
```python
class ApiKey(Base):
    user_id = Column(String(255), nullable=False, index=True)
    key = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=True)
```

#### UserSettings ([`storage/user_settings.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/user_settings.py))
```python
class UserSettings(Base):
    keycloak_user_id = Column(String, nullable=True, index=True)
    # 30+ user preference columns
```

### Integration Mapping Models

#### SlackUser ([`storage/slack_user.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/slack_user.py))
```python
class SlackUser(Base):
    keycloak_user_id = Column(String, nullable=False, index=True)
    slack_user_id = Column(String, nullable=False, index=True)
```

#### JiraUser ([`storage/jira_user.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/jira_user.py))
```python
class JiraUser(Base):
    keycloak_user_id = Column(String, nullable=False, index=True)
    jira_user_id = Column(String, nullable=False, index=True)
    jira_workspace_id = Column(Integer, nullable=False, index=True)
```

#### LinearUser ([`storage/linear_user.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/linear_user.py))
```python
class LinearUser(Base):
    keycloak_user_id = Column(String, nullable=False, index=True)
    linear_user_id = Column(String, nullable=False, index=True)
    linear_workspace_id = Column(Integer, nullable=False, index=True)
```

### Conversation and Resource Models

#### StoredConversationMetadata ([`storage/stored_conversation_metadata.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/stored_conversation_metadata.py))
```python
class StoredConversationMetadata(Base):
    user_id = Column(String, nullable=False)  # Keycloak User ID
    github_user_id = Column(String, nullable=True)  # GitHub user ID
    selected_repository = Column(String, nullable=True)
    git_provider = Column(String, nullable=True)
```

## Authentication Boundaries and System Integration

### 1. **API Gateway Boundary**
- **Entry Point**: FastAPI middleware and route dependencies
- **Validation**: `SaasUserAuth.get_instance()` validates cookies/API keys
- **Output**: Authenticated user context for downstream services

### 2. **Provider Integration Boundary**
- **Entry Point**: Provider-specific tokens from TokenManager
- **Validation**: Provider token refresh and validation
- **Output**: Valid provider tokens for external API calls

### 3. **Database Boundary**
- **Entry Point**: User-scoped database queries
- **Validation**: keycloak_user_id used as primary scoping mechanism
- **Output**: User-specific data retrieval and storage

### 4. **Conversation Boundary**
- **Entry Point**: Conversation creation and management
- **Validation**: User ownership validation via user_id
- **Output**: User-scoped conversation access

## Token Types and Management

### 1. **Keycloak Tokens**
- **Access Token**: Short-lived (minutes), used for API authentication
- **Refresh Token**: Long-lived (hours/days), used to refresh access tokens
- **Storage**: Encrypted in database, signed JWT in cookies

### 2. **Provider Tokens**
- **GitHub Token**: OAuth token for GitHub API access
- **GitLab Token**: OAuth token for GitLab API access
- **Slack Token**: Bot token for Slack workspace access
- **Jira Token**: OAuth token for Jira API access
- **Linear Token**: OAuth token for Linear API access
- **Bitbucket Token**: OAuth token for Bitbucket API access

### 3. **API Keys**
- **User API Keys**: Long-lived tokens for programmatic access
- **Session API Keys**: Temporary keys for specific conversation sessions
- **Storage**: Hashed in database, validated on each request

## Security and Access Control

### Rate Limiting
- **Implementation**: Redis-based rate limiter
- **Scope**: Per-user rate limiting using keycloak_user_id
- **Limits**: 10/second, 100/minute per user

### Token Security
- **Encryption**: All stored tokens encrypted using Fernet
- **Signing**: JWT cookies signed with server secret
- **Rotation**: Automatic token refresh before expiration

### User Verification
- **Waitlist**: Optional user verification via `user_verifier`
- **TOS Acceptance**: Required terms of service acceptance
- **Email Verification**: Email verification status tracking

## Key Integration Points

### 1. **Experiment System**
- **Purpose**: A/B testing and feature flags
- **User Scoping**: Uses user_id for consistent experiment assignment
- **Files**: [`experiments/experiment_manager.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/experiments/experiment_manager.py), [`experiments/experiment_versions/`](https://github.com/All-Hands-AI/OpenHands/tree/main/enterprise/experiments/experiment_versions)

### 2. **Billing System**
- **Purpose**: Usage tracking and payment processing
- **User Scoping**: Credits and billing tied to keycloak_user_id
- **Files**: [`server/routes/billing.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/server/routes/billing.py), [`storage/billing_session.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/enterprise/storage/billing_session.py)

### 3. **Integration Managers**
- **Purpose**: Provider-specific business logic
- **User Mapping**: Maps keycloak_user_id to provider-specific user IDs
- **Files**: [`integrations/*/manager.py`](https://github.com/All-Hands-AI/OpenHands/tree/main/enterprise/integrations) files

### 4. **Conversation Management**
- **Purpose**: Multi-user conversation handling
- **User Scoping**: Conversations owned by specific users
- **Files**: [`server/*conversation_manager.py`](https://github.com/All-Hands-AI/OpenHands/tree/main/enterprise/server)

## Summary of User ID Purposes

### Authentication (Primary)
- `keycloak_user_id`: Primary authentication identifier
- `user_id`: Generic authentication context
- API key validation and session management

### Resource Scoping (Secondary)
- Database query scoping by user
- Conversation ownership and access control
- Settings and preferences management
- Billing and usage tracking

### Cross-Platform Linking (Tertiary)
- `github_user_id`, `gitlab_user_id`: Repository access
- `slack_user_id`: Workspace integration
- `jira_user_id`, `linear_user_id`: Issue tracking integration
- Provider token management and refresh

### Analytics and Experimentation (Quaternary)
- PostHog user identification
- A/B test assignment consistency
- Feature flag evaluation
- Usage analytics and tracking

## Recommendations

1. **Consolidation**: Consider standardizing on `keycloak_user_id` as the primary identifier across all contexts
2. **Documentation**: Add inline documentation for user_id context in ambiguous cases
3. **Type Safety**: Consider using typed user ID classes to prevent confusion between different ID types
4. **Audit Trail**: Implement comprehensive logging for user ID usage in security-sensitive operations
