# Task List

1. ✅ Draft PRD.md outline and open questions for Minimal Python SDK

2. ✅ Iterate PRD.md to final review-ready version after answers
Updated with: system_message persistence; autoresume selection by last ts; fatal error exit rules; stdout snippet/display requirement; MCP deferred post-MVP; CLI precedence clarified; headless exit codes.
3. 🔄 Translate PRD into implementation tasks and acceptance criteria
Continue implementing autoresume, error-exit, IU display tweaks.
4. 🔄 Create openhands/sdk module (types, tool, llm, persistence, conversation, mcp, __init__)
Added system_message event; runtime.connect on start; function-calling warning; authorship handlers in tools.
5. 🔄 Implement openhands/sdk/tui.py (interactive + --no-tui + --autoresume)
Added CLIRuntime warning; function-calling warning; autoresume invocation; still need stdout snippet display via prompt-toolkit.
6. ✅ Run pre-commit and basic run to validate imports and minimal loop
Syntax check OK; previous ruff/mypy pass for changed files.
7. ✅ LLM function-calling capability warning (non-blocking)

8. 🔄 Autoresume: reconstruct full LLM context from sdk_events.jsonl
Message reconstruction helper added; TUI wired to autoresume_latest(); need assistant tool_calls synthesis if desired.
9. ✅ Connect runtime before using tools (await connect)

10. ⏳ Add unit tests under tests/unit/sdk/test_*.py for MVP
Cover persistence roundtrip, multi tool-calls, autoresume reconstruction, TUI flags, warnings, runtime happy paths, exit-on-error.
11. ✅ Add poetry console_script: openhands-sdk → openhands.sdk.tui:main
