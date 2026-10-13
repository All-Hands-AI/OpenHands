# Frozen recovery-gate regression

### Recovery-gate probe regression

On a fresh full-stack run, pass doctor and onboard with skip first. The tracked
`fixture recovery-gate` switches only this run to its real frontend-only launcher
on the same origin. API reject routes return 503 while the stored Local backend
stays in the browser. Run these blocks with `bug run --no-doctor`, because an
absent backend is the deliberate input. Restore with `fixture recovery-gate
--restore` afterward and doctor the full stack again. No requests are intercepted.

```sh known-bug F26.frontend-only-returning desktop
control-openhands browser viewport 1440x900
control-openhands fixture recovery-gate
control-openhands browser record start --feature F26.frontend-only-returning --name desktop --fps 4 --max-seconds 40
control-openhands browser goto /
control-openhands browser wait 'testid=agent-server-onboarding-screen' --timeout 20000
sleep 12
control-openhands browser text 'testid=manage-backends-row-Local'
control-openhands browser screenshot --feature F26.frontend-only-returning --name desktop
control-openhands browser record stop --gif
control-openhands assert --field history.length --equals 0 --bug-shows 2 -- browser toasts --history # bug
```

```sh known-bug F26.frontend-only-returning phone
control-openhands browser viewport 390x844
control-openhands fixture recovery-gate
control-openhands browser record start --feature F26.frontend-only-returning --name phone --fps 4 --max-seconds 40
control-openhands browser goto /
control-openhands browser wait 'testid=agent-server-onboarding-screen' --timeout 20000
sleep 12
control-openhands browser text 'testid=manage-backends-row-Local'
control-openhands browser screenshot --feature F26.frontend-only-returning --name phone
control-openhands browser record stop --gif
control-openhands assert --field history.length --equals 0 --bug-shows 2 -- browser toasts --history # bug
```
