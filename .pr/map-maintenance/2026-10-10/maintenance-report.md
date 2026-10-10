I'm an AI agent (Codex) helping Engel Nyst (@enyst) with project work.

# Delta maintenance: verified map corrections, baseline retained

BASE: 553d4519113192a80fb18376fdb6c1e39fa06387.
TARGET: 5a8c3832154b14d2dad651801c0ab3f74c96f02e.

The current PR incorporates genuine DeepSeek verification of assisted automation forms, prompt/plugin execution, task outcomes, exports, debug launch and long finish logs. The model-backed checks ran on fresh Linux stacks selecting the Local OpenHands backend, with SDK 1.54.0 and automation 1.19.3. Their 45 entry/check scopes yielded **40 pass, 4 fail, 1 blocked**; the remaining producer requirement is a genuine legacy/custom-schema finish. DeepSeek assistance and execution are verified paths in the maintained map.

This is a DELTA pass. Twelve first-parent commits changed 172 paths; all resolved to merged PRs, all 89 map references were audited in their owning repositories, and source coverage includes F01–F27 (745 stable IDs). SDK/client/automation changes and shared consumers widen the required delta to all 27 families. Live coverage remains scoped, so BASE is unchanged.

Covered merged PRs: [18228](https://github.com/OpenHands/OpenHands/pull/18228), [18219](https://github.com/OpenHands/OpenHands/pull/18219), [18243](https://github.com/OpenHands/OpenHands/pull/18243), [17758](https://github.com/OpenHands/OpenHands/pull/17758), [18237](https://github.com/OpenHands/OpenHands/pull/18237), [18175](https://github.com/OpenHands/OpenHands/pull/18175), [18253](https://github.com/OpenHands/OpenHands/pull/18253), [17199](https://github.com/OpenHands/OpenHands/pull/17199), [17200](https://github.com/OpenHands/OpenHands/pull/17200), [17201](https://github.com/OpenHands/OpenHands/pull/17201), [17242](https://github.com/OpenHands/OpenHands/pull/17242), [17688](https://github.com/OpenHands/OpenHands/pull/17688).

## Current verified behavior and map changes

- **F22.agent-assisted-setup:** the map contains literal credential-free draft save/reload/resume/custom-script tests and the exercised genuine model commands. Real `automation_form_update` filled prompt and plugin forms; desktop Hide/Show, phone Form/Conversation, associated-draft resumption, final creation and ordinary prompt/plugin Run now completed successfully. Fresh phone creation is recorded separately from resizing a desktop form. Final assisted creations are inactive until enabled; ordinary detail polling becomes Successful without reload. Draft Test's automatic completion remains a known failure with separate reload recovery.
- **F22.setup-review-confirm:** desktop Prompt Review/Back/Confirm retained values and created the selected flash automation. Separate desktop and phone prompt creation/execution checks passed. Agent-created plugins loaded the public `magic-test` fixture and registered `magic-word`; plugin skill invocation and the distinct template Plugin review/timezone path remain separate checks.
- **F23:** genuine successful runs updated status, summary, cost and conversation links without reload; conversation links and JSON/CSV exports worked on desktop/phone. Genuine `blocked`, `partial_success` and `unknown` finishes rendered Blocked, Partial and Needs review. Failed-run Debug launched the correctly seeded real model conversation and was paused after initial execution; no completed repair is claimed.
- **F23.run-logs-modal:** a real finish produced a 4,596-character outcome summary and 1,079-character metadata message. Summary/metadata endings, Output/Error tabs, stdout end and close controls were reachable at 1440×1000, 390×844, 1440×500 and 390×500; the header remained visible and phone had no horizontal overflow. This verifies [#18173](https://github.com/OpenHands/OpenHands/issues/18173) / [fix #18175](https://github.com/OpenHands/OpenHands/pull/18175) on pinned Linux Local, and the map states the passing contract.
- **F24.encryption:** key-only set/rotate/clear passes desktop/phone on pinned automation 1.19.3 in two fresh stacks. Each save dirties the export; without an intervening automation PATCH, the next sync commits ciphertext, different ciphertext, then plaintext. The maintained recipe reflects [automation#563](https://github.com/OpenHands/automation/pull/563) / [#551](https://github.com/OpenHands/automation/issues/551). [Desktop readbacks](encryption-root/desktop-export-results.json), [phone readbacks](encryption-root/phone-export-results.json), [desktop recording](encryption-root/desktop-key-only.mp4), [phone recording](encryption-root/phone-key-only.mp4). The F24 peer covered 26 IDs through 28 scopes: 25 pass, 2 Cloud prerequisites blocked and 1 non-404 status-error prerequisite not-run, including unsupported UI on automation 1.7.1.
- **README:** verified form-tool and split-view paths are linked to F22. Remaining home handoff, full draft-management, replacement editor, ACP and Cloud boundaries are named with their actual prerequisites.
- **F26:** seven native terminal scopes across five IDs pass (version/-v, info, help, two flag-conflict cases and missing-build scratch copy). These are CLI proof; Docker, Electron and embedded-host execution need their own checks.

The credential-free F22 checks also verified draft save/reload/resume, phone draft rename/Delete, template/import/form/responder behavior and generated callback-only script execution. [Desktop draft save](draft-root/draft-desktop.mp4), [phone resume](draft-root/resume-phone.mp4) and [phone renamed draft](draft-root/resumed-phone.png) retain the genuine captures. Their viewport comes from the media, not a later ledger registration.

## Scoped genuine model results

| Agent assignment | Entry/check scopes | Pass | Fail | Blocked |
|---|---:|---:|---:|---:|
| Assisted forms | 13 | 12 | 1 | 0 |
| Execution and outcomes | 27 | 23 | 3 | 1 |
| Long finish logs and desktop completion polling | 5 | 5 | 0 | 0 |
| Total | 45 | 40 | 4 | 1 |

[Detailed model results](deepseek-cloud-results.md) and [filtered source receipts](deepseek-cloud-receipts.json) give the tested entries, final agent counts and ledger hashes. These are entry/check scopes, not distinct complete-ID passes. Credential-free F22, F24 and F26 checks overlap other scopes and are not added into a claimed 745-ID coverage total. No full-family or full-delta pass is inferred.

## Current defects

- [#18263](https://github.com/OpenHands/OpenHands/issues/18263): draft Test stays Pending after backend COMPLETED. Independently verified with callback-only scripts, a real desktop prompt test and a real phone plugin test. The desktop model test stayed Pending through a 45.263-second Successful-row wait; the phone capture was 201.362 seconds after completion. Reload recovered Successful. The map preserves automatic completion as Expected and documents the failure. [First script backend receipt](../../bugs/2026-10-10/draft-run-status/first/sanitized-run-summary.json) and [second receipt](../../bugs/2026-10-10/draft-run-status/second/second-sanitized-run-summary.json) remain accessible.
- [#17948](https://github.com/OpenHands/OpenHands/issues/17948): a real timeout-1 prompt run ended FAILED without a conversation, but the desktop/phone activity row called it a script. This result covers the labeling symptom.
- F22's existing [#17959](https://github.com/OpenHands/OpenHands/issues/17959) blank no-match search and [#18061](https://github.com/OpenHands/OpenHands/issues/18061) blank Default after kind switches remain failures.

Existing issues are linked; no duplicates or product fixes are included. No before-change live comparison establishes a causal regression.

## Remaining prerequisites and coverage

The model-result table's single block needs a **genuine legacy/custom-schema finish producer** for absent/non-string/unrecognized status fallback, plus an actual failed producer carrying a finish summary for failed-run summary retention. The normal TaskOutcome producer proves its supported enum statuses. Injected run metadata or mocked model output is not live proof.

Other remaining coverage includes the home Code/Automate handoff, complete dashboard draft management and replacement editor; template Plugin review/timezone and plugin skill invocation; Pi/OpenCode ACP presets and genuine execution; Cloud organization handback, enterprise setup-state/tour entitlements, member permissions and multi-organization Git Sync; native/Docker/embedded paths and the rest of the affected recipes. F24.error-state needs a genuine non-404 status failure while automation remains healthy. The map index records these boundaries.

Unmapped-path accounting: scripts/check-sdk-version-sync.mjs is a contributor gate; acp-brand-marks.ts belongs to ACP icon consumers; automation-form.ts is shared by composer/conversation and automation-form consumers. F22 names the form constant/session/service and exercises the form tool and split navigation.

## Runtime, validation and teardown

Canvas 1.26.0 product source was built at TARGET. Genuine model verification used documentation head `ac3ea58e42d09178f027878a66b7b2e36bf59abd`, whose product source matches TARGET, with Node 24.19.0/npm 11.9.0, Chromium 151.0.7922.173, SDK 1.54.0 and automation 1.19.3; build identity `31b4983403910d82`. Credential-free and Git Sync captures used macOS 27.0.1/Chrome 155.0.8059.39, Node 25.9.0/npm 11.12.1 and uv 0.11.19, with the same backend pins. Builds and doctor passed. Default themes/fonts follow each recorded run; font metrics were not separately enumerated.

Reported model SDK estimates are listed in the detailed results; validation/title/helper costs are not fully accounted, so this is not a test of the scheduler's aggregate budget enforcement. The supplied DeepSeek key and real model calls succeeded.

Map structure, route/component coverage, cited test IDs, BASE ancestry and explicit BASE/TARGET affected checks pass. These static gates validate the map and are separate from live behavior.

Owned automations/drafts were deleted, Git Sync disabled/cleared, and retained evidence survived teardown. Linux model stacks had no live owned-group processes and all ports refused connections; unreaped dead zombie PIDs account for CLI `launcherStopped=false`. The cloud root reviewed the original private captures; published model receipts are filtered transcriptions of its completed reports/outputs. Credential values, raw system prompts, browser state and private homes remain unpublished. The source session scanned 384 evidence text files with no matches against its two configured credential values.

The accepted BASE remains unchanged because the full delta and its distinct backend/platform entry points are incomplete.
