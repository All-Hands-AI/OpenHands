# Live consent reversal — 12 October 2026

The pre-fix production Canvas left Automation opted out after the user returned to opt-in. The fixed Canvas persisted the final opt-in choice.

| Version | Frontend source | Final browser choice | Real Automation database |
| --- | --- | --- | --- |
| Before | `9f5eb1e2e709ba18b91bea663397c553ab042c2c` | `granted` | `[false]` |
| After | `a67ec1709627b6ca978ff727b8a2a422c880be0c` | `granted` | `[true]` |

The source links are [before](https://github.com/enyst/playground/blob/9f5eb1e2e709ba18b91bea663397c553ab042c2c/src/hooks/use-sync-automation-telemetry-consent.ts) and [after](https://github.com/enyst/playground/blob/a67ec1709627b6ca978ff727b8a2a422c880be0c/src/hooks/use-sync-automation-telemetry-consent.ts). The verification harness adds run-owned `service pause|resume` controls in the same evidence commit, documented in its help and skill, and tested with actual child processes including an unrelated service that must keep running.

## Production setup

Both versions used separate fresh browser profiles and private homes, real Agent Server/SDK 1.53.0 and the same pinned Automation service. No API responses were mocked. No model or automation execution was needed or started. Doctor passed before each check; its only warning was the unused model without an API key. The prebuilt SPA was served by the real launcher. Both runs used http://127.0.0.1:18800 sequentially.

The default harness build hard-disables telemetry and cannot produce this consent transition. These two builds explicitly enabled the consent store while pointing the supported PostHog host configuration at an unused loopback port with a dummy public project key. This exercises real Canvas consent and real Automation integration; it does not test analytics delivery. The Automation process retained the harness's server-side hard telemetry opt-out. No real analytics host or model provider was used.

Build each checkout with:

```sh
VITE_DO_NOT_TRACK=0 DO_NOT_TRACK=0 \
VITE_POSTHOG_API_KEY=phc_local_review_verification \
VITE_POSTHOG_HOST=http://127.0.0.1:19980 \
VITE_POSTHOG_UI_HOST=http://127.0.0.1:19980 npm run build:app
node --input-type=module -e 'import { buildIdentity } from "./.agents/skills/verify-openhands/scripts/lib/build-id.mjs"; import {writeFileSync} from "node:fs"; writeFileSync("build/verify-revision.txt", buildIdentity(process.cwd()) + "\n")'
control-openhands launch --new --build never --sdk-version 1.53.0
```

The marker was written only after a successful build of that source. The after build was built at `a67ec17096`, saved while the baseline was built, then restored after the baseline was stopped. Doctor verified both served identities. On this Mac, launch's free-memory threshold was lowered deliberately to 256 MB after `memory_pressure` reported 48% available memory; only one stack ran at a time.

## UI recipe

Export the exact run directory printed by launch as `OH_VERIFY_RUN`. Use the same recipe on each build:

```sh
control-openhands doctor
control-openhands onboard --skip
control-openhands browser goto /settings/app
control-openhands browser click 'testid=app-settings-screen >> text=Send anonymous usage data'
control-openhands browser click 'testid=submit-button'
control-openhands browser wait '[data-testid="submit-button"]:disabled'
control-openhands browser network --filter 'telemetry/consent' --bodies
# Confirm initial granted POST is acknowledged before the reversal.
control-openhands browser network --clear --filter 'telemetry/consent'
control-openhands browser record start --feature F16.analytics --name consent-reversal --fps 5
control-openhands service pause automation
control-openhands browser click 'testid=app-settings-screen >> text=Send anonymous usage data'
control-openhands browser click 'testid=submit-button'
control-openhands browser wait '[data-testid="submit-button"]:disabled'
control-openhands browser click 'testid=app-settings-screen >> text=Send anonymous usage data'
control-openhands browser click 'testid=submit-button'
control-openhands browser wait '[data-testid="submit-button"]:disabled'
control-openhands service resume automation
control-openhands browser scroll 'testid=app-settings-screen >> text=Send anonymous usage data'
control-openhands browser network --filter 'telemetry/consent' --bodies
control-openhands browser eval '({consent:localStorage.getItem("openhands-telemetry-consent")})'
control-openhands browser record stop --gif
control-openhands stop
```

Pause sends SIGSTOP only to the run's Automation descendants; Agent Server remains active, so both settings saves complete normally. Resume sends SIGCONT. The reversal takes less than the consent request's five-second timeout. One preliminary run used a mistyped selector and was discarded; the published recordings and results come from the corrected recipe.

## Results and limits

[Before video](before-consent-reversal.mp4) / [GIF](before-consent-reversal.gif) and [after video](after-consent-reversal.mp4) / [GIF](after-consent-reversal.gif) show the real privacy control and settings saves. The backend sync is invisible in the UI; the original network outputs and database reads establish the resulting state.

- Before: the acknowledged initial granted value was suppressed after the intervening denial. The reversal emitted only one consent POST (`false`, HTTP 200). Browser consent remained `granted`; Automation stored `false`.
- After: the reversal emitted denial and granted POSTs, both HTTP 200. Browser consent remained `granted`; Automation stored `true`.
- The database was inspected read-only with SQLite: `SELECT value FROM automation_service_metadata WHERE key='posthog_frontend_consent_by_distinct_id'`. The public outputs retain only the consent booleans; no keys or private state are published.
- Both cleanup results confirm launcher/browser stopped and all five owned ports closed.

This live check proves the return-to-acknowledged-value guard regression. Deliberately processing the older write *after* the new acknowledgement is covered by controlled-promise regression tests in both consent directions; this live run does not claim that separate ordering. Existing startup recovery media remains linked in the PR. Cloud consent and analytics delivery are outside this check.
