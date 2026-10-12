# Daily delta maintenance — 2026-10-12

I'm an AI agent (Codex) helping Engel Nyst (@enyst) with project work.

Partial delta: this PR corrects F17 MCP verification recipes and records an independently reproduced F18 source-filter failure. No accepted baseline is proposed. Every pass below names its Local backend and viewport; neither this report nor green CI proves the rest of the map.

## Frozen scope

- BASE: `553d4519113192a80fb18376fdb6c1e39fa06387` (2026-10-09).
- TARGET: `0f1b6f62507f1ccdb4e63f61cf3dc48356a0d4fa`.
- Canonical repository: OpenHands/OpenHands; primary origin is enyst/playground. Publication repository: verified child fork smolpaws/OpenHands, configured identity smolpaws. Upstream push permission is false; fork push permission true.
- All 46 first-parent commits resolve through GitHub commit associations to 46 merged PRs with matching merge SHAs. Descriptions, files, reviews/discussions and available owning issue criteria were inspected privately; linked Linear-only criteria remain unavailable. Intent is separate from runtime proof.
- All 351 changed paths are accounted for in [path-accounting.json](path-accounting.json). Shared styles, settings/service clients, runtime pins and builder changes widen the required delta to 27 families / 747 IDs. Five initial unmapped paths have explicit consumers or non-user-facing reasons. This is a source inventory, not completed runtime coverage.
- Static gates: map check 27 families / 747 IDs; coverage 31 routes / 29 feature directories with the context-menu exclusion; all 1031 cited testids resolve. BASE is known and an ancestor; complete history is present. Locked `npm ci --ignore-scripts` and `npm run build:app` passed. Node 25.9.0/npm 11.12.1; npm reported dependency engine warnings. Chrome 155.0.8059.39, macOS 27.0.1.

The full merged PR list is in [merged-prs.md](merged-prs.md).

## Proven corrections

| Mapped row | Live outcome | Limit |
|---|---|---|
| F17.save-as-secret | Space clears the native checkbox; Enter on help leaves it cleared; label click selects it. Focus outline and long GITHUB_PERSONAL_ACCESS_TOKEN remain readable and inside the row on OpenHands-Neutral and Light+, desktop 1440×1000 and phone 390×844. | Selection before installation. No credential-install/persistence or other palette proof. |
| F17.delete-server | Stale editor Delete returns a real 404 and exactly one error toast; editor stays open; fixture remains absent after reload. | MCP editor, desktop and phone; not service-down 502. |
| F17.enable-disable | Stale card toggle returns a real 404 and exactly one error toast; fixture remains absent after reload. | MCP card, desktop and phone; not the conversation Overview toggle. |

These reconcile #18278's theme-aware selection intent and #18182's fix for #18181. Existing IDs/counts stay stable. Expected behavior remains intact. Root ledger: **8 pass / 0 fail / 1 blocked / 0 not-run**, covering 3 passed IDs plus one blocked model ID in scoped entries; [reviewed outcomes](root-outcomes.json). The raw private append-only ledger is retained. New literal recipes were re-driven after editing. The earlier root browser page/context closed while stack doctor remained healthy; reload failed and resetting only the owned browser recovered. Origin unconfirmed; no product bug filed from this environment/harness event.

