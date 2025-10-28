# V1 API Redesign – Working Notes (tracking)

Purpose: Track current V1 implementation status for the three proposal aspects and enumerate V1 REST routes. Focus on app-server (V1) that orchestrates remote agent-server from agent-sdk. Ignore V0 legacy where not on the V1 execution path.

Sources read in repo:
- openhands/server/app.py (router mounting)
- openhands/app_server/v1_router.py (V1 API surface)
- app-server packages: app_conversation, event, event_callback, sandbox, user, services, config
- Frontend calls under frontend/src/api to validate route usage

External: agent-sdk (agent-server + sdk) is the V1 core. In this tree we import:
- openhands.agent_server.* (models, utils)
- openhands.sdk.* (LLM, workspace, secrets)

---

## 1) UserContext

Status
- UserContext abstraction exists and is used via FastAPI DI.
  - Interface: openhands/app_server/user/user_context.py
    - get_user_id(), get_user_info(), get_authenticated_git_url(), get_latest_token(provider_type), get_secrets()
  - Implementations:
    - AuthUserContext (user-auth backed): openhands/app_server/user/auth_user_context.py
      - Bridges to legacy user auth storage to obtain settings and provider tokens as needed, but keeps tokens out of route signatures
      - Internally uses ProviderHandler to derive provider services and latest tokens
    - SpecifyUserContext (admin/sandbox/internal flows): openhands/app_server/user/specifiy_user_context.py
      - Request-scoped override carrying a specific user_id (or None for admin)
  - Injectors:
    - AuthUserContextInjector provides request-scoped UserContext from request-auth.

Observations
- agent-sdk/agent-server have no concept of user_id; user is an app concern.
- app-server introduces persistence for conversation metadata in DB (SQLAlchemy models) with user_id columns, but these are used via services that consume UserContext.
- New V1 routes do not carry user_id in path or query; scoping is enforced inside services via UserContext (see SQLAppConversationInfoService._secure_select()).

Auth/token threading in V1 app-server
- Tokens are not threaded through route signatures.
- Provider tokens are accessed via UserContext methods, often converted to SecretSource for the agent runtime.
- For agent-server communication, a short-lived session API key is used via header X-Session-API-Key.

Org risk and recommendation
- Enterprise is adding organizations (org_id) linking users to orgs. Do NOT introduce org_id into routes.
- Extend context instead of paths/signatures:
  - Option A: add optional org_id to UserContext.get_user_info() result and to SQL filter logic; record created_by_org_id in metadata.
  - Option B: introduce a separate OrganizationContext resolved by DI and consumed by services alongside UserContext.
- Ensure all service-layer DB queries filter by (user_id OR memberships via org_id) based on policy. Keep route signatures unchanged.

Actionable follow-ups
- Add org-aware filtering in SQL services without affecting routes.
- Keep provider tokens and org scoping behind UserContext/OrganizationContext.

Key references
- user_context.py, auth_user_context.py, specifiy_user_context.py
- app_conversation/sql_app_conversation_info_service.py (uses get_user_id() for row-level filtering)
- event/filesystem_event_service.py (permissioning via app_conversation_info_service)

---

## 2) ConversationPaths

Status
- agent-sdk and agent-server store conversation data; app-server keeps metadata in DB and events in filesystem.
- No user_id is embedded in filesystem paths in V1 app-server.
  - FilesystemEventService stores events under: {persistence_dir}/v1/events/{conversation_id}/timestamp_kind_eventId
- Therefore, V0 concern about user_id in conversation paths is not present in V1 app-server.

Validation
- FilesystemEventService._ensure_events_dir(), _get_event_files_by_pattern() demonstrate directory layout without user_id.
- All user scoping happens at service layer by checking conversation ownership via DB service (batch_get_app_conversation_info) before returning file-based events.

Recommendation
- Keep user/org scoping out of paths. If orgs are added, continue enforcing access via DB/service checks, not via path namespacing.

Key references
- app_server/event/filesystem_event_service.py
- app_server/app_conversation/sql_app_conversation_info_service.py

---

## 3) TokenSource → LookupSecret(SecretSource)

Status
- agent-sdk’s equivalent boundary is SecretSource with implementations:
  - StaticSecret for literal values
  - LookupSecret for remote fetch
- app-server V1 maps provider tokens into SecretSource:
  - In LiveStatusAppConversationService._build_start_conversation_request_for_user():
    - If web_url is configured, constructs a LookupSecret to GET /api/v1/webhooks/secrets with X-Access-Token (JWS) that includes user_id and provider_type (scoped and expirable)
    - Else falls back to StaticSecret with latest provider token from UserContext
