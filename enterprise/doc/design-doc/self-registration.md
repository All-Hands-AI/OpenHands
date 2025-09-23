# Self Registration

## 1 Introduction

### 1.1 Problem Statement

Some enterprise customers experience friction when setting up OpenHands for
proof-of-concept (POC) evaluations due to the requirement for IT partner
engagement to configure corporate Single Sign-On (SSO) integration. This can
delay POC timelines and create unnecessary overhead for temporary evaluation
environments where full SSO integration may not be required.

### 1.2 Proposed Solution

Implement a self-registration feature that allows users to create accounts and
access OpenHands without requiring pre-configured SSO integration. This solution
will:

- **Enable immediate access**: Users can register and start using OpenHands
  without any additional administrative process
- **Maintain security**: Leverage Keycloak's built-in user management and email
  verification

The feature will be controlled by a Helm chart configuration flag
(`ENTERPRISE_SELF_REGISTRATION`), allowing organizations to enable
self-registration for POC environments while maintaining SSO-only access for
production deployments.

## 2. Additional Context

## 3. UX

### 3.1 Self Registration Flow

| Step | Description | Location |
|------|-------------|----------|
| 1 | User visits UI | OpenHands UI |
| 2 | Click self register button | OpenHands UI |
| 3 | Redirect to Keycloak self registration page | Keycloak UI |
| 4 | Complete registration and check email | Keycloak UI + Email |
| 5 | User verifies email and account is created | Email + Keycloak UI |
| 6 | Keycloak automatically redirects to OpenHands | OpenHands UI |

**Note**: Step 6 uses client configuration redirect. See section 4.3.2 for other
post-registration possibilities.

### 3.2 Authentication for Self Registered Users

After completing registration and email verification, self-registered users need
to authenticate to access OpenHands. This follows the standard OAuth/OIDC flow
used by other identity providers.

| Step | Description | Location |
|------|-------------|----------|
| 1 | User clicks login button | OpenHands UI |
| 2 | Redirect to Keycloak login page | Keycloak UI |
| 3 | User enters credentials and logs in | Keycloak UI |
| 4 | Keycloak redirects to OpenHands callback URL | OpenHands UI |
| 5 | OpenHands processes OAuth callback and logs user in | OpenHands UI |

**Key Points**:

- Uses the same authentication flow as other identity providers
- Leverages existing `generateAuthUrl` utility with `identityProvider:
  "self_registration"`
- No additional configuration needed beyond enabling self-registration
- Users authenticate with their registered email/password credentials

### 3.3 Enable via Helm Chart Flag

The Helm Chart has an environment variable `ENTERPRISE_SELF_REGISTRATION` that
when set to true enables the UI for self registration button and the required
Keycloak configuration.

SMTP configuration is also required for proper functioning.

## 4. Technical Design

### 4.1 Feature Flag in Helm Chart

The self-registration feature will be controlled by the
`ENTERPRISE_SELF_REGISTRATION` environment variable in the OpenHands-Cloud Helm
charts, following the same pattern as the existing `ENABLE_ENTERPRISE_SSO` flag.

#### 4.1.1 Helm Chart Configuration

**Location**: `OpenHands-Cloud/charts/openhands/values.yaml`

The feature flag will be added to the `env` section of the values.yaml file:

```yaml
env:
  DISABLE_WAITLIST: "true"
  SANDBOX_REMOTE_RUNTIME_API_TIMEOUT: "60"
  RUNTIME_URL_PATTERN: "https://{runtime_id}.runtime.chuck-test.aws.all-hands.dev"
  # Self-registration feature flag
  ENTERPRISE_SELF_REGISTRATION: "false"  # Set to "true" to enable
```

**Environment-specific overrides**: Individual environments can override this
setting in their respective values files:

- `deploy/openhands/envs/production/values.yaml`
- `deploy/openhands/envs/staging/values.yaml`
- `deploy/openhands/envs/feature/values.yaml`

#### 4.1.2 Environment Variable Processing

**Location**: `OpenHands-Cloud/charts/openhands/templates/_env.yaml`

The environment variable is processed in the Helm template at lines 289-294:

