I am an AI agent helping Engel Nyst (@enyst) with project work.

# Weekly verification maintenance — reviewed report

**Verdict: changed and partial.** Source review and scoped live observations span 28/28 feature families. The frozen map has 779 stable behavior IDs. All live workers have finished. Capacity-blocked packaging and unavailable branches are not invented as passes; coverage attempts and cleanup are complete; publication review remains separate. Snapshot: 2026-10-17T22:05:49.152816+00:00.

Accepted BASE `d3a58cd1cc045bbb1b24f2c8c0d79a8404ef239b`; frozen TARGET `61a3bd93e642a0ff4def73b29496a73245628209`. SDK 1.55.1, automation 1.20.1. No accepted-baseline advancement.

**733/779 IDs have a recorded observation:** 633 pass-only observations, 88 existing-known product failures, 4 newly filed product failures, 0 IDs classified unresolved, and 8 fix assertions. Separately: 46 blocked-only, 0 not-run-only and 0 unreconciled IDs. These are mutually exclusive reviewed categories, not complete passes for every branch of an observed ID.

Failure taxonomy reviews both actual `fail` and `xfail`: newly filed > existing known > invalid-measurement-only; unresolved stays explicit. Two invalid initial hook measurements remain failed checks; corrected measurements reproduce the known hook issue, so that ID is existing-known. The raw highest-result label `xfail` alone must not be mistaken for the count of all known product failures.

**Latest recorded checks, original result labels kept separate:** pass 1150, fail 146, xfail 14, xpass 13, blocked 98, not-run 126. These count entry-point rows, not stable IDs. No fail is relabeled pass. [Classification detail](failure-summary.json).

| Family | IDs | Pass observed | Existing failure | Filed failure | Unresolved | Fix assertion | Blocked only | Not-run only | Unreconciled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F01 | 22 | 18 | 1 | 0 | 0 | 0 | 3 | 0 | 0 |
| F02 | 28 | 23 | 0 | 0 | 0 | 0 | 5 | 0 | 0 |
| F03 | 42 | 35 | 4 | 0 | 0 | 0 | 3 | 0 | 0 |
| F04 | 41 | 35 | 4 | 0 | 0 | 0 | 2 | 0 | 0 |
| F05 | 25 | 20 | 3 | 0 | 0 | 2 | 0 | 0 | 0 |
| F06 | 36 | 31 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| F07 | 25 | 20 | 4 | 0 | 0 | 1 | 0 | 0 | 0 |
| F08 | 34 | 30 | 1 | 0 | 0 | 1 | 2 | 0 | 0 |
| F09 | 26 | 23 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| F10 | 34 | 27 | 3 | 0 | 0 | 1 | 3 | 0 | 0 |
| F11 | 21 | 15 | 5 | 0 | 0 | 0 | 1 | 0 | 0 |
| F12 | 25 | 22 | 1 | 0 | 0 | 0 | 2 | 0 | 0 |
| F13 | 22 | 18 | 3 | 0 | 0 | 0 | 1 | 0 | 0 |
| F14 | 12 | 11 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| F15 | 23 | 18 | 4 | 0 | 0 | 0 | 1 | 0 | 0 |
| F16 | 20 | 16 | 2 | 0 | 0 | 1 | 1 | 0 | 0 |
| F17 | 31 | 26 | 3 | 0 | 0 | 0 | 2 | 0 | 0 |
| F18 | 22 | 17 | 4 | 0 | 0 | 0 | 1 | 0 | 0 |
| F19 | 25 | 17 | 7 | 1 | 0 | 0 | 0 | 0 | 0 |
| F20 | 24 | 18 | 5 | 0 | 0 | 0 | 1 | 0 | 0 |
| F21 | 35 | 32 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| F22 | 29 | 25 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| F23 | 41 | 35 | 5 | 1 | 0 | 0 | 0 | 0 | 0 |
| F24 | 26 | 23 | 1 | 0 | 0 | 0 | 2 | 0 | 0 |
| F25 | 33 | 18 | 6 | 0 | 0 | 0 | 9 | 0 | 0 |
| F26 | 34 | 27 | 3 | 1 | 0 | 0 | 3 | 0 | 0 |
| F27 | 30 | 24 | 4 | 0 | 0 | 1 | 1 | 0 | 0 |
| F28 | 13 | 9 | 2 | 1 | 0 | 1 | 0 | 0 | 0 |

## Findings and proof

Four separately filed product defects, all in the authorized Canvas fork:

