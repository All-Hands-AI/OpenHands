# Historical reproduction recipes for #17949

These exact recipes produced the paired attempts in this proposal.

### Launcher flag regression recipes

Run these on a fresh `control-openhands launch --new --host 0.0.0.0
--allow-lan-session-key` stack. They observe only whether a disposable key was
injected, never its value. The baseline ignores the flag and opens Add a backend;
the corrected launcher opens the normal agent onboarding step.

```sh known-bug F26.host-bind-lan-optin desktop
control-openhands browser viewport 1440x900
control-openhands browser goto /
control-openhands browser wait 'role=dialog' --timeout 30000
control-openhands browser screenshot --feature F26.host-bind-lan-optin --name desktop
control-openhands assert --field value --equals true --bug-shows false -- browser eval 'Boolean(window.__AGENT_CANVAS_SESSION_API_KEY__)' # bug
```

```sh known-bug F26.host-bind-lan-optin phone
control-openhands browser viewport 390x844
control-openhands browser goto /
control-openhands browser wait 'role=dialog' --timeout 30000
control-openhands browser screenshot --feature F26.host-bind-lan-optin --name phone
control-openhands assert --field value --equals true --bug-shows false -- browser eval 'Boolean(window.__AGENT_CANVAS_SESSION_API_KEY__)' # bug
```

```sh known-bug F26.cli-port-in-use once
control-openhands assert --field messageCount --equals 1 --bug-shows 2 -- launcher busy-port # bug
```

For the metadata block, launch a separate `--backend-only` run.

```sh known-bug F26.backend-only metadata
control-openhands assert --field value --equals 'Unified entry point. Routes /api/automation/* to the automation backend, /api/* and /sockets to the agent-server.' --bug-shows 'Unified entry point. Routes /api/automation/* to the automation backend, /api/* and /sockets to the agent-server, and /* to the frontend.' -- api GET /server_info --pick runtime_services.services.ingress.description # bug
```