```yaml
{{- if .Values.env }}
{{- range $key, $value := .Values.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}
```

This ensures the `ENTERPRISE_SELF_REGISTRATION` environment variable is passed
to the OpenHands enterprise server container.

#### 4.1.3 Backend Configuration Detection

**Location**: `OpenHands/enterprise/server/config.py`

Following the pattern established by `ENABLE_ENTERPRISE_SSO` (lines 152-153),
the backend will detect the feature flag:

```python
if ENABLE_ENTERPRISE_SSO:
    providers_configured.append(ProviderType.ENTERPRISE_SSO)

# Add similar logic for self-registration
if ENTERPRISE_SELF_REGISTRATION:
    providers_configured.append(ProviderType.SELF_REGISTRATION)
```

The flag will be added to the `PROVIDERS_CONFIGURED` array in the config
response (lines 167-168), which is consumed by the frontend to conditionally
render UI elements.

#### 4.1.4 Frontend Conditional Rendering

**Location**:
`OpenHands/frontend/src/components/features/waitlist/auth-modal.tsx`

Following the pattern established for Enterprise SSO (lines 89-92), the frontend
will conditionally show the self-registration button:

```typescript
const showSelfRegistration =
  providersConfigured &&
  providersConfigured.length > 0 &&
  providersConfigured.includes("self_registration");
```

The button will only be rendered when `showSelfRegistration` is true, similar to
how the Enterprise SSO button is conditionally rendered based on the
`providersConfigured` array.

#### 4.1.5 Self-Registration URL Generation

**Location**: `OpenHands/frontend/src/utils/generate-auth-url.ts`

The self-registration feature will leverage the existing `generateAuthUrl`
utility function to create Keycloak self-registration URLs. This follows the
same pattern as other identity providers (GitHub, GitLab, Bitbucket, Enterprise
SSO).

**Implementation Pattern**:

```typescript
const selfRegistrationUrl = useAuthUrl({
  appMode: appMode || null,
  identityProvider: "self_registration",
  authUrl,
});
```

The `generateAuthUrl` function will need to be updated to handle the
`self_registration` identity provider by generating a URL that points to
Keycloak's self-registration endpoint:

```plaintext
https://{auth-host}/realms/allhands/login-actions/registration?client_id=allhands&kc_idp_hint=self_registration&response_type=code&redirect_uri={redirect-uri}&scope=openid%20email%20profile&state={state}
```

This approach maintains consistency with the existing authentication flow while
enabling users to access Keycloak's built-in self-registration functionality.

#### 4.1.6 SMTP Configuration Requirements

**Current State**: The OpenHands-Cloud charts have partial SMTP configuration
but require additional setup for self-registration to work.

**Environment Variable**: The `KEYCLOAK_SMTP_PASSWORD` is already configured in
the Helm chart environment variables (lines 122-126 in
`OpenHands-Cloud/charts/openhands/templates/_env.yaml`):

```yaml
- name: KEYCLOAK_SMTP_PASSWORD
  valueFrom:
    secretKeyRef:
      name: keycloak-realm
      key: smtp-password
```

**Required Setup**: Users must configure SMTP settings in two places:

1. **Kubernetes Secret**: Update the `keycloak-realm` secret with actual SMTP
   credentials:

   ```bash
   kubectl create secret generic keycloak-realm -n openhands \
     --from-literal=realm-name=allhands \
     --from-literal=provider-name=email \
     --from-literal=server-url=http://keycloak \
     --from-literal=client-id=allhands \
     --from-literal=client-secret=$GLOBAL_SECRET \
     --from-literal=smtp-password=<your-smtp-password>  # Set actual password
   ```

2. **Keycloak Realm Configuration**: The Keycloak realm must be configured with
   SMTP server settings. This can be done through:
   - Keycloak Admin Console UI
   - Keycloak Admin API
   - Custom initialization script

**Required SMTP Settings**:

```json
{
  "smtpServer": {
    "password": "<smtp-password>",
    "starttls": "true",
    "auth": "true", 
    "host": "<smtp-host>",
    "from": "<from-email>",
    "fromDisplayName": "<display-name>",
    "ssl": "true",
    "user": "<smtp-username>"
  }
}
```

