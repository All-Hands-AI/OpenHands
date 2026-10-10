I'm an AI agent (Codex) helping Engel Nyst (@enyst) with project work.

# Verified DeepSeek scopes: 40 pass, 4 fail, 1 producer block

Verified on 2026-10-10 in the completed OpenAI Codex cloud session **Fix Codex DeepSeek Key Usage**, task `01a1257b-9287-7597-94ac-0dc8ba9e606e`, verification turn `01a1259a-f52c-7603-92cb-0e3c2e45faf4`; incorporated into this PR on 2026-10-11. Three independent agents used fresh, separate stacks and genuine `deepseek/deepseek-flash` calls. Their final reports and command outputs supply the scope and results below.

The 45 reported entry/check scopes cover parts of F22 and F23. **40 passed, four failed on two existing defects, and one remains blocked on a matching legacy/custom-schema producer.** They are not 45 distinct feature IDs, a complete family pass, or a completed 745-ID delta. Counts apply to the three assignments below; overlapping credential-free checks are reported separately.

## Revision and runtime

- Tested checkout: `ac3ea58e42d09178f027878a66b7b2e36bf59abd`, the documentation-only head of [PR #18264](https://github.com/OpenHands/OpenHands/pull/18264). Product source matches frozen TARGET `5a8c3832154b14d2dad651801c0ab3f74c96f02e`.
- Accepted BASE remains `553d4519113192a80fb18376fdb6c1e39fa06387`.
- OpenAI cloud Linux; the selected **OpenHands backend was Local**, not OpenHands Cloud. Canvas 1.26.0, Agent Server/SDK 1.54.0, automation 1.19.3; build identity `31b4983403910d82`.
- Node 24.19.0, npm 11.9.0 and Chromium 151.0.7922.173. Desktop 1440×1000, phone 390×844; long-log checks additionally used 1440×500 and 390×500. Doctor checks passed. No model output or run metadata was injected.

## Separate agent scopes

| Agent assignment | Entry/check scopes | Pass | Fail | Blocked |
|---|---:|---:|---:|---:|
| Assisted forms (`F22.agent-assisted-setup`, `F22.setup-review-confirm`) | 13 | 12 | 1 | 0 |
| Execution and outcomes (F22/F23) | 27 | 23 | 3 | 1 |
| Genuine long finish logs and desktop completion polling | 5 | 5 | 0 | 0 |
| Total | 45 | 40 | 4 | 1 |

The final agent summaries and source-ledger SHA-256 hashes are retained in [transcribed receipts](deepseek-cloud-receipts.json). This is a filtered transcription of completed cloud command outputs, not a replacement for the original append-only ledgers or media. The originating session retained those private artifacts and reports that its root visually inspected the passing and failing captures. This local follow-up did not download or independently inspect those images, and publishes no fabricated media or inaccessible screenshot links.

## Verified behavior

| Stable feature / entry point | Expected and observed result | Scope |
|---|---|---|
| `F22.agent-assisted-setup`: fresh Add Automation → Create → docked prompt | Genuine `automation_form_update` filled prompt and plugin forms; Save/reload/resume preserved values; Form/Conversation and Hide/Show preserved the form | Desktop and phone, selected Local |
| `F22.agent-assisted-setup`: create → enable → Run now | Agent-created prompt/plugin automations completed with real `finish` events and became Successful without reloading the ordinary detail page | Prompt on phone; plugin on desktop and phone |
| `F22.setup-review-confirm`: template/direct custom setup → Prompt → create | Desktop Review/Back/Confirm retained values; separate desktop and phone prompt creation used the selected flash profile | Phone Back/review persistence and the distinct template Plugin review/timezone path remain separate checks |
| `F23.run-now`, `F23.run-status-polling`, `F23.activity-log` | Dispatch and live completion, summary, cost and conversation link appeared; backend independently reported COMPLETED | Desktop and phone |
| `F23.run-linked-conversation`, `F23.activity-log-export` | Conversation link/Back worked; real JSON and CSV activity exports contained the run data | Desktop and phone |
| `F23.run-task-outcome` | Genuine `blocked`, `partial_success` and `unknown` finishes rendered Blocked, Partial and Needs review respectively | Desktop and phone; normal TaskOutcome schema only |
| `F23.debug-with-openhands`: failed run → Logs → Debug | Correct failed-run seed and automation skill reached a real DeepSeek conversation; initial execution observed, then paused | Desktop; launch/handoff only, no completed repair claim |
| `F23.run-logs-modal`: completed/failed ordinary runs | Run/task/system sections, stdout/stderr tabs and closing worked | Desktop and phone |
| `F23.run-logs-modal`: genuine long summary and metadata | Summary/metadata endings, Output/Error tabs and true stdout end reachable; sticky header/X visible; closing did not navigate; phone had no horizontal overflow | 1440×1000, 390×844, 1440×500, 390×500 |

The plugin fixture was a copy of the public packaged `magic-test` plugin. Retained SystemPromptEvent checks confirmed registration of its `magic-word` skill in three execution conversations. The `pong` request did not invoke that skill's trigger, hooks, MCP or scripts; do not treat plugin loading/execution as proof of those additional behaviors.

The long-log producer supplied a **4,596-character outcome_summary and 1,079-character metadata message**, with only a `finish` model action. No backend metadata was edited. Four viewport scopes plus genuine desktop status polling passed, verifying [#18173](https://github.com/OpenHands/OpenHands/issues/18173) / [fix #18175](https://github.com/OpenHands/OpenHands/pull/18175) on pinned Linux Local. F23 now states the passing long-content contract. MacOS/OpenHands Cloud need their own checks; no pre-fix live comparison is claimed.

## Existing failures and exact remaining prerequisite

- **[#18263](https://github.com/OpenHands/OpenHands/issues/18263), two failed scopes:** genuine phone plugin draft Test and an independently produced desktop prompt draft Test finished in the backend, but the open Test runs page stayed Pending. The phone capture was 201.362 seconds after backend completion. The desktop agent confirmed COMPLETED before and after a 45.263-second Successful-row wait. Reload recovered Successful in both cases. The phone capture was at 11:57:10.962621Z following completion at 11:53:49.600611Z.
- **[#17948](https://github.com/OpenHands/OpenHands/issues/17948), two failed scopes:** an actual timeout-1 prompt-preset run ended FAILED without a conversation. Desktop and phone incorrectly called it a script run. This verifies the labeling defect, not every other symptom bundled into that issue.
- **`F23.run-task-outcome`, one blocked scope:** a genuine legacy/custom-schema finish producer is needed for absent/non-string/unrecognized status fallback, plus an actual failed producer carrying a finish summary for failed-run summary retention. The normal TaskOutcome producer verifies only the supported enum statuses. The block is not a missing DeepSeek key or a budget failure; injected metadata and mocked responses are not substitutes.

No duplicate issues were filed. No causal regression or complete product repair is claimed. These failures remain documented as failures.

## Credentials, cost and coverage limits

The supplied DeepSeek key passed model listing, a minimal real flash completion, profile validation and product execution. Credential-backed form assistance and automation execution are verified in the runtime described above.

Recorded SDK estimates were $0.019398252 for eight assisted-form/execution conversations, $0.004847154 for six execution/outcome runs, $0.005270172 for the debug conversation, and $0.004413984 for the long-log worker's four actual producers. Three short producers in the last amount were excluded from coverage after overlapping another assignment. These are partial, differently scoped receipts, not a provider billing total: profile/preset validation, title generation and unrecorded helper calls are excluded. The verification did not enforce or prove the scheduled automation's $10 aggregate cap. Working product checks must not be represented as proof of comprehensive budget enforcement.

Full F22/F23 coverage, distinct template Plugin review/timezone paths, plugin skill invocation, external integrations, other model profiles, OpenHands Cloud, native/Docker/embedded paths and the rest of the affected map remain outside this follow-up. Preserve the remaining prerequisites and keep BASE unchanged.

## Teardown and changes made

Final receipts report zero remaining fixture automations/drafts, every test port closed, no live process in the owned launcher groups, and model conversations finished or paused. Dead unreaped Linux zombie PIDs caused CLI `stop` to report `launcherStopped=false`; independent process-state and port checks confirmed shutdown. Evidence survived teardown. The originating root scanned 384 evidence text files against its two configured credential values with zero matches; raw prompts, private homes, keys, browser state and logs remain unpublished.

The maintained F22 recipes incorporate the exercised form, navigation, creation and execution commands; the index identifies those verified paths, and F23 states the passing long-log behavior. BASE remains unchanged while the full delta is incomplete.