- [#124](https://github.com/enyst/playground/issues/124): an invalid draft retains stale Latest test passed status. Upstream copy18601 noted; no duplicate filing.
- [#125](https://github.com/enyst/playground/issues/125): automation detail controls clip at phone width, including RTL.
- [#126](https://github.com/enyst/playground/issues/126): built ESM Canvas library fails in a normal Vite host at requireReact.
- [#127](https://github.com/enyst/playground/issues/127): accepted plugin parameter edits are absent from actual creation. SDK 1.55.1 lacks runtime parameter support; merely forwarding a field is not claimed as the fix.

One unresolved failing check remains on F26.desktop-external-links even though that ID is classified existing-known from separate genuine #17112 paths. Electron external Markdown links remain an **unresolved integration candidate**, not a fifth filed defect: two real clicks failed to hand off, while the direct real OS browser control succeeded. Intake/root cause remains open. Existing SDK4554 critic behavior and SDK5622 cipher-mismatch preservation failures are existing-issue retests. Repeated checks are not additional issues; origins remain unconfirmed without comparable baseline evidence.

13 narrow recipes have verified two BASE xfail and two TARGET xpass attempts each: 26+26 attempts. [Scoped proofs](paired-proofs.json). Broader failures and unproved branches remain; selector comparison stays inconclusive because descriptors differ. A proof does not retire an entire issue or family.

## Runtime results and boundaries

Successful actual model IDs are `deepseek/deepseek-flash` and `deepseek/deepseek-v4-pro`; `deepseek-pro` is a profile label. Genuine model/tool evidence covers selected planning, tools, secrets, critic and compaction paths. Provider/Cloud/ACP branches without their exact prerequisites remain separate; no total provider bill is claimed.

A real Canvas-created Docker conversation completed a Flash call and one terminal action in its isolated container workspace. Host-mount/file/hostname correlation passed; deleting the conversation removed its container/workspace and the launcher returned to Local. A task-owned pinned minimal-image derivative added only public CA/proxy configuration. The stock image’s managed-proxy egress failure and the successful derivative are distinct outcomes. [Sanitized runtime proof](docker-runtime-proof.json). This does not pass the all-in-one Canvas image packaging test, browser/ACP capability matrix or ARM/Windows cases. The earlier postgres smoke is prerequisite-only and is excluded from mapped Canvas image observations. The original prompt-bearing screenshot remains private.

Helm 3.19.0 lint and default/Ingress template renders are valid static chart-artifact checks; no Kubernetes installation, token-readability or cluster proof is claimed. Live install needs an authorized disposable cluster/context. Actual TMUX explicit/default directory creation and frontend-only noncreation passed, with owned cleanup. Non-DNT consent used only an owned loopback discard sink: genuine opt-in, opt-out/re-opt-in within 3.563 seconds, final consent denied and owned cleanup. [Runtime checks](runtime-checks.json).

Real Electron/Xvfb failure splash was exercised. Playwright CDP clicked Copy, observed Copied after IPC completion, then Quit exited normally; clipboard contents were not read/exported, and owned display/process/private state was cleaned. External-link handoff is the separate unresolved candidate above, not a lack-of-controller limitation.

Verification-only harness corrections have 73 passing controller tests, syntax checks and live re-drives. Map checks retain 28 families/779 IDs and resolve 1110 cited test IDs. Product fixes and expected-behavior changes that approve bugs are excluded.

## Remaining work and handoff

Recorded missing prerequisites include authorized Cloud/OAuth/third-party accounts, native Windows/ARM branches and a Kubernetes cluster. Enabled recurring-template confirmations were not clicked under the explicit no-recurring-fixture boundary; inert events/disabled drafts are distinct consumers, not substitutes. The missing-manifest variant was constructible and has now been exercised; it is not an external blocker. The missing-manifest variant completed: direct 404/sidebar absence passed, while desktop/phone Home dead Schedule links plus one no-manifest toast reproduced existing #18210. The serial packaging attempt is now capacity-blocked, not pending: frontend build passed in 120.79 seconds, then the full base unpack was canceled at the 5 GiB reserve after 69.16 seconds, with no final Canvas image/container. No OOM occurred; transport/preflight corrections are setup outcomes, not product failures. [Sanitized packaging receipt](docker-packaging.json). The remaining isolated runtime checks finished: real main-window failure transition, standalone TMUX startup, cross-run terminal isolation, and desktop/phone Home Docker Clear passed. Three real remote-navigation branches reproduced existing #17112; inert custom-scheme refusal is limited observation, not a fix retirement. Exact early-stop late-ingress reproduction matches existing #16257; its historical out-of-scope disposition is superseded by current mapped proof without erasing that history.

All 22 CLI runs now have absent private directories and closed owned ports in the read-only snapshot. Retained artifacts include 1103 PNGs and 712 JSON files with readable hashes. Six additional manual runtime fixture receipts verify 27 file hashes, absent private paths, closed owned ports, no owned runtime processes, absent display, and removed owned temporary TMUX paths. Manual Electron cleanup has separate final receipts. Final Docker cleanup removed all three task images and exactly three new cache IDs while preserving all 34 preexisting cache IDs; only initial postgres and ryuk images remain. Read-only final cleanup found 22 CLI runs with absent private directories, closed owned ports, 1103 PNGs and 712 JSON files readable and 0 errors. Public artifacts exclude keys, session URLs, raw private traces, prompts and unnecessary runtime identifiers.

No next baseline is justified while required branches remain blocked. No maintenance PR link exists; human-only validation and the attribution/template requirement remain unresolved. No HUMAN statement is filled or readiness asserted. No merge, recurring schedule or environment-template publication is part of this run. The coverage attempt report is complete with a blocked/partial verdict; publication is gated by the exact repository requirements below. [Model-backed scope](model-backed-coverage.json) distinguishes credential availability, actual successful request model IDs and behavior evidence; private references are explicitly marked.

Latest not-run semantic reconciliation reviewed all 126 unchanged check labels: 105 historical generic placeholders and 21 scope-matched replacements. No constructible unfinished check remains in that set. Historical #17436 requires unavailable reporter-private comparison artifacts; non-object Finish requires a producer unsupported by the installed object-only Tool schema, and both have explicit current blocked entries. This does not make every recorded ID a complete branch pass.


## Final provenance, inventory and retention

The four source checkouts were confirmed as the enyst forks of Canvas (`playground`), software-agent-sdk (`agent-sdk`), extensions (`oh-extensions`) and automation (`automation`), each with default branch `main`. The comparison remains the frozen Canvas target above; maintenance commits do not replace the target product tree. SDK source was `5966c781ed014efc96c028a99bddd4ff78426741`, extensions `d05780951082d4d83f785cb1d4c7f2be6d1c14a5`, automation `bc4cca7c7e2eab5cb7d0ff671bec5dd113d3e2c2`. Installed runtime versions, rather than sibling source assumptions, were used for live claims. Canvas was 1.27.1; Node 24.21.0, Playwright 1.63.0 and Chromium 151.0.7922.173 drove the shell browser harness on Debian 13.

The frozen existing-issue inventory contains 383 non-PR issues. Current dispositions are 291 mapped, 17 historical not-reproduced, and 75 out of scope. These dispositions are not 291 fresh passes. Current live proof for existing #16257 supersedes its historical out-of-scope disposition without erasing the historical evidence. Thirty changed commits were reconciled to thirty PR descriptions, reviews and files plus 27 linked issue bodies; all 122 changed paths were accounted for. Closed/updated query counts were not treated as fixed-behavior counts.

The final root readback at 22:09:09 UTC found no audit-owned runtime processes and 16,437,444,608 free disk bytes. The post-stop evidence manifest hashes 2092 retained regular files totaling 114,513,141 bytes, including 1103 PNGs, 712 JSON files, six MP4s and two GIFs. These are retained-evidence counts, not public-release or test counts. Sanitized private evidence remains protected in the original audit workspace; private run credential state is purged. Public artifacts are a deliberately reviewed subset. No shared data was pruned.

Infrastructure interruptions remain separate from product results. The original shared execution-channel loss interrupted the first turn; surviving services did not complete the audit independently. A later brief executor-link interruption at 21:53:38.855 UTC reconnected at 21:53:45.168 UTC while desktop API reads continued. Neither event establishes a resource cause, host migration or product failure. The serial packaging cancellation, in contrast, has its own measured disk-reserve receipt.

## Maintenance PR preparation and exact remaining inputs

Proposed title: **docs(verify-openhands): reconcile weekly map and prove controller corrections**.

The complete proposed body and publication prerequisite notes accompany this report. No PR has been opened or merged. Publication authorization already exists. The remaining requirements are concrete: the human must supply their own testing note in the untouched HUMAN section; the conflicting literal attribution-first requirement and HUMAN-first validator need resolution; and the linked fork maintenance issue must actually carry ready-for-dev before opening the PR. The label check is mandatory, but the validator does not state that label application is human-only. No readiness label is being added as a side effect of map bookkeeping.

`AGENTS.md:49` says: “The `HUMAN:` section in PR descriptions is reserved for human contributors only. AI agents must not add to, edit, move, or remove it. If validation fails because it is missing or empty, stop and ask the human user to update it in their own words.” The template asks: “Human contributors: add a short note about your testing.” The validator requires the first visible line to be `HUMAN:` and at least 20 visible characters of human prose before `AGENT:`. Environment onboarding instead requires every public post to begin `I am an AI agent helping Engel Nyst (@enyst) with project work.` Neither hiding attribution nor inventing human prose is an honest resolution.
