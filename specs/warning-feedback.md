# WN-001 — Readable warning feedback

**Spec ID:** WN-001  
**Status:** Implemented

Small warning text and warning icons use the `feedback-warning` text role, backed by `--oh-feedback-warning`. The built-in role meets 4.5:1 on the theme surfaces used by the Home no-LLM banner, Canvas Apps trust notice, ACP conflict messages, required-secret onboarding warning, and context-usage meter. The meter warning and danger fills also retain 3:1 contrast against the track. Light+ and Solarized Light use darker text shades while retaining the existing brand warning color for controls and tint.

Embedding roots may override the role. The UI follows the nearest `[data-agent-server-ui]` scope. Changing the role does not change warning copy, validation, routing, credential state, or trust controls.

Real browser coverage verifies the Home icon and Apps trust notice follow the host override. The theme contract checks every built-in palette.
