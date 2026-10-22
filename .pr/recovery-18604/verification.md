# Live credential recovery verification — PR 18604

Date: 2026-10-21. Real DigitalOcean VM reused; no VM creation, pause, destruction or LLM message was performed.

## Exact sources and topology

- Before: `7b9fbcda38e916fba87c11f1cd9f3bf34f7a5ada`.
- After: `a17cc2a7115540b0ef097a92401d63866bb8fc05`. The recovery form source in the temporary after build is byte-identical to this commit.
- Both copies used the production `npm run build` output, served with `scripts/static-server.mjs --auth-required --disable-telemetry` on isolated `http://127.0.0.1:18640`.
- The real `/mars`, `/api`, `/server_info`, `/health`, `/sockets`, `/alive` and `/ready` routes were proxied to the existing localhost:8000 stack. It was neither restarted nor changed for this check. Its saved DigitalOcean OAuth connection and existing READY session were reused.
- **Shared verification prerequisite:** both temporary copies applied only the frontend bridge-key forwarding source diff from [PR 18465](https://github.com/OpenHands/OpenHands/pull/18465) at head `09336296e70766963ed2f635e5ec9b066ccfaf15`, so typed hosting keys can authenticate real bridge RPCs. Patch SHA-256: `fa18937ecf0b1c8a7595cc7afc936f0d6e9c5d4817a1edbd39e69302fcd5b1ee`. This prerequisite is not part of the recovery implementation commit.
- **Shared topology adjustment:** both temporary copies set the reverse proxy's `changeOrigin` to false, preserving the browser Host so the real bridge's same-origin checks work behind the extra localhost proxy. This is verification infrastructure only, not a product change or mock.
- Browser: repository-pinned Playwright Chromium, 1280×900. No routes or API responses were mocked. Trace recording was disabled. Analytics destinations were blocked.

## Procedure

1. Complete ordinary backend onboarding through the UI with the real hosting Canvas key; skip model setup.
2. In Add Backend → Providers → DigitalOcean, select the existing `openhands-do-test` agent. Its existing `openhands-do-test-9l71qg` session connects and opens its existing conversation. No new conversation is submitted.
3. Save this UI-created browser state privately for equivalent before/after starting states.
4. **Explicit fault injection:** replace only the saved hosting-root key with a known invalid string, clear this isolated context's bridge cookie, and reload. This simulates stale hosting credentials plus an expired bridge cookie. The guest record and active selection remain unchanged. The real guest `/server_info` request returns 401 and the production recovery form appears.
5. Enter a name and the real hosting key in the recovery form. Its actual `GET /api/settings` validation returns 200. Observe reload and inspect the real persisted registry.

## Results

| Assertion | Before | After |
| --- | --- | --- |
| Hosting root receives recovered key | No | Yes |
| Existing guest id/name/host/kind/key/session fields preserved | No | Yes |
| Guest key stays empty | No | Yes |
| Guest remains selected and reaches its real `/server_info` after recovery | No: saved guest host becomes Canvas root | Yes: 200 from the same VM |
| Registry contains original root and guest (2 records) | 2, but guest overwritten | 2, both correct |

Before, the selected guest is renamed “Canvas recovered”, its host becomes the Canvas root and its key becomes the hosting key, while the actual root still has stale credentials. The app displays the local Canvas conversations. After, the hosting root is updated, the original DigitalOcean guest remains unchanged and reconnects to the same session.

The focused unit tests separately cover absent-root creation and cloud-looking Canvas origins; this live run intentionally covers the existing-root recovery flow only.

## Media and privacy

- `before-result.png` / `after-result.png`: actual final browser screens with backend menu open.
- `before-recovery.webm` / `after-recovery.webm`: continuous real-browser recording through stale-key recovery and reload. No simulated UI or stitched outcome frames.
- A fixed black rectangle redacts unrelated sidebar conversation titles in the published images/videos. API-key inputs remain password-masked. There are no account panels, emails, token values, raw request bodies or storage snapshots in the published assets.
- `before-outcome.json` / `after-outcome.json` retain only boolean registry comparisons, guest host/name and response paths/statuses; no credentials.
