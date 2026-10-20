# Cloud first message: history cursor (#18717)

Evidence for the fix in `src/hooks/query/use-conversation-history.ts`.

## Before (from the issue, main@1f7b1e69a)

The socket opened with `after_seq=5`, taken from the runtime's event count,
while the history page came from the Cloud App API. The user `MessageEvent` was
runtime seq 3 and was missing from that page, so neither path delivered it. The
bubble stayed "Sending..." below the reply and became "Failed to send" after
150 s:

- https://raw.githubusercontent.com/OpenHands/OpenHands/68d71905b219fdb2795da2c19604e7bf0a832cd3/.pr/bugs/2026-10-20/cloud-first-message-pending/sending-below-reply.png
- https://raw.githubusercontent.com/OpenHands/OpenHands/68d71905b219fdb2795da2c19604e7bf0a832cd3/.pr/bugs/2026-10-20/cloud-first-message-pending/failed-to-send-before-reload.png

## After (this branch, real OpenHands Cloud backend)

Harness: `control-openhands launch --new --print-run --timeout 900` built this
worktree, then `onboard --skip`. The Cloud backend was added with Add Backend →
Cloud → Authorize Device (recipe F25 "Cloud backend"). The first message was
sent from Home:

```sh
control-openhands browser fill 'testid=chat-input' 'Reply with exactly: QA_CLOUD_FIX. Do not run any tools.'
control-openhands browser click 'testid=submit-button' --expect-url '/conversations/'
# at ~30 s, ~90 s and ~165 s:
control-openhands browser eval "<message rows in testid=chat-scroll-container, Sending.../Failed to send flags>"
control-openhands browser events --kinds websocket-created --last 5
```

| Time after send | Message rows (in order) | Sending... | Failed to send | Socket |
| --- | --- | --- | --- | --- |
| 30 s | user-message, pending (sandbox still starting, socket not open yet) | yes | no | none yet |
| 38 s | user-message, agent-message `QA_CLOUD_FIX`, 2 hook rows | no | no | `/sockets/session/<id>?after_seq=-1` |
| 92 s | user-message, agent-message, 2 hook rows | no | no | same, no reconnect |
| 167 s (past the 150 s watchdog) | user-message, agent-message, 2 hook rows | no | no | same, no reconnect |
| after a reload | user-message, agent-message, 2 hook rows | no | no | `after_seq=-1` again |

There was exactly one `user-message` and one `agent-message` at every point,
including after the reload, so the replay added no duplicate rows. The page
shows the same order as before the reload.

Screenshots of the chat panel only. The sidebar is cropped out because it lists
the Cloud account's other conversations.

- `cloud-after-40s.png`: the user message first, then the reply, with nothing pending.
- `cloud-after-165s.png`: the same after the 150 s watchdog, still with no "Failed to send".

### Replay deduplication: event ids are shared between the two logs

For the same conversation, comparing `GET /api/v1/conversation/<id>/events/search`
(App API) with the runtime's `GET <conversation_url>/events/search`:

- App API: 10 events. Runtime: 11 events (`/events/count` = 11).
- 9 event ids are identical in both. Only in the App API:
  1 `ConversationStateUpdateEvent`. Only in the runtime: 2 `HookExecutionEvent`s,
  which the App API page still lacked.

The events that both logs hold have the same id, so the event store's id dedupe
absorbs the replayed overlap. The runtime-only hook rows reach the page through
the replay.

### Local backend unchanged

On the same run (`control-openhands llm preset deepseek`), I started a local
conversation from Home with `Reply with exactly: QA_LOCAL_FIX. Do not run any
tools.`. It showed user-message, then agent-message `QA_LOCAL_FIX`, with no
pending state and no duplicates. The socket still resumes at the count's tail:
`after_seq=3` on the first connect, and `after_seq=6` after a reload with
`/events/count` = 7. Screenshot: `local-after.png`.

### Cloud cleanup

I deleted the Cloud conversation through the UI (`conversation-name >>
ellipsis-button`, `delete-button`, confirm). The App API then returned `[null]`
for its id, and the account's conversation list matched the list from before
the run. I removed the Cloud backend in Manage Backends, and the selector read
`Local` again. I deleted the device grant's API key `Device Link Access Key
(<code of this run>)` with `DELETE /api/keys/<id>` and left every other key in
place.
