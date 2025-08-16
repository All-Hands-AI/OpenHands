# Phase 1a: Gemini-CLI-aligned tools in OpenHands

Goal: land a minimal, Gemini-optimized tool surface aligned with Gemini-CLI for file operations, and route actions correctly through the runtime (ACI) with safe fallback behavior.

Scope (Phase 1a)
- Expose a Gemini-only tool set to Gemini models in CodeActAgent:
  - read_file(path, offset?, limit?)
  - write_file(file_path, content)
  - replace(file_path, old_string?, new_string, expected_replacements?)
- Map Gemini function-calls to existing OpenHands Actions (FileReadAction, FileWriteAction, FileEditAction) without changing the public OpenHands Action types.
- In the runtime, route FileEditAction(command='replace', impl_source=OH_ACI) to a GeminiEditor if available, otherwise fallback to OHEditor('str_replace').
- Make tests pass and document fallback semantics.

Why
- OpenHands’ default editor tools (str_replace_editor) are optimized for Anthropic’s function-calling and exhibit strict single-occurrence matching by design.
- Gemini-CLI uses simpler, consistent tool names and arguments. Aligning OpenHands tools for Gemini improves instruction-following and reduces schema/tooling friction.

References
- google-gemini/gemini-cli (cloned to /workspace/project/gemini-cli)
- All-Hands-AI/openhands-aci (cloned to /workspace/project/openhands-aci)
- All-Hands-AI/OpenHands (this repo; branch feat/gemini-cli-tools-phase1a)

Implementation summary
1) Tool exposure/gating in CodeActAgent
   - For models containing 'gemini' in the model name, expose only these tools in addition to standard infra tools:
     - read_file, write_file, replace
   - Exclude str_replace_editor for Gemini models.
   - File: openhands/agenthub/codeact_agent/codeact_agent.py

2) Tool definitions (Gemini-CLI-aligned)
   - Files: openhands/agenthub/codeact_agent/tools/gemini/{read_file.py, write_file.py, replace.py}
   - Names come from openhands.llm.tool_names (read_file, write_file, replace)
   - Schemas:
     - read_file(path: string, offset?: int, limit?: int)
     - write_file(file_path: string, content: string)
     - replace(file_path: string, old_string?: string, new_string: string, expected_replacements?: int)

3) Function-calling mapping (response_to_actions)
   - File: openhands/agenthub/codeact_agent/function_calling.py
   - Map Gemini tool calls to OpenHands actions:
     - read_file -> FileReadAction(path, start=end derived from offset/limit)
     - write_file -> FileWriteAction(path=file_path, content)
     - replace -> FileEditAction(path=file_path, command='replace', old_str, new_str, impl_source=OH_ACI, expected_replacements?)
   - Keeps backwards-compatible handling for legacy editors and other built-ins.

4) Runtime routing and fallback (ACI)
   - File: openhands/runtime/action_execution_server.py
   - Try to import openhands_aci.editor.gemini_editor.GeminiEditor.
     - If present: call GeminiEditor(command='replace', path, old_str, new_str, expected_replacements)
     - If absent: fallback to OHEditor(command='str_replace', path, old_str, new_str)
   - Observations are built from ToolResult and compute a file diff for clarity.

5) Tests (Phase 1a)
   - Unit tests validate:
     - Tools exposed for Gemini models exclude str_replace_editor
     - Mapping of read_file/write_file/replace into Actions
   - Runtime test validates:
     - FileEditAction(command='replace', impl_source=OH_ACI) routes and applies changes in the runtime
     - Accept fallback behavior when GeminiEditor is not present in openhands-aci

Behavioral notes and deltas vs Gemini-CLI
- replace semantics
  - Gemini-CLI uses ‘replace’ with parameters {file_path, old_string, new_string, expected_replacements}. From the UI flow, it can support multi-replacement cases and checkpointing.
  - Phase 1a fallback (OHEditor.str_replace) enforces a single, unique occurrence of old_string. If multiple matches are found or no match, it errors. expected_replacements is ignored in fallback.
  - This preserves safety and determinism while we iterate toward a native GeminiEditor in openhands-aci.
- read_file offset/limit
  - Implemented as line-based offsets; both offset and limit must be provided together or neither.
  - Binary media (images, pdf, video) are encoded as data URLs by the runtime’s FileReadAction path.

Follow-ups (Phase 1b+)
- Implement GeminiEditor in openhands-aci to fully align with Gemini-CLI replace semantics:
  - Honor expected_replacements strictly (error if counts differ)
  - Allow creating new files when old_string is empty and file does not exist
  - Consider multi-span replacement if Gemini-CLI requires it (TBD based on upstream code/UI semantics)
- Add write_file and read_file wrappers in ACI only if/when we need permissioning, sandbox, or snapshot behaviors; currently runtime handles these safely.
- Expand tests to cover:
  - expected_replacements paths
  - Non-UTF-8 and large files
  - Multi-tool call sequences (read -> replace -> read)
- Document model-specific tool sets in OpenHands docs, including fallback behavior.

CI/PR checklist
- Install pre-commit hooks (or use -n while CI proves green):
  poetry run pre-commit install -f --hook-type pre-commit
- Push to branch feat/gemini-cli-tools-phase1a and update PR
- For openhands-aci: open a companion PR (even if no code yet) to track GeminiEditor design; or pin a version in OpenHands once GeminiEditor lands

Known constraints
- openhands-aci 0.3.1 does not include gemini_editor; fallback path is expected and tested.
- Some dev containers block creating non-root UIDs in tests; runtime test avoids useradd by using username='root' for the unit test sandbox.

Status
- Code: implemented gating, tool definitions, mapping, runtime fallback
- Tests: unit + runtime (fallback) pass locally
- Next: push + open/refresh PRs, then begin GeminiEditor design in openhands-aci
