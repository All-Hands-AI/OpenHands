# Daily delta maintenance, 2026-10-13

I'm an AI agent (Claude Code) helping Engel Nyst (@enyst) with project work.

**Verdict: delta pass, changed.** Range `553d4519113192a80fb18376fdb6c1e39fa06387..2bdc0e9d6c5940bc3d4667fb2127fbb753b2f7c8`: 62 first-parent commits, all resolved through the commits/pulls API to 62 merged PRs, and 432 changed paths. `map affected` lists 25 families (F01-F13, F16-F27), 58 shared paths (tailwind.css, translation.json, theme definitions, API clients) and 19 unmapped paths. The unmapped `src/` paths now sit on Source lines: ACP marks and conflict warnings in F13, the LLM provider-connection constant in F10, the DigitalOcean logo and MARS paths in F25. The rest are build or launcher scripts that are not user-facing. Proposed next baseline: `main@2bdc0e9d` (2026-10-13). Merging this PR accepts it, despite the blocked steps listed below.

## Run identity

- Live stacks were built from this checkout at TARGET with `control-openhands launch --new`: Linux, headless Chromium 1194, Node 24.21.0, Agent Server 1.54.0 (matches the pin), automation 1.19.3, model deepseek-flash (one deepseek-pro turn).
- Workers sharded by family:
  - w1: F01-F03, F09, F16, F25
  - w2: F04-F08, F27
  - w3: F10-F13, F17-F20
  - w4: F21-F24, F26
- An independent agent re-ran every edited family on a fresh stack (v1-v4). It accepted each edit or sent corrections, and the corrections were applied. Comparison runs at BASE `553d4519` for regression verdicts came from that worktree's own CLI.
- Static checks: `map check` reports 27 files, 760 IDs (was 747) and no problems. `map coverage` shows 31 routes and 29 feature directories, all mapped. `map testids` shows 1069 cited test ids, 0 unresolved.

## Coverage ledger (rows across the eight target runs)

| Family | pass | fail | blocked | not-run | xfail |
|---|---|---|---|---|---|
| F01 | 17 | 1 | 2 | 4 | 0 |
| F02 | 6 | 2 | 1 | 0 | 0 |
| F03 | 25 | 2 | 0 | 0 | 0 |
| F04 | 19 | 0 | 0 | 0 | 0 |
| F05 | 6 | 2 | 1 | 0 | 0 |
| F06 | 14 | 3 | 1 | 0 | 0 |
| F07 | 16 | 2 | 0 | 0 | 0 |
| F08 | 11 | 2 | 0 | 0 | 0 |
| F09 | 18 | 0 | 0 | 0 | 0 |
| F10 | 17 | 5 | 0 | 1* | 0 |
| F11 | 4 | 0 | 0 | 0 | 0 |
| F12 | 5 | 0 | 1 | 0 | 0 |
| F13 | 25 | 3 | 2 | 0 | 0 |
| F16 | 4 | 5 | 0 | 0 | 0 |
| F17 | 15 | 2 | 1 | 0 | 0 |
| F18 | 3 | 0 | 0 | 0 | 0 |
| F19 | 2 | 0 | 0 | 0 | 0 |
| F20 | 3 | 0 | 0 | 0 | 0 |
| F21 | 21 | 7 | 0 | 0 | 0 |
| F22 | 11 | 3 | 0 | 0 | 0 |
| F23 | 22 | 8 | 0 | 0 | 0 |
| F24 | 10 | 0 | 0 | 0 | 0 |
| F25 | 21 | 8 | 8 | 0 | 3 |
| F26 | 9 | 2 | 4 | 2 | 0 |
| F27 | 5 | 0 | 0 | 0 | 0 |
| **Total** | **309** | **57** | **21** | **7** | **3** |

\* A row with a mistyped ID was recorded as not-run and then retracted.

Rows count repeated checks by the worker and its independent verifier separately. 289 distinct sub-feature IDs were recorded. F14 and F15 had no changed paths. Every fail row is a known open issue or one of the new defects below.

## Closed issues re-driven

- **Fixed and verified live; notes removed or rewritten:**
  - #17915 (F04/F07 confirm-button test ids)
  - #17920 (F06 rejected action resolves its group)
  - #17926 (F05 fast draft flush)
  - #17928 (F06 Ctrl shortcuts)
  - #17938 (F10/F13 taken-name message)
  - #17957 (F18 Escape)
  - #17958 and #18181 (F17)
  - #18060 (F13 menu keyboard)
  - #18061 (F22 Default profile)
  - #18173 (F23 logs dialog)
  - #18178 (F26 IPv6-less Docker)
  - #18206 (F07 hooks text)
  - #17884 (F01 hello reply)