**Validation Requirement**: When `ENTERPRISE_SELF_REGISTRATION` is enabled, the
system should validate that SMTP is properly configured:

1. **Backend Validation**: Check that `KEYCLOAK_SMTP_PASSWORD` is present and
   non-empty
2. **Keycloak Validation**: Verify that Keycloak realm has SMTP server
   configured
3. **Warning Logging**: Log warnings if self-registration is enabled but SMTP is
   not properly configured

**Implementation Example**:

```python
# In OpenHands/enterprise/server/config.py
if ENTERPRISE_SELF_REGISTRATION:
    if not KEYCLOAK_SMTP_PASSWORD:
        logger.warning("ENTERPRISE_SELF_REGISTRATION is enabled but KEYCLOAK_SMTP_PASSWORD is not configured.")
    # Additional validation could check Keycloak realm SMTP configuration
```

### 4.2 UI for Self Registration

**Keycloak-Provided UI**: The self-registration UI is provided by Keycloak's
built-in registration page. No custom UI development is required.

**Enabling the UI**: The self-registration UI is automatically enabled when the
realm configuration is updated (see section 4.3.1). The UI will be accessible
at:

```plaintext
https://{auth-host}/realms/allhands/protocol/openid-connect/registrations?client_id=allhands
```

**UI Features** (provided by Keycloak):

- User registration form with email/password fields
- Email verification workflow
- Password strength validation
- Terms of service acceptance (if configured)
- Captcha protection (if enabled)

**No Additional Configuration Required**: The Keycloak self-registration UI
works out-of-the-box once the realm settings are updated via the Helm chart.

### 4.3 Keycloak Configuration

#### 4.3.1 Self-Registration Settings

**Location**: `OpenHands/enterprise/allhands-realm-github-provider.json.tmpl`

The realm configuration is automatically applied via Helm chart using the
existing template system. The following settings need to be updated in the realm
template:

**Current Settings** (lines 32-36):

```json
"registrationAllowed": false,
"registrationEmailAsUsername": true,
"verifyEmail": false,
"loginWithEmailAllowed": false,
```

**Updated Settings for Self-Registration**:

```json
"registrationAllowed": true,
"registrationEmailAsUsername": true,
"verifyEmail": true,
"loginWithEmailAllowed": true,
```

**Implementation**: The Helm chart uses `envsubst` to substitute environment
variables in the template, then applies the configuration via the Keycloak Admin
API. No manual configuration needed.

**Required Changes**:

1. Update the realm template to enable self-registration settings
2. Ensure `AUTH_WEB_HOST` environment variable is set in Helm values
3. The existing Keycloak configuration job will automatically apply the changes

#### 4.3.2 Post-Registration User Experience

**Problem**: After completing registration and email verification, users are
left on Keycloak's default success page without clear guidance on how to
proceed.

**Chosen Solution - Client Configuration Redirect:**

The OpenHands client configuration is already automated in the Helm chart via
the realm template. The client's `baseUrl` and `rootUrl` are set using
environment variables:

**Location**: `OpenHands/enterprise/allhands-realm-github-provider.json.tmpl`
(lines 712-714)

```json
"rootUrl": "${authBaseUrl}",
"baseUrl": "",
```

**Environment Variable**: `AUTH_WEB_HOST` (set in Helm values)

This approach:

- Uses Keycloak's built-in redirect mechanisms after registration completion
- Requires no custom themes or code
- Provides seamless user experience with automatic redirection
- **Fully automated** via existing Helm chart configuration

**Other Possibilities (Not Planned):**

**Custom Theme via ConfigMap:**

- Would provide more control over the user experience
- Requires ConfigMap creation and Helm chart modifications
- Could display custom "Registration Successful" page with branded messaging

**Custom Required Action:**

- Most complex but provides full control
- Requires custom Java code and deployment
- Would allow completely custom post-registration flow

## 5. Implementation Checklist

### 5.1 Backend Feature Flag Implementation

**Goal**: Enable self-registration feature flag detection and configuration
response.

