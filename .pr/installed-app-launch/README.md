# Issue #17891: section titles and installed-app launch preferences

The existing `useAppTitle` hook now derives Home, Conversations, Automations, and Settings titles from existing translations and router paths. Conversation/panel titles, status emojis, rename refreshes, and loading fallbacks keep their existing path. No new document-title writer, persistence, backend contract, or dependency is introduced. Embedded exports do not mount the standalone root layout.

The manifest requests `navigate-existing`, declares `handle_links: preferred`, and adds New conversation, Conversations, and Automations shortcuts. Their URLs and icons resolve relative to the manifest under both `/` and `/canvas/`. Both conversation shortcuts target the existing `/conversations` home/composer; `/` can redirect to a user-pinned page. Static manifest shortcut names are English; in-app section titles use the user's language.

## Verification

- Base: `852132d38dbc15e03d6825bbacbeb971c72575be`; feature branch `feat/installed-app-launch-titles`.
- macOS arm64; Node 24.15.0; locked dependencies installed with `npm ci --ignore-scripts`.
- A real isolated Local stack was launched through `control-openhands launch --new --min-free-mb 0`; Agent Server 1.55.1 and automation 1.20.1. The macOS free-page heuristic initially rejected launch despite reclaimable memory; the explicit override was used for one stack.
- Onboarding was skipped in this disposable profile, analytics disabled, and no LLM API key or model call was used. This feature does not require model execution.
- The title and manifest regressions failed before implementation (11 failures, 12 passes). The final focused run passed 22 tests; the first post-change run passed 23 before one redundant nested-route case was removed.
- `npm run lint`, `npm run build`, and `npm run build:lib` passed. Lint reported 619 warnings and zero errors. The full-suite result and environment-specific failures are recorded below.

## Real browser observations

`control-openhands doctor` passed its health checks. Using the sidebar, Settings → Automations → New Chat produced `Settings | OpenHands`, `Automations | OpenHands`, and `Conversations | OpenHands`. The identical `performance.timeOrigin` in [readbacks.json](readbacks.json) proves those transitions did not reload the document. Visiting `/` produced `Home | OpenHands`. At 390×844, the New Chat route retained `Conversations | OpenHands`.

[Navigation recording](section-navigation.webm) and [Settings](settings.png), [Automations](automations.png), [New Chat](conversations.png), and [phone](phone-conversations.png) captures show the real app context. The recorder captures page content, not the browser's title bar; the readbacks contain the actual document titles. These are browser-tab checks, not installed-app verification.

The first launch was interrupted by a production rebuild replacing lazy-loaded assets, producing stale-chunk 404s. Reloading onto the final build resolved them. Repeating the sidebar transitions with a cleared error log yielded zero page errors, console/HTTP app errors, or warnings, as recorded in the readbacks.

## Remaining installed-app verification

This checkout does not link `site.webmanifest` and its installable app name is empty. The separate PWA foundation is issue #17890 / PR #17895 and remains outside #17891's scope. The served manifest returned HTTP 200 with the requested launch fields and shortcuts, but OS installation, shortcut-menu activation, and existing-window reuse were not verified. Browser support and the user's link-capturing preference control whether launch declarations are honored; merely declaring `handle_links` does not prove capture.

After the foundation lands, install Canvas in a supporting Chromium browser. Open it once, launch an in-scope link again, and confirm that the same window navigates. Exercise all three OS shortcuts and repeat under `--base-path /canvas`. Record the installed window, title changes, and OS shortcut menu before marking the PR ready for review.

## Reproduce the verified path

```sh
control-openhands launch --new
control-openhands doctor --run <run-dir>
control-openhands onboard --skip --run <run-dir>
control-openhands browser goto /settings/llm --run <run-dir>
control-openhands browser eval 'document.title' --run <run-dir>
control-openhands browser click 'testid=sidebar-automations-link' --expect-url '/automations$' --run <run-dir>
control-openhands browser eval 'document.title' --run <run-dir>
control-openhands browser click 'testid=sidebar-conversations-link' --expect-url '/conversations$' --run <run-dir>
control-openhands browser eval 'document.title' --run <run-dir>
control-openhands stop --run <run-dir>
```

The verify-openhands skill and feature map were used read-only.

## Environment and scope notes

- Browser: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36`.
- `map affected` maps `use-app-title.ts` to F01; `public/site.webmanifest` has no owning feature-map entry. This coverage gap is reported here; verification-skill files were not changed.
- Verification teardown stopped the browser and launcher, and confirmed the ingress, Agent Server, automation, static frontend, and editor ports closed. Captures were copied and inspected before teardown.
- In-app language switching and conversation rename/status behavior have automated coverage using the real hooks, router, i18next resources, query cache, and status store; only the conversation service is mocked. They were not exercised with a paid model in the live run.

## Unrelated timezone-sensitive test

The full suite encountered `__tests__/components/automations/detail/run-phase.test.tsx`, test `negative: returns null for timestamps the formatter would print as garbage`. The test expects `/1970/` for `1970-01-01T00:00:00Z`, but the shared formatter displays `31 déc. 1969` in America/Los_Angeles. The isolated file reproduces that failure (31 passed, 1 failed) and passes under `TZ=UTC` (32 passed). The test, `run-phase.tsx`, and `format-relative-time.ts` are byte-for-byte identical to the base commit; their Git blob hashes match. They were left unchanged.

## Full-suite result

`npm test -- --maxWorkers=2` completed in 373.90 seconds: **840 test files passed, 3 failed; 9,150 tests passed, 4 failed, 7 todo**. In addition to the timezone assertion above:

- `docker-runtime-packages.test.ts` invokes the system Python 3.9, which cannot import `datetime.UTC` from the unchanged Debian-snapshot updater. Rechecking this file and the timezone-sensitive file under Python 3.12 and `TZ=UTC` passes all 35 tests.
- Both `docker-session-key-policy.test.ts` cases fail under the system Bash 3.2: expanding the existing empty `STATIC_SERVER_SESSION_KEY_ARGS` array with `set -u` exits 127 (`unbound variable`). A direct execution of the same unchanged block reproduces this. The Dockerfile, entrypoint, test files, and updater have matching base/worktree Git blob hashes.

These environment failures were not fixed in this feature PR. Lint, both production builds, translation completeness, and all 22 focused title/manifest checks pass.

Local and Cloud conversations, OpenHands and ACP agents, and standard/planning/delegated conversations all supply the same existing `AppConversation` title/status fields to the unchanged conversation-title branch. The new route-section branch is standalone-only; embedded library exports and the separate shared-conversation route do not mount this root layout. No compatibility floor change is needed.
