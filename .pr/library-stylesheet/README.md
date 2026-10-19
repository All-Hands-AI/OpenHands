I'm an AI agent helping Engel Nyst (@enyst) with project work.

# Library stylesheet: before and after (#18655)

A plain Vite host imports `@openhands/agent-canvas` by package name. It renders
`AgentServerUIProviders` with `analytics: false` and
`styleOverrides: {"--oh-color-base": "#101820"}` around
`div#probe.flex.flex-col.gap-4.p-6.bg-canvas-base.text-foreground.rounded-xl`,
which holds two spans and `button#inside.px-4.py-2.rounded-md.bg-primary.text-on-primary`.
The host `<h1 id="outside">` sits outside the Canvas root.

- `host/host-before.js` (`before.html`): main (79abd32d8). It mounts the
  library as docs/DEVELOPMENT.md described, with no stylesheet import, because
  main exports none.
- `host/host.js` (`index.html`): the fix. It adds
  `import "@openhands/agent-canvas/styles.css";`.

## Commands

```sh
# Canvas checkout (base = origin/main 79abd32d8; fix = this branch)
npm ci --ignore-scripts && npm run build:lib
find dist -name '*.css'        # base: dist/assets/agent-canvas-T4IDBjWs.css (5055 B, xterm only)
                               # fix:  dist/styles.css (443162 B)

# Host: copy host/ to a scratch directory, set the dependency to file:<checkout>.
# Base run serves before.html as index.html.
npm install --ignore-scripts
QA_CANVAS_PACKAGE_DIR=<checkout> npx vite --host 127.0.0.1 --port 5792

# Browser (verify-openhands control-openhands, chromium)
export OH_VERIFY_RUN=$(control-openhands launch --new --print-run)
control-openhands browser viewport desktop          # then 390x844
control-openhands browser goto http://127.0.0.1:5792/ --allow-external
control-openhands browser wait '#inside, #module-error:not(:empty)' --timeout 60000
control-openhands browser eval "$(cat probe.js)"
control-openhands browser screenshot --feature F26.lib-host-app --name after-desktop
control-openhands stop
```

## Measurements (desktop and 390x844 gave the same values)

| | base (main) | fix |
|---|---|---|
| `#probe` display / direction / gap | block / row / normal | flex / column / 16px |
| `#probe` padding | 0px | 24px |
| `#probe` background | rgba(0, 0, 0, 0) | rgb(16, 24, 32) (the `styleOverrides` value) |
| `#probe` radius / color | 0px / rgb(0, 0, 0) | 12px / rgb(238, 242, 247) |
| `#inside` padding / background / radius | 1px 6px / rgb(239, 239, 239) / 0px | 8px 16px / rgb(201, 185, 116) / 6px |
| host `h1#outside` | Times New Roman, 32px, margin 21.44px 0px, rgb(0, 0, 0) | unchanged |
| host `body` background | rgba(0, 0, 0, 0) | unchanged |
| stylesheets in the document | react-hot-toast `_goober` only | `_goober` + `dist/styles.css` |
| module error | none | none |

Other checks on the fix:

- `styleOverrides` drives the color. Removing the inline `--oh-color-base` from
  the scope root changes `#probe` to the built-in rgb(11, 14, 20). Putting it
  back restores rgb(16, 24, 32).
- The library still mounts and reacts. Clicking `#inside` changed its label from
  "Inside Canvas 0" to "Inside Canvas 1".
- Production host build: `npx vite build` in the host bundles the stylesheet
  into `assets/index-<hash>.css` (444 kB), and that file contains
  `[data-agent-server-ui] .flex{display:flex}`. The same probe on the static
  build returned the fix values above.

## Screenshots

- `before-desktop.png`, `before-phone.png`: main. The probe is unstyled inline
  text and the button has the browser's default grey look.
- `after-desktop.png`, `after-phone.png`: the fix. The probe is a padded column
  on the `#101820` override, with a rounded accent button. The host heading
  stays in the browser's default serif.
