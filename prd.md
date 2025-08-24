# PRD: Minimal Python SDK (openhands.sdk)

I am OpenHands-GPT-5, an AI agent. This PRD specifies the Minimal Python SDK for OpenHands (Issue #10577) with MCP-first tooling and a small CLI/TUI. It reconciles prior discussions (see also 10577-revisited.md) and aligns with the tool-centric direction (#10585). The SDK is synchronous, runtime-agnostic, and does not require the server.

Goals (MVP)
- Small, synchronous Python API for running an agent loop using LLM tool-calling
- Runtime-backed tools (default: CLIRuntime); MCP-first tooling compatibility
- Multiple tool calls per assistant turn supported
- Thread-based execution with event callbacks; JSONL persistence of SDK-native events
- No server or legacy EventStream coupling; no implicit global state
- Minimal TUI/CLI in a single module, headless mode via --no-tui, autoresume

Non-goals (MVP)
- Server/GUI/socket integrations
- Planner, condenser, security analyzer, delegation
- Browser tooling by default

High-level architecture
- openhands.sdk (new module)
  - llm.py: Thin wrapper over openhands.llm.LLM (DebugMixin retained). Expose send(messages, tools, tool_choice='auto'). Warn if model does not appear to support function calling; continue anyway.
  - tool.py: SDK Tool definition and runtime-backed tools (execute_bash, file_read, file_write) expressed as MCP-compatible functions (JSON Schema input).
  - types.py: Pydantic types: SDKEvent, ToolResult, ConversationStatus.
  - persistence.py: Append-only JSONL writer/reader for SDK events (<conversation_dir>/sdk_events.jsonl).
  - conversation.py: Conversation loop (threaded), callbacks, message assembly with tool result messages (role='tool', tool_call_id), runtime integration via a minimal no-op event bus.
  - mcp.py (optional): Utilities for building/executing MCP tools from settings (lazy import).
  - tui.py: Single interactive module with --no-tui and --autoresume.

Key decisions
- Default Runtime: CLIRuntime; allow passing any Runtime implementation.
- Tools: MCP-first; runtime-backed tools use MCP-like schemas and LLM tool params. Support multiple tool_calls per turn.
- Events: SDK-native events only; no EventStream persistence. Write JSONL per event for persistence.
- Assistant text-only responses → assistant_message and set status=IDLE. No finish tool; finish via /exit.
- System prompt: exact content from openhands/agenthub/codeact_agent/prompts/system_prompt.j2. Persist a system_message event at loop start containing this text (for reproducibility). Microagents (if provided) may be appended as simple extensions after the base system prompt (no directory parsing/triggers in MVP).
- Settings precedence: CLI flags > env vars (reserved; may add later) > settings file. For MVP we implement CLI > settings file.

Public API (MVP)
- class LLMConfig
  - model: str
  - api_key: str | None
  - base_url: str | None
  - api_version: str | None
  - custom_llm_provider: str | None
  - temperature: float = 0.0
  - reasoning_effort: str | None ('low'|'medium'|'high'|'none')
  - max_output_tokens: int | None
  - top_k: int | None
  - top_p: float | None

- class LLM
  - __init__(config: LLMConfig)
  - send(messages: list[dict], tools: list[dict], tool_choice: str = 'auto') -> ChatResponse
    - Returns provider-like dict with choices[0].message, possibly including tool_calls. Emits a friendly warning if function calling appears unsupported.

- class Tool(BaseModel)
  - name: str; description: str | None; input_schema: dict; output_schema: dict | None; handler: Callable[[dict], ToolResult] | None
  - to_param() -> dict (OpenAI/Anthropic-compatible function param)

- class ToolResult(BaseModel)
  - status: 'ok'|'error'; output: Any | None; error: str | None

- class SDKEvent(BaseModel)
  - type: 'user_message'|'assistant_message'|'tool_call'|'tool_result'|'status_update'|'error'|'system_message'
  - ts: datetime; conversation_id: str; data: dict

- class ConversationStatus(Enum)
  - RUNNING | IDLE | FINISHED | ERROR | CANCELED

- class Agent
  - __init__(llm: LLM, tools: list[Tool], microagents: list[str] | None = None, system_prompt: str | None = None, system_prompt_extensions: list[str] | None = None)

- class Conversation
  - __init__(agent: Agent, runtime: Runtime | None = None, persist_dir: str | None = None, metadata_store: ConversationStore | None = None, conversation_id: str | None = None, user_id: str | None = None)
  - start(), stop(), status()
  - send_message(text: str)
  - register_callback(fn: Callable[[SDKEvent], None])
  - autoresume(conversation_id: str | None = None): Load events from JSONL and reconstruct LLM messages (system/user/assistant/tool) so the session can continue seamlessly.

Runtime integration (no-op bus)
- Pass a minimal bus to Runtime to satisfy its expectations; do not persist legacy events.
  - Attributes: sid, user_id, file_store
  - Methods: subscribe(), add_event() are no-ops

Loop semantics
- On send_message: emit user_message, append to messages
- Iteration: call LLM.send(messages, tools, tool_choice='auto')
  - If response includes tool_calls:
    - For each tool_call in order: emit tool_call, execute handler (runtime-backed or MCP), emit tool_result, then append LLM tool message: { role: 'tool', content: JSON(ToolResult), tool_call_id }
    - After executing all tool calls, immediately continue to the next LLM turn with the appended tool messages
  - Else (no tool_calls): emit assistant_message, set status=IDLE
- ERROR: on unrecoverable exceptions (LLM/tool/runtime), emit error and terminate (exit-on-error)

Persistence
- Metadata: reuse FileConversationStore for ConversationMetadata (title, created_at, user_id, model)
- History: SDK events in <conversation_dir>/sdk_events.jsonl (append-only). Provide read helper for autoresume.

MCP integration (optional)
- Settings structure mirrors MCP protocol: mcp.sse_servers, mcp.shttp_servers, mcp.stdio_servers items with the required fields per protocol.
- If configured, build MCP tools and expose them to the LLM; on invocation, execute via MCP client and map results to ToolResult.
- Lazy import mcp library; if absent but configured, show a clear error.

TUI/CLI
- Single module at openhands/sdk/tui.py
- Flags: --no-tui, --autoresume, --settings (defaults to ~/.openhands/settings_sdk.json), --model, --api-key
- No --persist flag. We always persist to ~/.openhands/conversations for the SDK
- Autoresume: pick most recent conversation by last event timestamp; load sdk_events.jsonl and reconstruct full LLM message state (canonical OpenAI format), including synthesizing assistant tool_calls messages as needed; partial tails are tolerated.
- Behavior: interactive by default; in headless mode, print concise event logs; prompt user for missing model/api_key (similar spirit to the existing CLI TUI but simplified)
- tool_choice='auto' used by default
- Use variable name conversation consistently

Settings file (~/.openhands/settings_sdk.json)
- Minimal required: model, api_key, base_url (optional), temperature, reasoning_effort, mcp: {...}
- Precedence: CLI flags > settings file (env vars reserved for later)

Security notes
- CLIRuntime executes on host; print a clear warning on startup
- No guardrails for MVP

- Exit on fatal error (e.g., LLM auth); print a single-line error in CLI/TUI then exit non-zero in headless mode

Tests and CI
- tests/unit/sdk/test_*.py
  - JSONL persistence round-trip (write/read via Pydantic)
  - Loop behavior: multiple tool_call → tool_result sequencing; assistant_message → IDLE
  - Runtime-backed tools: execute_bash/file ops success/error paths
  - LLM integration: tool result message formatting (role='tool', tool_call_id)
  - TUI flags: --no-tui and --autoresume behaviors
  - Function-calling warning: when not supported, warn but proceed
- Pre-commit and existing CI must pass

Packaging
- Add a poetry console_script entrypoint openhands-sdk -> openhands.sdk.tui:main (not publishing yet)

MVP vs Next
- MVP scope as above
- Next slices:
  - Finish tool and richer status updates
  - Richer TUI panels (tools list, collapsible events, streaming), environment var support
  - MCP tool registry management and UI affordances
  - Timeouts, cancellation, and better error recovery paths


Runtime
- get_tools() → list of MCP-like tools provided by the runtime only (no SDK fallback):
  - Each tool: { name: str, description: str, inputSchema: dict, outputSchema?: dict }
  - Built-in minimal set: execute_bash, file_read, file_write
- execute_tool(name: str, arguments: dict) -> Observation
  - Local dispatch:
    - execute_bash → run(CmdRunAction(command, timeout?))
    - file_read → read(FileReadAction(path, view_range?))
    - file_write → write(FileWriteAction(path, content))
  - Unknown name → ErrorObservation("Unknown tool: <name>")
- call_tool_mcp(MCPAction) remains available for external MCP servers (unchanged)

SDK
- sdk.Tool (MCP-aligned fields)
  - name: str
  - description: Optional[str]
  - inputSchema: dict (JSON Schema)
  - outputSchema: Optional[dict]
  - to_param(): returns OpenAI function param-compatible shape for LiteLLM
- Conversation
  - Do not define fallback tools and do not bind handlers
  - tools = runtime.get_tools() only (MCP format)
  - For LLM: convert each runtime tool to sdk.Tool and then to_param()
  - On tool_call: runtime.execute_tool(name, args) → Observation
    - Map Observation → SDK ToolResult for logs
    - Build provider-agnostic tool_result message; keep Anthropic sequencing fix (assistant tool_calls before tool_result)
- Provider compatibility/diagnostics
  - Keep: enqueue user first; gate LLM on user/tool; exact payload logs; JSONL persistence; exit codes; no duplicate tools
- Optional flag: --tool-choice=required to force tool use on first turn

References
- Issue #10577 (Minimal Python SDK)
- Issue #10585 (Tool-centric, MCP-friendly)
- 10577-revisited.md (this repo)