**Files to Modify**:

- `OpenHands/enterprise/server/config.py` - Add `ENTERPRISE_SELF_REGISTRATION`
  detection
- `OpenHands/enterprise/server/routes/auth.py` - Update config response to
  include self-registration provider

**Test Files to Create**:

- `OpenHands/enterprise/tests/unit/test_self_registration_config.py` - Test feature flag
  detection
- `OpenHands/enterprise/tests/unit/test_auth_config_response.py` - Test config API includes
  self-registration

**Established Test Pattern**: Follow the existing pattern in
`OpenHands/enterprise/tests/unit/test_auth_routes.py` which tests auth-related
functionality with mocked requests and responses. Use similar fixtures and
mocking patterns for testing config detection and API responses.

**Testing Strategy**:

- Unit tests with different environment variable values
- Integration tests for config API response
- Test that `providersConfigured` array includes `"self_registration"` when
  enabled

**Acceptance Criteria**:

- [ ] `ENTERPRISE_SELF_REGISTRATION` environment variable is detected
- [ ] Config API returns `"self_registration"` in `providersConfigured` when
  enabled
- [ ] Config API excludes `"self_registration"` when disabled
- [ ] All existing tests pass

### 5.2 Frontend Self-Registration Button

**Goal**: Add self-registration button to auth modal with conditional rendering.

**Files to Modify**:

- `OpenHands/frontend/src/components/features/waitlist/auth-modal.tsx` - Add
  self-registration button
- `OpenHands/frontend/src/utils/generate-auth-url.ts` - Add self-registration
  URL generation
- `OpenHands/frontend/src/hooks/use-auth-url.ts` - Add self-registration hook
  usage

**Test Files to Create**:

- `OpenHands/frontend/src/components/features/waitlist/__tests__/auth-modal-self-registration.test.tsx`
- `OpenHands/frontend/src/utils/__tests__/generate-auth-url-self-registration.test.ts`

**Established Test Pattern**: Follow the existing pattern in
`OpenHands/__tests__/components/` which uses React Testing Library and Jest.
Reference existing auth modal tests for mocking patterns and component testing
approaches.

**Testing Strategy**:

- Mock config API responses with/without self-registration enabled
- Test button visibility based on `providersConfigured` array
- Test URL generation for self-registration identity provider
- Visual regression tests for button appearance

**Acceptance Criteria**:

- [ ] Self-registration button appears when `providersConfigured` includes
  `"self_registration"`
- [ ] Button is hidden when self-registration is not configured
- [ ] Clicking button generates correct Keycloak registration URL
- [ ] Button styling matches existing auth buttons
- [ ] All existing tests pass

### 5.3 Keycloak Realm Configuration (Manual)

**Goal**: Enable self-registration in Keycloak with manual realm configuration
for testing.

**Files to Modify**:

- `OpenHands/enterprise/allhands-realm-github-provider.json.tmpl` - Update realm
  settings

**Configuration Changes**:

```json
"registrationAllowed": true,
"verifyEmail": true,
"loginWithEmailAllowed": true
```

**Test Configuration**:

- Set up local SMTP server (MailHog or similar)
- Configure Keycloak SMTP settings via Admin Console
- Test email verification flow

**Testing Strategy**:

- Manual testing of registration flow
- Email verification testing with local SMTP
- End-to-end flow testing (registration → email verification → authentication)

**Acceptance Criteria**:

- [ ] Self-registration page is accessible at Keycloak URL
- [ ] Users can register with email/password
- [ ] Email verification emails are sent and received
- [ ] Users can authenticate after email verification
- [ ] Post-registration redirect works (client configuration)

### 5.4 Helm Chart Environment Variable

**Goal**: Add `ENTERPRISE_SELF_REGISTRATION` environment variable to Helm chart.

**Files to Modify**:

- `OpenHands-Cloud/charts/openhands/values.yaml` - Add environment variable
- `OpenHands-Cloud/charts/openhands/templates/_env.yaml` - Ensure variable is
  passed to container

**Test Files to Create**:

