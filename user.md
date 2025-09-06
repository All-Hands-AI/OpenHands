# OpenHands user_id audit

I am OpenHands-GPT-5, an AI agent. This document collects findings about `user_id` usage in the OpenHands codebase to inform the refactor toward Single-User (SU), Multi-User (MU), or None options. It excludes test files.

## Summary
- Total occurrences (excluding tests): 339 lines across 68 files.
- Non-sandbox identity-related occurrences (excluding tests and sandbox/UID code paths): 290 lines across 53 files (see analysis/user_id_identity_hits.txt).
- Concentration by area (top files):
  - server/conversation_manager/standalone_conversation_manager.py (33)
  - server/conversation_manager/docker_nested_conversation_manager.py (28)
  - server/routes/git.py (23)
  - storage/locations.py (19)
  - server/services/conversation_service.py (19)
  - server/routes/manage_conversations.py (19)
  - server/routes/mcp.py (14)
  - controller/state/state.py (9)
  - server/session/agent_session.py (8)
  - see analysis/user_id_hits_no_tests.txt for full list

## If-guards that don’t use user_id in body
Automated AST scan of Python detected:
- if blocks whose condition references user_id: 12
- blocks where the body does not reference user_id: 7

Examples (see analysis/if_user_id_blocks.json for snippets):
- openhands/controller/state/state.py: two blocks guarding legacy cleanup/restore paths; body ignores user_id (file path variants)
- openhands/server/conversation_manager/standalone_conversation_manager.py: guards for session/connection filtering; body paths operate on maps without using user_id directly
- openhands/storage/conversation/conversation_store.py: guard checks metadata.user_id vs param, body returns booleans only
- openhands/resolver/issue_resolver.py: checks sandbox user_id == 0 to remap to unique uid; body does not use user_id afterward

These are candidates for boundary-level policy enforcement or function extraction so that core logic doesn’t need to “know” about user_id.

## Categories of user_id usage
1) Storage partitioning and paths
- storage/locations.py defines get_conversation_dir and related helpers, adding `users/{user_id}/` prefix when user_id is present.
- Event store, state save/restore, metadata paths thread user_id through to choose per-user directories.
- Impact: For SU, user_id could be a single stable identifier (e.g., "local"), but better to inject a UserContext/StorageNamespace provider at boundary.

2) Conversation/session scoping
- ConversationManager methods accept user_id to filter sessions, connections, and to open conversation stores; Session holds user_id.
- Impact: Keep user scoping at conversation/service boundaries; internals operate on already-scoped resources.

3) API dependencies and request context
- FastAPI routes depend on get_user_id/get_user_settings/get_user_secrets. DefaultUserAuth returns None (no MU). Settings/Secrets stores accept user_id to fetch namespaced records.
- Impact: For SU, DefaultUserAuth could return a stable derived id (e.g., from local OAuth or machine account). For None, continue returning None but keep boundaries intact.

4) Data model fields
- ConversationMetadata includes user_id; persisted per conversation.
- Impact: Retain field to be forward-compatible; for SU, set to the single user; for None, leave None.

5) Git provider tokens and runtime init
- Runtime init and provider services accept user_id to resolve tokens and MCP config scoping.
- Impact: Boundary keeps responsibility; internal tools shouldn’t inspect user_id.

## Findings for your questions
- How many occurrences of user_id can you find?
  - 339 lines in code/docs (excluding tests), in 68 files. Raw list saved at analysis/user_id_hits_no_tests.txt. Full repo count including tests is 522 lines in 88 files.
- Where are they?
  - See analysis/user_id_hits_no_tests.txt and analysis/user_id_files.txt for file list; top concentrations listed above.
- How many are like `if user_id` but body doesn’t use user_id and what do they do?
  - 7 such blocks detected. Details and snippets saved to analysis/if_user_id_blocks.json.

## Refactor recommendations (deep)
- Introduce explicit boundary abstractions:
  - UserContext (id, email, tokens) — resolves to None (None mode), a concrete id (SU), or request-scoped id (MU). DefaultUserAuth can implement SU by returning a stable local id.
  - StorageNamespace (provides path prefixing) — produces the proper root path using UserContext; core code calls StorageNamespace without seeing user_id.
  - ConversationStoreFactory(Session/ConversationManager boundary) — always constructed with a UserContext; inner methods do not accept user_id.
- Push user policy checks to edges:
  - Route-level authorization (owner checks) stays in API layer. ConversationManager/Session operate on scoped resources, avoiding internal if user_id guards.
- Migrate path helpers:
  - Deprecate get_conversation_* functions that take user_id everywhere. Replace with an object bound to a namespace when the conversation is created (e.g., ConversationPaths with root set from UserContext). Keep compatibility wrappers short-term.
- Clean the if-guards:
  - Replace if user_id blocks that just select alternative paths with direct calls on the injected namespace object. Remove guards where body doesn’t use user_id.

## SU feasibility and implications
- Easy path to SU:
  - Implement SingleUserAuth that returns a stable id (e.g., provider user id or “local”). Wire it into DefaultUserAuth when local OAuth is configured.
  - Update DefaultUserAuth.get_user_id to optionally return the single user id when SU is enabled; otherwise None.
  - Since most usage is already at boundaries (routes, managers, stores, locations), SU works with minimal core changes if we introduce StorageNamespace.
- Risks/complexity:
  - Scattered get_conversation_* helpers and direct user_id threading create churn. Encapsulating into StorageNamespace reduces signatures and future changes.
  - Docker/nested conversation managers also pass user_id; refactor both via a common ConversationManager base that accepts a UserContext.

## MU in OSS vs SaaS
- OSS can remain SU/None, while SaaS continues MU. By abstracting via UserContext and StorageNamespace, SaaS can inject MU adapters from its repo without polluting core.
- SaaS extensions (/enterprise routes, org_id) can build on the same boundary contracts. Avoid direct `user_id` checks in core — use adapters.

## Artifacts saved
- analysis/user_id_hits.txt: full repo hits (522 including tests)
- analysis/user_id_hits_no_tests.txt: hits excluding tests (339)
- analysis/user_id_files.txt: list of files with hits (88 including tests)
- analysis/user_id_hits_no_tests_first200.txt: first 200 lines preview
- analysis/if_user_id_blocks.json: details of if-guards whose bodies don’t use user_id

## Next steps
- Approve boundary introduction (UserContext, StorageNamespace, ConversationPaths).
- I can draft a minimal PR that:
  - Adds these abstractions
  - Refactors storage/locations and EventStore/State to use them
  - Removes the 7 redundant if-guards and simplifies method signatures where practical
- CI: run pre-commit for backend; no behavior change intended.

Counters in this document were generated by repository scans on this branch. See the analysis/ directory for raw grep outputs. They may differ slightly from future scans as code evolves.