- **#18303 (F10):** source-verified only. Both call sites use `SETTINGS$SUBSCRIPTION_MODELS_NOT_LOADED`, which is translated in every locale. A live drive needs a slow subscription-models request.

## Defects filed (each reproduced by a second, independent agent; fix PR linked)

| Issue | Feature | Regression | Fix PR |
|---|---|---|---|
| #18378 | F04/F07: leaving a setup conversation tags the next one | yes, #17242 on #17200 | #18385 |
| #18379 | F05/F22: setup composer prompt stays as Home draft | yes, #17688 | #18392 |
| #18380 | F23: edit page toasts raw 422/404 | yes, #17688 | #18391 |
| #18381 | F21: tiles count draft test automations | yes, #17242 | #18393 |
| #18382 | F21: draft delete confirmation ignores Escape, no dialog | yes, #17242 | #18394 |
| #18383 | F10/F13: "A meta-profile…" in LLM/agent editors | yes, #18144 | #18384 |
| #18386 | F03: Code/Automate toggle white on light pill | yes, #17199 | #18402 |
| #18387 | F02: success toasts white in light themes | no (since #16632) | #18403 |
| #18388 | F16: Application settings stale after backend switch (Save can write the other backend's Git identity) | no | #18401 |
| #18389 | F25: backend modals neither take nor keep focus | no | #18400 |
| #18390 | F25: new backend asked for the old conversation id (intermittent) | not established | none: root cause not pinned down |
| #18395 | F06: confirmation labels wrap in 26 px buttons | no (#18127 only lengthened them) | #18397 |
| #18396 | F08: File discovery dialog wider than a phone | no (since #17869) | #18398 |

Linked instead of filed: the MCP add and delete requests sent three times go on #17932 (same `withRetry` cause). The ACP auth banners at 1.10:1 and 1.26:1 in Light+ go on #18004. Clearing the time and saving midnight is a new path for #17948; open PR #18260 changes only the now-unused edit modal.

Still reproducing, with notes re-dated: #18302, #17955, #17135 (new symptom since #18218), #18202, #17567, #18356 (new F06 note), #18263, #18341, #18362 (new F26 row), #18233 (xfail), #18324, #17927, #17900, #17953.

## Map changes

- **New rows:**
  - F04.automation-setup-tag
  - F08.files-discovery-settings
  - F13.acp-local-presets and F13.acp-model-discovery
  - F16.backend-switch
  - F21.saved-drafts
  - F25.providers-tab, F25.digitalocean-sign-in, F25.digitalocean-agents and F25.digitalocean-backend-removal
  - F26.automation-startup-failure
  - F03.launcher-mode-toggle and F03.launch-automate-mode
- **Rewritten:**
  - Every automation edit row (F21.edit and F23.edit-*): kebab Edit now opens `/automations/setup?automationId=<id>` (#17688).
  - F03 row-menu Edit
  - F06 confirmation recipes
  - F01 choose-agent: Pi and OpenCode, local only (#17758)
  - F13 ACP rows (#17758, #18131)
  - F17 library count, 56 cards with Bitbucket (#18336)
  - F09 breakpoint sweep (#18256)
  - Theme-colour checks for #17646, #18270, #18321, #18330, #18333 and #18346

## Blocked (prerequisite → route attempted)

- **OpenHands Cloud account:** F25 cloud rows, including the #18228 `?org=` hand-back; F01.locked-cloud-first-run; F17.native-git-tabs; F13.cloud-read-only; F02.alert-banner (needs Cloud alerts).
- **OHE cookie-auth deployment:** F01.cookie-auth-redirect.
- **DigitalOcean Managed Agents account:** F25.digitalocean-agents, F25.digitalocean-backend-removal. The sign-in screen was proven with the MARS bridge on; `launch` has no flag for `MARS_WEB`, see #18350.
- **Logged-in ACP agent:** F05.slash-plan-code (#18251), F06.live-activity (#18371), F13.acp-conversation.
- **Electron binary:** F26.desktop-boot-splash, F26.desktop-main-window.
- **helm binary and a cluster:** F26.helm-chart.
- **Host-app example:** F26.lib-host-app.
- **No route to fail `/api/meta-profiles` alone:** F12.load-error.

Not-run: F01 cloud-login, hello-close, recommended-automation and bootstrap-loading; F26 cli-port-in-use and docker-conversation-runtime. Their source is unchanged in range.

## Harness notes

- `launch` cannot set `MARS_WEB` (#18350 may remove the need).
- `bug run F25.selector-dropdown` needs Local active first.
- `evidence add` accepts unknown IDs.
- Launching a BASE worktree needs that worktree's own `control-openhands`.

## Teardown

Every stack this pass launched was stopped with `control-openhands stop` (ports closed), and its evidence survived. Fixtures were deleted or left only in the stopped private runs. No keys appear in any published file.
