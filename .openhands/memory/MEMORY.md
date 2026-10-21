# Project memory — Agent Canvas (OpenHands/OpenHands)

## `.openhands/setup.sh` auto-run (issue #18737)
- Canvas has NO built-in auto-run today. The only implementation is the
  Cloud/self-hosted **app-server** (`OpenHands/enterprise`,
  `app_conversation_service_base.py` → `maybe_run_setup_script`, called from
  `run_setup_scripts`), which uses `AsyncRemoteWorkspace.execute_command`
  (i.e. `POST /api/bash/start_bash_command`). Local Canvas talks to the
  agent-server only, so on a local stack setup.sh never runs.
- `RUNNING_SETUP_SCRIPT` in `src/api/conversation-service/agent-server-conversation-service.types.ts`
  is a **cloud start-task status only** — it comes from the app-server's start
  task polling, not from local Canvas. Not evidence of local support.
- **HARD BLOCKER (verified 2026-10-19):** the agent-server route
  `POST /api/conversations/{id}/execute_tool` and the `direct_tool_execution_v1`
  capability do NOT exist on SDK main or v1.56.0 — they are an **open, unmerged**
  PR (software-agent-sdk#6099). npm `@openhands/typescript-client` latest is
  1.56.0 and has no `executeTool`. Repo pins client 1.56.0, agentServer 1.56.0,
  minimumAgentServer 1.55.0.
- Do NOT reimplement the endpoint in Canvas (repo ownership rule). The real
  guard for typed access is `src/api/no-direct-agent-server-calls.test.ts`.
- There is NO `check:agent-server-api` / endpoint-audit script (issue text
  claimed one; triage corrected this).
- In-repo `.openhands/setup.sh` is real and meaningful (installs uv, `npm ci`,
  creates `.env`, runs `make-i18n`) — the papercut is genuine.

## Env quirks
- `npm run test` runs `make-i18n` first; `#/i18n/declaration` typecheck errors
  after adding keys are fixed by `npm run make-i18n`.
- MSW route for server info is `*/server_info`, not `*/api/server_info`.
- `npm run lint` is 0-error / ~600 pre-existing warnings (shadcn arbitrary-value).
- Full suite: `npx vitest run` = 851 files / ~9350 tests, ~12 min. Run it with
  `(nohup npm test > /tmp/fulltest.log 2>&1 &)` and poll; a 1800s foreground
  timeout is refused (runtime idle cap ~1200s, foreground capped at 1080s).

## Review-fix learnings (PR #18740, commit 8f632f3)
- Shell-injecting a path into `chmod +x "$p" && . "$p"` is NOT safe: double
  quotes still expand `$(...)`/backticks. Use single quotes with `'\''` for an
  embedded quote (`quoteForShell` in `src/api/setup-script-service.ts`).
- Server capabilities and the pinned browser client version independently.
  `direct_tool_execution_v1` on the server does NOT imply the pinned
  `@openhands/typescript-client` has `executeTool`. Gate on a runtime check of
  the method, not the capability alone (`SetupScriptService.isSupported`).
- Splitting create into create+sendEvent strands a real conversation idle when
  the send fails. Carry the id (`ConversationFirstMessageError`) and persist
  `setStoredConversationMetadata` BEFORE the send.
- `new_worktree` workspaces are NOT a blocker for pre-create probing: the
  per-conversation dir is created by `EventService.start()`
  (`working_dir.mkdir(parents=True)`), and a `new_worktree` copies from the
  attached dir the pre-create probe already read. Probing pre-create is correct.
- Vitest constructor mocks: `mockReturnValueOnce` throws "cannot use with new";
  use `mockImplementationOnce(function X() { return {}; })`. The non-class
  function form trips vitest's `vi.fn()` warning but works.
- Token embedded in the `origin` remote URL goes stale; refresh with
  `git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/<fork>.git"`
  before pushing.
