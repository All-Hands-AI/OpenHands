# MCP Apps: initial Canvas integration

This increment adds a frontend integration seam and a self-contained HTML host.
Agent Server 1.54.0 does not expose the resource/tool proxy required for production
MCP Apps. The default Canvas has no adapter and continues to render ordinary tool
text. No new Agent Server endpoint, wire requirement, or version floor is added.

| ID      | Behavior                                                                                                                                                                                                                                                                                                                 |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| MCA-001 | An MCP observation with separately owned frontend presentation data can declare a UI through tool-definition metadata. Missing/invalid sidecar data retains the existing text renderer; unpublished App-shaped event fields are ignored. The complete result remains available to the View.                              |
| MCA-002 | App results remain outside collapsed tool groups and initially expand their cards. Their original text remains visible while loading, unavailable, or failed.                                                                                                                                                            |
| MCA-003 | A configured adapter reads resources and an official AppBridge handles initialization and data delivery. A separate-origin proxy embeds self-contained HTML in an opaque-origin iframe. Both Host and proxy validate message sources. External resources and additional permissions are not supported in this increment. |
| MCA-004 | Sessions bind to the originating backend, generation, conversation, and tool call. Shared views override injected hosts. Write callbacks recheck the current writable owner; mode switches never retarget a View. Abort, retry, and unmount dispose old work.                                                            |

## Frontend integration data

Canonical Agent Server events are never extended. A trusted embedding adapter or
fixture owns a separate `MCPAppArtifacts` map keyed by the originating event ID:

```ts
const artifacts: MCPAppArtifacts = new Map([
  [event.id, { tool: { name, _meta }, toolInput, toolResult }],
]);
<MCPAppHostProvider host={host} scope={scope} artifacts={artifacts}>
  {conversation}
</MCPAppHostProvider>
```

`tool._meta.ui.resourceUri` is the standard entry; the deprecated
`tool._meta["ui/resourceUri"]` is accepted only without a nested declaration.
The normalized descriptor and private metadata stay separate from LLM-ready
observation content, event history, and transcript export. Provider defaults and
nested shared-view providers have empty sidecars. Replace the map when artifacts
change so grouping and rendering can react to data arrival or removal. The
normalizer ignores unpublished App-shaped fields on canonical events. A future
adapter must consume released SDK/client contracts and populate this view model.

`MCPAppHostProvider` owns the explicit Host, conversation scope, and sidecar. The Host
opens a session from the originating event binding and resolves the authorized
Server itself. `readResource` is required; tool, context, and message callbacks
are optional. Capability declarations match these callbacks. Adapters own
authorization, tool visibility, audit, and next-turn context consumption. They
must use published typed APIs when real Agent Server support becomes available.
Never place credentials or runtime URLs in the sandbox initialization payload.
The prototype starts a valid artifact without a consent prompt. Conversation
scope checks prevent retargeting but are not user authorization: a production
Host must gate tool calls, messages, and context updates with visibility,
confirmation, audit, and rate-limit policy before enabling those callbacks.

The initial host does not enable ACP Apps: ACP events currently lack equivalent
provenance and resource routing. It does not infer UI resources from ordinary
text, `raw_output`, or arbitrary metadata supplied by an iframe.

## Sandbox deployment

Run `node scripts/mcp-app-sandbox.mjs --parent-origin http://127.0.0.1:3101`.
The default bind is loopback port 3102. Configure the Host's `sandboxUrl` as
`http://127.0.0.1:3102/sandbox.html`. The sandbox must remain a separate,
credential-free origin; serving this file under the Canvas origin is rejected.
For remote/HTTPS hosting, use a dedicated HTTPS origin and retain the response
headers enforced by the script. This is not automatically started by the
production Canvas launcher.

The script serves only the fixed proxy page for the configured parent origin.
It enforces CSP, frame-ancestors, no-store, no-referrer, and disabled permissions.
The inner App runs with `allow-scripts` and no same-origin permission. HTML is
parsed in an inert document and receives an additional restrictive CSP before
being assigned to srcdoc. The proxy forwards App messages only from that
iframe's window and opaque origin; the Host verifies the proxy's fixed origin.

## Local prototype review

Run `npm run demo:mcp-apps` and open
`http://127.0.0.1:3101/src/fixtures/mcp-apps/`. The fixture uses the real
conversation renderer and protocol bridge with an in-memory Host adapter. It
shows the original MCP text, a complete result (including View-only `_meta`),
tool/context/message callbacks, origin filtering, and write revocation after a
conversation-mode change. It does not connect to an Agent Server or an LLM.

Run `npm run test:e2e:mcp-apps` for the dedicated Chromium checks. Set
`MCP_APPS_BROWSER_PATH` when using an installed browser instead of Playwright's
managed Chromium.

## Remaining production work

Implement and publish SDK/Agent Server metadata/provenance preservation,
conversation-bound resource/tool proxies, tool visibility and consent/audit,
next-turn App context, Cloud history persistence, and ACP support. Then provide
a real Host adapter, choose sandbox deployment for each install mode, and update
compatibility only if the released integration requires the new Server contract.
