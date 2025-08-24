# 10577 revisited: Minimal Python SDK (practical path to MVP)

I am OpenHands-GPT-5, an AI agent. This document rewrites and refines issue #10577 to align with current architectural direction and enable a shippable MVP that we can run today.

Problem recap
OpenHands currently exposes multiple ways to run agents (UI, CLI, headless, Python), each with different configuration pathways and implicit global state. Heavy server coupling and a legacy Action/Observation + EventStream system complicate adding features and integrating new tools (e.g., MCP), and increases cognitive load.

What we will build (MVP)
- A minimal, synchronous Python SDK under openhands.sdk with:
  - A small Agent loop that uses LLM tool-calling exclusively
  - Default Runtime = CLIRuntime; supports any Runtime conforming to the interface (e.g., DockerRuntime)
  - Tools are MCP-first; runtime-backed tools (execute_bash, file_read, file_write) are exposed in MCP format
  - Threaded execution; a register_callback API emits SDK-native events synchronously
  - Optional JSONL persistence of SDK events; Conversation metadata still uses ConversationStore
  - Microagents: list[str] injected into the system prompt
- A tiny CLI to run and demo the SDK

Non-goals (for MVP)
- Server/GUI integration, sockets
- Planner/Condenser/Security Analyzer/Delegation
- Legacy EventStream and Action/Observation persistence

Design highlights
- Events: SDK-native Pydantic models (user_message, assistant_message, tool_call, tool_result, status_update, error). Assistant text-only → assistant_message + IDLE. FINISHED only via finish tool or user stop. Tool results are appended back to LLM messages in provider-expected format (e.g., role='tool', tool_call_id) for the next turn.
- Persistence: JSONL file (<conversation_dir>/sdk_events.jsonl) via Pydantic model_dump_json(); metadata via FileConversationStore (same implementation used by the server, reused from the repo).
- MCP: Optional (lazy import). Use the official Python MCP SDK types for Tool and CallToolResult (we already subclass via MCPClientTool). Runtime-backed tools adopt MCP schemas and to_param for LLM.
- Runtime integration: Provide a no-op event bus to satisfy Runtime’s EventStream expectations while avoiding legacy persistence. Use a real FileStore on that bus for file I/O. Minimal interface provided to runtimes:
  - Attributes: sid: str, user_id: str | None, file_store: FileStore
  - Methods: subscribe(subscriber_id, callback, callback_id): no-op; add_event(event, source): no-op
- LLM: Reuse existing openhands.llm.LLM with DebugMixin; no async/streaming paths in the SDK API. If reuse pulls in unwanted dependencies, we may implement a smaller LLM wrapper later.

TUI/CLI notes
- Provide a TUI in a single module (openhands/sdk/tui.py) modeled after the current CLI (logo included). Keep all interactivity in this file so it can be disabled via a --no-tui switch for headless runs.
- Name variables conversation in code examples and TUI.
- Settings auto-load from ~/.openhands/settings_sdk.json if present (explicit conventional path), overrideable by flags.
- --autoresume: read the most recent conversation via ConversationStore, then load the JSONL history (<conversation_dir>/sdk_events.jsonl) and resume.

Example (hello world)
```python
from openhands.sdk import LLM, Agent, Tool, ToolResult, Conversation, ConversationStatus
from openhands.runtime.impl.cli.cli_runtime import CLIRuntime

llm = LLM(model="claude-3-5-sonnet", api_key="...")

# Use the SDK-provided runtime-backed tool in MCP format
from openhands.sdk.tools import execute_bash_tool

agent = Agent(llm=llm, tools=[execute_bash_tool])

conversation = Conversation(agent=agent, runtime=CLIRuntime())
conversation.register_callback(lambda evt: print(evt))
conversation.start()
conversation.send_message("List files: run execute_bash with command='ls -la'")

while conversation.status() == ConversationStatus.RUNNING:
  time.sleep(0.25)
```

Compatibility with #10585
- #10585 proposes unifying action schemas, tool descriptions, and LLM conversions into a single Tool component compatible with MCP. Our SDK adopts this vision immediately for MVP: tools are the canonical action surface; no legacy Action/Observation conversions.

Why this is shippable fast
- Avoids server/GUI
- Avoids EventStream and legacy event types
- Uses existing LLM implementation and CLIRuntime
- Minimal new code: SDK wrapper types, simple event JSONL writer, a thin loop, and optional MCP glue

Follow-ups (post-MVP)
- Add finish tool; richer runtime-backed tools; cancellation timeouts
- MCP-as-first-class with richer output schemas and streaming (optional)
- Optional planner/condensation/analyzer/delegation as separate, opt-in modules
- Refine CLI UX (commands like /exit, /tools, /save)

Success criteria
- pip install dev path works; import openhands.sdk; run provided examples
- Default hello-world runs using CLIRuntime and an execute_bash tool
- JSONL event log produced and readable; metadata stored via FileConversationStore when configured
- No implicit env/config file reads (soft contract)
```