- `OpenHands-Cloud/charts/openhands/tests/test-self-registration-env.yaml` -
  Helm test for env var

**Testing Strategy**:

- Helm chart rendering tests
- Deploy test environment with variable enabled
- Verify environment variable reaches OpenHands container

**Acceptance Criteria**:

- [ ] `ENTERPRISE_SELF_REGISTRATION` appears in Helm values
- [ ] Environment variable is passed to OpenHands container
- [ ] Backend detects environment variable correctly
- [ ] Feature can be enabled/disabled via Helm values

### 5.5 Automated Realm Configuration

**Goal**: Automate Keycloak realm configuration via Helm chart template updates.

**Files to Modify**:

- `OpenHands/enterprise/allhands-realm-github-provider.json.tmpl` - Update realm
  settings
- `OpenHands-Cloud/charts/openhands/templates/keycloak-config-script.yaml` -
  Ensure script applies changes

**Test Files to Create**:

- `OpenHands/tests/test-realm-template-self-registration.py` - Test template
  rendering
- `OpenHands-Cloud/charts/openhands/tests/test-keycloak-config-job.yaml` - Test
  config job

**Testing Strategy**:

- Template rendering tests with different environment variables
- Integration tests for Keycloak configuration job
- End-to-end deployment testing

**Acceptance Criteria**:

- [ ] Realm template includes self-registration settings
- [ ] Keycloak configuration job applies settings automatically
- [ ] Self-registration works without manual Keycloak configuration
- [ ] Settings persist across Keycloak restarts

### 5.6 SMTP Configuration and Testing

**Goal**: Configure and test SMTP for email verification in self-registration
flow.

**Files to Modify**:

- `OpenHands-Cloud/charts/openhands/values.yaml` - Add SMTP configuration
  options
- `OpenHands-Cloud/charts/openhands/templates/keycloak-config-script.yaml` - Add
  SMTP configuration

**Local Testing Setup**:

```yaml
# Local SMTP server for testing
smtp:
  enabled: true
  host: "mailhog"
  port: 1025
  from: "noreply@localhost"
  username: ""
  password: ""
```

**Test Files to Create**:

- `OpenHands/tests/test-smtp-configuration.py` - Test SMTP setup
- `OpenHands/tests/test-email-verification-flow.py` - Test email verification

**Testing Strategy**:

- Deploy MailHog for local email testing
- Test email sending and receiving
- Verify email verification links work
- Test with different SMTP providers

**Acceptance Criteria**:

- [ ] SMTP configuration is applied to Keycloak
- [ ] Registration emails are sent successfully
- [ ] Email verification links work correctly
- [ ] Users can complete registration after email verification

### 5.7 End-to-End Integration Testing

**Goal**: Complete end-to-end testing of self-registration flow.

**Test Files to Create**:

- `OpenHands/tests/integration/test-self-registration-e2e.py` - Full flow
  testing
- `OpenHands-Cloud/charts/openhands/tests/test-self-registration-deployment.yaml`
  - Deployment testing

**Testing Strategy**:

- Deploy complete environment with self-registration enabled
- Test full user journey: UI → Keycloak → Email → Authentication
- Test with different user scenarios (valid/invalid emails, password
  requirements)
- Performance testing with multiple concurrent registrations

**Acceptance Criteria**:

- [ ] Complete user flow works from start to finish
- [ ] All error scenarios are handled gracefully
- [ ] Performance meets requirements
- [ ] Security requirements are met (email verification, password strength)

### 5.8 Documentation and Deployment

**Goal**: Complete documentation and production deployment preparation.

**Files to Create/Modify**:

- `OpenHands-Cloud/charts/openhands/README.md` - Update with self-registration
  instructions
- `docs/enterprise/self-registration-setup.md` - User documentation
- `OpenHands/enterprise/doc/design-doc/self-registration.md` - This document

**Testing Strategy**:

- Documentation review and testing
- Production deployment dry-run
- User acceptance testing

**Acceptance Criteria**:

- [ ] Documentation is complete and accurate
- [ ] Production deployment process is documented
- [ ] Monitoring and alerting are configured
- [ ] Rollback procedures are documented
