# MCP Apps validation

Updated on 2026-10-15. Localization source:
`fe0337abb102f64d0b77bfcd49a31512fe6aa8e8`.

## Scope and environment

Windows, Node.js 24+, installed Google Chrome. The fixture uses the actual
Canvas renderer, official MCP AppBridge, and separate-origin sandbox.
Backend: **in-memory MCPAppHost fixture**. Model: **none**. These are frontend
integration checks; production Agent Server and live-model integration remain
outside this increment.

## Current localization checks

| Check                               | Result                                                                                         |
| ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| Focused Vitest suite                | 6 files, 43 tests passed                                                                       |
| Chrome integration                  | 5 tests passed                                                                                 |
| Translation coverage                | 50 new keys, all 16 supported languages; existing 2,905 keys preserved                         |
| Live locale updates                 | Initialization and later host-context notifications; same session and retained price/tool data |
| Default and fallback                | English by default; explicit query selection; unsupported locale falls back to English         |
| RTL                                 | Arabic document/UI direction; market chart and timeline remain LTR                             |
| Mobile layout                       | All 16 languages checked at 390px; no horizontal overflow in Canvas or the App                 |
| Browser page errors                 | None during layout checks and recorded interactions                                            |
| TypeScript                          | Passed, including library declaration check                                                    |
| Source/test ESLint                  | No errors; existing fixture grid-theme warning remains                                         |
| Translation generation/completeness | Passed                                                                                         |
| Prettier / git diff --check         | Passed                                                                                         |
| build:app / build:lib               | Passed                                                                                         |
| Commit hooks                        | ESLint, formatting, staged typecheck, translation completeness passed                          |

The 43-test suite covers the artifact, protocol bridge, renderer, Host provider,
stable-event conversation rendering, and shared-view isolation:

```sh
npm test -- \
  src/components/features/mcp-apps/mcp-app-artifact.test.tsx \
  __tests__/components/features/mcp-apps/mcp-app-bridge.test.ts \
  __tests__/components/features/chat/tool-visualizers/mcp/mcp.test.tsx \
  src/components/features/mcp-apps/mcp-app-host-context.test.tsx \
  __tests__/components/conversation-events/chat/messages-stable-event-props.test.tsx \
  __tests__/routes/shared-conversation-viewer-behavior.test.tsx
```

Behavioral coverage includes resolved locales, language changes while resources
or the bridge are still initializing, updates after teardown, original-result
preservation, and existing write-scope restrictions. The installed client package
emits existing missing-source sourcemap warnings.

```sh
npm run make-i18n
npm run check-translation-completeness
npm run typecheck
npm run build:app
npm run build:lib
```

## Browser reproduction

```sh
npm run demo:mcp-apps
# Open http://127.0.0.1:3101/src/fixtures/mcp-apps/
npm run test:e2e:mcp-apps
```

Use the Language selector or a URL such as `?lang=ar` or `?lang=zh-CN`.
Set `MCP_APPS_BROWSER_PATH` to an installed Chrome executable if needed.
The dedicated tests block external Google Fonts requests because the fixture
uses system fonts. A temporary Playwright config reused the running fixture
service during the final verification; the committed config starts its own
service when ports 3101/3102 are free.

The five tests cover the original text and complete ToolResult, responsive
height, declared callbacks and revoked writes, wrong-window rejection, live
switching through all 16 languages without a second Host session, initial Arabic,
mobile RTL, and unsupported-language fallback.

The recording starts in English, refreshes the mock price, sends model context
and a follow-up message, revokes/restores write access, then changes through
Chinese, Arabic, and English while retaining the price and original session.

- [English desktop screenshot](desktop.png)
- [English mobile screenshot](mobile.png)
- [Arabic RTL mobile screenshot](rtl-mobile.png)
- [Actual interaction recording](interaction.webm)
- [All 16 mobile layout measurements](locale-layout.json)

## Earlier prototype verification

The initial source `629caa65be46746c318f46f7bd726cdd4cf2b610` passed 12 focused
Vitest files (115 tests), five existing conversation compatibility files
(144 tests), and three browser tests before this localization follow-up.
Its package check confirmed `build/mcp-app-sandbox.html`,
`dist/mcp-app-sandbox.html`, and `scripts/mcp-app-sandbox.mjs` are included.
The packaged sandbox HTTP/origin regression also passed. These earlier totals
are historical results, not additional tests claimed for the current follow-up.

## Draft readiness

The production Host adapter, released resource/tool proxies, consent and audit
policy, next-turn context consumption, Cloud history persistence, ACP support,
and live backend/model evidence remain follow-ups. The human-only PR testing
note must be written by the contributor; issue #16620 still requires the
`ready-for-dev` label. The PR remains a draft.
