# Smallest DigitalOcean VM: verification

Source baseline: OpenHands/OpenHands `8d39305538c1d17a30cbe477e57a0e18fcee7d95`.

- `before.png`: production build with the baseline New Agent component restored. New Agent initially selects **Default (DigitalOcean picks)**.
- `after.png`: production build with the changed component. The real DigitalOcean size catalog initially selects the **1 vCPU / 1 GB** entry.
- `explicit-default.png`: the person can still choose **Default (DigitalOcean picks)** explicitly.
- `phone.png`: the same explicit option is reachable at 390×844 without document overflow.

Both runs used isolated local Canvas stacks, local Agent Server 1.56.0 and `control-openhands`; no request interception, fake bridge, seeded browser state or mock build. DigitalOcean sign-in was used only to read the agent list and size catalog. **Create and launch was never clicked. No config/session was created, resumed or connected. No inference was invoked.** Both verification stacks were stopped and their ports confirmed closed.

Commands: `control-openhands launch --new --build always`, `doctor`, `onboard --skip`, then browser clicks through Add Backend → Providers → DigitalOcean → New Agent. Browser value/screenshot checks confirmed the initial choice and explicit provider-default selection. The first experimental run used an unstamped manual build and failed the doctor's build-stamp check; it was stopped and is not the evidence above. The two recorded builds passed doctor.

Component TDD: 5 failures against the original component (selection and no implicit fallback), then all 8 final component cases pass. The focused component, managed-agents view, manifest-builder and tunnel-bridge suites pass: **52 tests across 4 files**. These cover submitted slugs, explicit provider default, delayed/failed/empty catalogs, and preservation of a choice made before the catalog arrives.

`npm run typecheck`, `npm run lint`, `npm run build`, translation completeness and changed-file ESLint pass. Full lint reports existing warning-level findings (645 warnings, 0 errors). The full repository test suite was not run. The initial shared dependency directory was incompatible with this checkout; a clean `npm ci --ignore-scripts` resolved that before typecheck/build verification. No dependency files were changed.
