# TMX-001 — Create the local terminal socket directory

Before starting an Agent Server, the npm/full-stack launcher creates the resolved
`TMUX_TMPDIR`. Its default is `<stateDir>/tmux`; an explicit environment override
is preserved and created if needed. Frontend-only mode creates no local terminal
directory. The path used to create the directory and passed to the Agent Server
comes from the same resolved launcher configuration.

tmux socket paths have an operating-system length limit. Long or network-mounted
state directories need a short, socket-capable `TMUX_TMPDIR` override. The current
SDK gives each terminal a unique socket name; other instances' restarts must not
reset the terminal of a running instance.