- Therefore, token refresh/leakage is solved at the boundary: agent runtime calls back via LookupSecret; route signatures remain free of tokens.

Other tokens/headers in signatures
- X-Session-API-Key: agent-server session API key for starting conversations via app-server → agent-server POSTs.
- X-Access-Token: app-server-issued JWS for sandbox to retrieve secrets via /api/v1/webhooks/secrets.
- No provider_tokens or user_id appear in public REST route signatures.

Recommendation
- Keep all external-provider token logic behind SecretSource and JWT/JWS.
- With orgs, add org_id into the JWS claims when appropriate, and enforce in webhook secret retrieval by validating both user and org scopes.

Key references
- app_conversation/live_status_app_conversation_service.py (GIT_TOKEN secret construction)
- event_callback/webhook_router.py (GET /secrets; validates JWS and fetches provider tokens via per-user DI)
- user/auth_user_context.py (ProviderHandler usage is internal)

---

## V1 REST Routes (current)

Mounted under /api/v1 via openhands/app_server/v1_router.py

- /api/v1/app-conversations (app_conversation_router)
  - GET /search: filter by title/created_at/updated_at; pagination via page_id, limit
  - GET /count: same filters, returns count
  - GET /: batch get by ids[]=UUID
  - POST /: start task (returns AppConversationStartTask); uses background processing and X-Session-API-Key to talk to agent-server
  - POST /stream-start: streams AppConversationStartTask updates until READY/ERROR
  - GET /start-tasks/search: filter by conversation_id; sort order; pagination
  - GET /start-tasks/count
  - GET /start-tasks: batch get by ids[]=UUID

- /api/v1/events (event_router)
  - GET /search: filters (conversation_id, kind, timestamp ranges), sort, pagination
  - GET /count: same filters, count
  - GET /: batch get by id[]=str (UUIDs)

- /api/v1/sandboxes (sandbox_router)
  - GET /search: pagination
  - GET /: batch get by id[]=str
  - POST /: start sandbox (optional sandbox_spec_id)
  - POST /{sandbox_id}/pause
  - POST /{sandbox_id}/resume
  - DELETE /{id}: delete sandbox (NB: path parameter name differs from function param; consider standardizing to {sandbox_id})

- /api/v1/webhooks (webhook_router)
  - POST /{sandbox_id}/conversations: upsert conversation info from agent-server callback
  - POST /{sandbox_id}/events/{conversation_id}: append events from agent-server callback
  - GET /secrets: return provider secret value for scoped JWS (X-Access-Token)

- /api/v1/users (user_router)
  - GET /me: returns current authenticated user info

Auth primitives in routes
- No user_id in REST paths.
- No provider_tokens in route signatures.
- Authentication/authorization via DI-provided contexts and header tokens (session or access) where necessary.

---

## Legacy/V0 surface still present (for UI compatibility)

- openhands/server/app.py mounts both legacy routers and V1 when server_config.enable_v1 is true. The UI still calls many /api/user/* endpoints (see frontend src), hence legacy routes remain. V1-specific UI calls use /api/v1/* for conversations/sandboxes/events.
- Risk: Introducing orgs must not add org_id to these routes. Keep org scoping in DI and services only.

---

## Open risks and proposed refactor plan (orgs)

1) Data model
- Add org_id (nullable) columns to conversation metadata and related tables; maintain created_by_user_id and created_by_org_id.
- Backfill/nullable default for OSS.

2) Context and DI
- Option A: Extend UserContext.get_user_info() to include org memberships and an active org_id (if selected).
- Option B: Add OrganizationContext via DI and inject alongside UserContext. Services consult both for scoping.

3) Service filters
- Update SQLAppConversationInfoService._secure_select() to filter by either user_id or org memberships as policy dictates. Avoid touching route signatures.

4) Secret scoping
- When issuing JWS for /webhooks/secrets, include org_id claim and verify it on fetch. Ensure provider token resolution respects org policies.

5) Endpoint contracts
- Keep V1 routes as-is (no org_id in path). Avoid proliferating new route variants.

6) Cleanup
- Gradually remove V0 routes once frontend migrates fully to V1 equivalents.

---

## Quick pointers (file paths)
- V1 router aggregator: openhands/app_server/v1_router.py
- UserContext: openhands/app_server/user/user_context.py
- AuthUserContext: openhands/app_server/user/auth_user_context.py
- Admin override: openhands/app_server/user/specifiy_user_context.py
- V1 DB services: app_conversation/sql_app_conversation_info_service.py, sql_app_conversation_start_task_service.py
- Events: app_server/event/filesystem_event_service.py
- Secrets/lookup: app_server/event_callback/webhook_router.py, app_conversation/live_status_app_conversation_service.py

This file is a living document – update as implementations evolve.
