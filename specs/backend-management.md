# Backend Management Specs

---

### BM-001: Auto-switch on connect
- [x] Adding a backend shall automatically switch the active selection to it.

### BM-002: Switching backends keeps the user on the same page
- [x] Switching backends shall redirect to the same section but on the new backend. The user shall never see stale data from the previous backend.

### BM-003: Fallback on active backend removal
- [x] Removing the currently active backend shall fall back to a remaining local backend. The user shall never be left without an active backend.

### BM-004: Theme-aware connection feedback
- [x] Connection errors, disabled-backend diagnostics, and connected/disconnected status text shall use the host-overridable feedback roles in all five themes. Small feedback text shall remain readable on its actual surface, including tinted error panels.

### BM-005: Display the active backend's execution mode
- [x] The Manage backends surface shall show each local backend's execution boundary (local or Docker) next to its version badge.
- [x] The mode shall be read from the agent server's reported runtime field (`conversation_runtime`, or `execution_runtime` when present); no new endpoint or contract is added.
- [x] A single resolver (`getBackendExecutionMode`) shall be the only reader of that field for display, so the badge cannot disagree with itself.
- [x] The workspace the server is asked for during conversation creation shall not be changed by the shipped `conversation_runtime` field: the create path keeps requesting `LocalWorkspace`, which the server normalizes to the isolated workspace it owns.
- [x] When the server omits the field, no mode badge shall render and the row is unchanged.
- [x] Cloud backends expose no `/server_info`, so they render no mode badge even when they share a host and key with a local backend.
- [x] The badge shall refresh when the backend health poll observes new server info, so a server that restarts in a different mode is reflected without reopening the modal.
- [x] The bootstrap cache shall compare and store hosts normalized the same way as the agent-server client options (trailing slashes removed), so a persisted backend host ending in `/` still hits the cache instead of re-probing.
- [x] The mode label shall be localized through `src/i18n/translation.json`.
