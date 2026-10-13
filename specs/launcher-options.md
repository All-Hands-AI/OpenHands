# Launcher options and runtime descriptions

## LAR-001 - Explicit LAN key opt-in

The npm launcher, static development launcher and Vite frontend honor
`--allow-lan-session-key`. The option permits injection of the session key on
a non-loopback bind. Without it, a non-loopback bind serves key-free HTML and
opens the API-key entry path. Public mode remains key-free with the option.

## LAR-002 - Expected occupied-port errors

An occupied required port stops startup with exit code 1 and one diagnostic,
without a stack trace. The diagnostic names the occupied services and explains
that ingress can use `--port <other>` or `PORT=<other>`. Unexpected failures
retain their stack traces.

## LAR-003 - Accurate backend-only metadata

In backend-only mode, runtime services omit the frontend and the ingress
description does not claim that `/*` routes to it. Full-stack mode continues to
advertise the frontend route. These descriptions also feed the agent's runtime
service context.