A second owned root stack `root-f17-tab` re-proved native Tab focus in all four theme/viewport combinations (four passes, overlapping the first run's selection scopes and counted once in the reviewed latest root rows). The reporter captures viewport when a row is appended; the first root phone 404 rows and the F18 desktop row were appended after a viewport switch. Reviewed outcomes retain that append-time metadata separately and name actual PNG/video dimensions. Private raw ledgers are unchanged.

Fresh F17 peer `f17-peer-live`: **20 pass / 1 fail / 9 blocked / 9 not-run**, 39 scoped entries / 31 IDs; [reviewed ledger](peer-f17-outcomes.json). The eight changed MCP scopes all passed independently. The one failure reproduces already-mapped #17922 (Sentry empty unsupported install modal); no new ticket. Time catalog Install was rejected by automatic approval review because it downloads/executes third-party code and persists configuration; no retry or alternate download bypass. Install-dependent checks need explicit approval. Remaining unexercised family steps are not-run. This is not a full F17 family pass.

F18 `F18.facets`: root **0 pass / 2 fail / 0 blocked / 0 not-run**, separate desktop/phone same-name source-filter scopes; [reviewed outcomes](root-f18-outcomes.json). Fresh Local browser has one public skill-creator, then a genuine local fixture adds a second distinct definition. Source filtering then retains an extra local card under Built in and renders two identical local-path cards under This project. Matches existing [#18287](https://github.com/OpenHands/OpenHands/issues/18287); origin unconfirmed, no causal PR or pre-change regression claim. The fixture was removed and a reload restored exactly one public card. No agent/model ran. Independent fresh F18 peer `f18-collision-peer`: **0 pass / 2 fail / 0 blocked / 0 not-run**, same excluded-local/duplicate-local sequence on both viewports; [peer outcomes](peer-f18-outcomes.json). Its rows were appended before viewport changes; fixture cleanup restored one public card, all owned ports stopped, media reviewed. Desktop and phone captures live under `.pr/bugs/2026-10-12/skill-source-collision/`.

Reviewed scoped total: **52 entries = 28 pass / 5 fail / 10 blocked / 9 not-run** across root latest F17, F17 peer, root F18 and F18 peer. Cross-run overlap is deliberate independent proof and does not imply completed families. Native-Tab root repeats are counted once. Required denominator remains 27 affected families /747 IDs; full entrypoint/control-flow matrix is unfinished.

## Required delta still incomplete

Owning-repository link audit: 110 references = 57 issues / 53 PRs, no API errors. Fourteen Canvas issues closed since BASE: #17884 (F01), #17915 (F04/F07), #17920 (F06), #17926 (F05), #17928 (F06), #17938 (F10/F13), #17957 (F18), #17958 (F17), #18060 (F13), #18061 (F22), #18173 (F23), #18178 (F26), #18181 (F17), #18206 (F07). Only #18181's two changed failure paths were re-proved here; the other closure rechecks remain not-run or model-blocked. Closed SDK #5460 still has pinned-version failure wording requiring real model retesting. No new SDK/automation issue closure since BASE was found. Historical map proofs remain historical.

Private source readers covered all families and retained all 747 expected rows, family entrypoints and prerequisites. Their inventory is not a fully expanded per-entrypoint/control-flow matrix and is not added to the scoped check denominator. Candidate stale text includes draft flushing (F05), profile name/menu and hooks/confirmation selectors (F07/F13), onboarding checklist labels/tour stops (F02), and legacy automation Edit modal selectors (F03/F21/F23). These are unverified source findings; their map wording remains pending live proof. Stacked automation PR review concerns also remain unconfirmed and are not new bug claims.

Model operations, validation and real-key reads: **0; USD 0 / 10**. The scheduled DeepSeek key is absent. Existing configured key sources were not opened because an aggregate bound for parent/child/title/planner/condenser/judge/automation calls has not been established. Every model-dependent recipe needs that bound plus a configured cheap DeepSeek key. No paid provider substitution or mocks. Cloud entrypoints need an authenticated entitled Cloud backend; Docker needs a binary/daemon (the binary is absent here); native Electron and embedded Canvas entrypoints were not driven. Unexercised credential-free families and backend/control-flow entrypoints are **not-run**, not silently passed. BASE is retained for this unfinished required delta.

New current-skill requirement: audit open `bug` issues opened since BASE. Eight Canvas and two SDK issues were found, zero automation bugs; [owning candidates](recent-bug-candidates.md). At source audit time, missing map references were Canvas #18319, #18301, #18299 and #18287, plus SDK #5718. SDK #5711 is explicitly outside the mapped Canvas consumers: current source does not use the owning client's RemoteState/RemoteConversation cached getters. F18 #18287 received fresh failure wording after live reproduction. Only an independently reproduced candidate can receive fresh failure wording. Other candidates are **not-run** with their owning issue prerequisites; no non-reproduction comment or duplicate issue is justified by a source audit.

## Evidence and cleanup

Root run `root-f17` used real Local Agent Server/SDK 1.54.0 and automation 1.19.3 with an isolated private home. All root stacks reused the same free port block serially. Owned ports were ingress 18810, agent-server 18811, automation 18812, frontend 18813 and reserved editor 19811. Serial `--min-free-mb 0` followed Engel's previously recorded single-stack authorization. Screenshots and canonical browser recordings were visually reviewed, including decoded transition frames; no keys or raw traces are published. Only retained allowlisted evidence is under `root/`. The run stopped and all five owned ports closed; evidence survived. Private runtime homes/logs/ledgers remain outside GitHub.

Evidence is temporary review material. The repository's PR Artifacts workflow handles approval cleanup for same-repository PRs and post-merge cleanup PRs for forks. Commit-pinned artifact URLs survive removal from main. This PR does not require permanent-main retention.
