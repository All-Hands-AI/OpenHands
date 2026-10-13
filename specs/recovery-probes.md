# RGP-001 — Quiet model and version probes

Registered but unreachable backends keep their status and failure detail in the
Manage backends recovery row. Background model-flag hydration and backend-version
probes do not add global error toasts, including their nested query fetches.

When connectivity returns, free/default model flags and the version badge recover
through their normal queries. Genuine Agent Server query errors elsewhere still
use the global toast handler. First-run and API-key screens remain quiet.
