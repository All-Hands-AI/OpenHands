# Gemini-CLI-aligned tools for Gemini models (Phase 1a)

Goal: For Gemini models in OpenHands, expose only: read_file, write_file, replace. Replace is routed to ACI GeminiEditor (with exact Gemini CLI semantics); fallback to OHEditor.str_replace when ACI is missing.

Why: Gemini models perform better with Gemini-CLI style tools – stricter replace semantics (expected count, CRLF preservation, explicit errors), concise surface API.

Scope (Phase 1a)
- Agent gating: Only Gemini models see read_file, write_file, replace.
- Mapper: function_calling maps Gemini replace args: offset/limit -> start/end already removed; use (path, old_string, new_string, expected_replacements?).
- Runtime: action_execution_server routes replace to ACI GeminiEditor; parse CLIResult (path, prev_exist, old_content, new_content) and compute diff for observation. Fallback to OHEditor.str_replace if GeminiEditor is not present in ACI.
- ACI: New GeminiEditor implementing `replace` with Gemini-CLI semantics:
  - Absolute path + workspace boundary enforcement
  - Error if old==new
  - If file missing and old=="": create file with new content
  - If file missing and old!="": error
  - expected_replacements default 1; enforce exact match count; error on 0 or mismatch
  - literal replace with EOL normalization for matching; preserve original EOL style when writing (CRLF/CR/LF)
  - return CLIResult with output or error (for parameter/validation errors)

Tests
- Unit: tests/unit/test_gemini_tools.py (OpenHands) – tool exposure & mapping
- Runtime: tests/runtime/test_gemini_editor_integration.py – verifies routing, prev_exist, content, and diff present.
- ACI unit: tests/unit/editor/test_gemini_editor.py – edge cases for replace semantics, workspace boundaries, CRLF preservation

Next (Phase 1b)
- Add view/list for directories and range reads
- Implement insert and undo_edit with Gemini semantics
- Shell/web/search parity alignment where beneficial
- Consolidate error surface into model-friendly JSON structures where applicable

Notes
- Keep PR self-contained; undraft after CI green across both repos.
- Maintain fallback paths; no behavior change for non-Gemini models.
