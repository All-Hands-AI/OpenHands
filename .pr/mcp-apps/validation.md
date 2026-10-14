# MCP Apps prototype validation

Validated on 2026-10-14. Source: `629caa65be46746c318f46f7bd726cdd4cf2b610`.

## Scope and environment

Windows, Node.js 24+, local Chrome. The browser fixture uses the actual Canvas
renderer, official MCP AppBridge, and two iframe origins. Backend:
**in-memory MCPAppHost fixture**. Model: **none**. This is frontend regression
and prototype evidence; no production Agent Server or live LLM result is claimed.

| Check                                      | Result                                                                                |
| ------------------------------------------ | ------------------------------------------------------------------------------------- |
| Focused Vitest suite                       | 12 files, 115 tests passed                                                            |
| Existing conversation compatibility suites | 5 files, 144 tests passed                                                             |
| Browser integration                        | 3 tests passed                                                                        |
| TypeScript                                 | Passed                                                                                |
| Changed source/test ESLint                 | 24 files passed                                                                       |
| Script syntax checks                       | Passed                                                                                |
| Prettier / git diff --check                | Passed for all 38 source paths                                                        |
| build:app                                  | Passed                                                                                |
| build:lib, including declaration emit      | Passed                                                                                |
| npm pack --dry-run                         | Includes build/mcp-app-sandbox.html and scripts/mcp-app-sandbox.mjs                   |
| Packaged sandbox HTTP/origin test          | Included in the passing focused suite                                                 |
| Interaction recording                      | Completed, 0 browser page errors                                                      |
| 1440px and 390px layouts                   | No horizontal overflow; mobile content height approximately 623.6px in a 624px iframe |

## Focused test command

```sh
npm test -- \
  src/utils/mcp-app-descriptor.test.ts \
  src/components/features/mcp-apps/mcp-app-host-context.test.tsx \
  src/components/features/mcp-apps/mcp-app-artifact.test.tsx \
  __tests__/components/features/mcp-apps/mcp-app-bridge.test.ts \
  __tests__/components/features/chat/tool-visualizers/mcp/mcp.test.tsx \
  __tests__/components/conversation-events/chat/group-events.test.ts \
  __tests__/components/conversation-events/chat/messages-stable-event-props.test.tsx \
  __tests__/routes/shared-conversation-viewer-behavior.test.tsx \
  src/utils/transcript-export/index.test.ts \
  __tests__/scripts/mcp-app-sandbox.test.ts \
  __tests__/package-library.test.ts \
  src/api/no-direct-agent-server-calls.test.ts
```

Observed final Vitest output:

```text
Test Files  12 passed (12)
     Tests  115 passed (115)
```

For local execution, the equivalent direct Node Vitest CLI was used. The
TypeScript-client package emits existing missing-source sourcemap warnings.

## Existing conversation compatibility command

```sh
npm test -- \
  __tests__/components/conversation-events/get-event-content.test.tsx \
  __tests__/components/conversation-events/chat/messages-confirmation.test.tsx \
  __tests__/components/conversation-events/chat/event-message-components/event-group.test.tsx \
  __tests__/components/conversation-events/chat/event-content-helpers/should-render-event.test.ts \
  __tests__/components/features/chat/typing-indicator.test.ts
```

These five files pass 144 existing cases, including the original two-argument
visualizer contract, user rejection presentation, grouping, activity hints, and
secret-request filtering. No existing test assertions were weakened.

## Browser reproduction

```sh
npm run demo:mcp-apps
# Open http://127.0.0.1:3101/src/fixtures/mcp-apps/
```

The recorded interaction initializes the App, delivers the complete ToolResult
and private View metadata, refreshes the mock price, updates text model context,
sends a follow-up message, revokes writes on a mode switch, and restores them
when returning to the originating writable conversation.

The 3 browser tests also check wrong-window rejection and 390px responsive
height reporting. During this validation the demo service was started or reused by a temporary Playwright config; the committed
`playwright.mcp-apps.config.ts` starts an isolated demo service when its ports
are free. An installed Chrome executable was supplied using
`MCP_APPS_BROWSER_PATH`.

- [Desktop screenshot](desktop.png)
- [Mobile screenshot](mobile.png)
- [Actual interaction recording](interaction.webm)

## Draft readiness

No production Host adapter is wired into Canvas. Server provenance/resource/tool
proxies, consent/visibility/audit policy, next-turn context consumption, Cloud
history persistence, ACP support, and live backend/model evidence remain open.
The human-authored PR testing note must be supplied by the contributor, and
issue #16620 does not currently have the required `ready-for-dev` label.

The prototype's successful tests do not establish completion of the issue's
production acceptance criteria. The PR remains a draft.
