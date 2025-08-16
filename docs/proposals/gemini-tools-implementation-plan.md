# Gemini-optimized tools for OpenHands (Implementation Plan)

This document captures the concrete plan we will execute now. After implementation, we will run a targeted evaluation (e.g., SWE-bench) using Gemini with its own toolset. If Gemini+tools outperforms the current setup, we will open PRs for review and merge.

## Objectives

- Provide Gemini-specific tools in OpenHands whose names, parameter schemas, and behavior mirror google-gemini/gemini-cli.
- When the selected model is Gemini, disable the legacy `str_replace_editor` tool and expose only the Gemini tools.
- Keep all changes safe-by-default using the ACI runtime, with a dedicated Gemini editor module for filesystem operations.

## Phase 1 Scope: Full file-operation tool parity with Gemini CLI

Implement the following Gemini CLI counterparts first (all filesystem-oriented):
- replace
- read_file
- write_file
- list_directory
- glob
- search_file_content
- read_many_files

The intent is to cover everything that overlaps with OpenHands’ `str_replace_editor` capabilities (and more), so Gemini models never need that legacy tool.

## Design Principles

- Exact signatures and naming: tools should have the same names, parameter JSON schemas, and descriptive guidance as in Gemini CLI. This ensures we “speak” the tool dialect Gemini already knows best.
- Replace `str_replace_editor` for Gemini: the CodeActAgent must not present `str_replace_editor` when Gemini is the model; it must expose only the Gemini tools.
- Dedicated Gemini runtime implementation: create a new Gemini Editor in `openhands-aci` (separate from the Anthropic-style `OHEditor`). The new editor exposes method-per-tool (no “command”-style interface at the tool level).

## Architecture Overview

### Agent (OpenHands)

- New Gemini tool definitions under `openhands/agenthub/codeact_agent/tools/gemini/`, one file per tool:
  - `create_gemini_replace_tool()`
  - `create_gemini_read_file_tool()`
  - `create_gemini_write_file_tool()`
  - `create_gemini_list_directory_tool()`
  - `create_gemini_glob_tool()`
  - `create_gemini_search_file_content_tool()`
  - `create_gemini_read_many_files_tool()`
- Tool JSON schemas and descriptions are copied/adapted from Gemini CLI (keeping to its simple, Gemini-compatible formats). Where Gemini CLI references a “rootDirectory,” we will map to OpenHands’ workspace root.
- Model gating in `CodeActAgent._get_tools()`:
  - If `llm.config.model` indicates a Gemini model, register the Gemini tools above and omit `str_replace_editor`.
  - Otherwise, preserve current behavior.
- Function-call mapping (`function_calling.py`):
  - Add explicit handlers for each Gemini tool name, mapping them into a new, dedicated action type (see below) with strongly typed arguments.

### Actions and Runtime Wiring (OpenHands)

- Prefer reusing existing OpenHands Actions where possible (FileReadAction, FileWriteAction, FileEditAction with impl_source=OH_ACI). Only if truly necessary for parameter carriage or routing clarity, introduce minimal new Actions in a later stage after proving we cannot reuse existing ones.
- In `ActionExecutionServer`, route Gemini-file operations through the existing paths wherever feasible (e.g., FileReadAction for read_file, FileWriteAction for write_file, FileEditAction with command='replace' for replace). When adding non-edit operations (list_directory, glob, search_file_content, read_many_files), attempt to use existing read/write/edit pathways first; if they are insufficient, we will add narrow, internal-only Actions later.

### Runtime (openhands-aci)

- Add `GeminiEditor` in `openhands_aci/editor/gemini_editor.py` (inherits from a minimal shared base or composes existing helpers from `OHEditor`).
- Implement methods:
  - `replace(file_path, old_string, new_string, expected_replacements?)`
    - If `old_string == ''` and file doesn’t exist: create with `new_string`.
    - If `old_string == ''` and file exists: error (attempt to create existing file).
    - Normalize CRLF→LF for matching.
    - Replace all occurrences; if `expected_replacements` is provided, enforce exact match.
    - Error when 0 matches; error when `old_string == new_string` (no-op).
    - Return snippet/diff-like context similar to current ACI outputs.
  - `read_file(path, offset?, limit?)`
    - For text: return content slice; indicate truncation if needed.
    - For images/PDFs (when explicitly targeted): return base64-encoded data (aligning with Gemini CLI behavior).
  - `write_file(file_path, content)`
    - Create parent dirs as necessary; overwrite if exists; return confirmation.
  - `list_directory(path, ignore?, respect_git_ignore?=true)`
    - Return immediate children (dirs first, alphabetical). Apply glob ignores. Honor `.gitignore` when requested (best-effort using a simple gitignore parser; fall back gracefully if parsing isn’t possible).
  - `glob(pattern, path?, case_sensitive?=false, respect_git_ignore?=true)`
    - Return absolute paths matching pattern, newest-first (by mtime). Exclude nuisance dirs like `.git` and `node_modules` by default.
  - `search_file_content(pattern, path?, include?)`
    - Use `git grep` if inside a repo; otherwise Python regex over files filtered by `include`. Return matches with file path and line numbers.
  - `read_many_files(paths, include?, exclude?, recursive?=true, useDefaultExcludes?=true, respect_git_ignore?=true)`
    - Concatenate text files with `--- {absolutePath} ---` separators.
    - For images/PDF/audio/video explicitly requested: return base64 data items.
    - Skip obviously binary files unless explicitly requested by extension.
- Security and constraints:
  - Enforce OpenHands workspace boundaries (absolute paths under the workspace root).
  - Apply size limits and truncation policies comparable to current ACI behavior for consistency.

## What We Are NOT Doing (Phase 1)

- No multi-stage LLM “edit correction” loop inside ACI for `replace`. We will initially rely on the model to provide exact literals after `read_file`. If needed, we can add an optional correction layer in Phase 2.
- No interactive confirmation UI in runtime. We’ll return clear messages/snippets; UI can display diffs using existing mechanisms.
- No overloading of `str_replace_editor` or its “command” interface. The Gemini toolset is independent and method-per-tool on the runtime side.

## Testing Plan

- OpenHands
  - Unit tests for tool registration/gating (Gemini-only exposure of the new tools; `str_replace_editor` disabled for Gemini).
  - Function-call conversion tests for each Gemini tool → `GeminiToolAction` with correct arguments.
- openhands-aci
  - Unit tests for each `GeminiEditor` method:
    - `replace`: new-file creation via `old_string==''`, single/multi replacement, mismatch on `expected_replacements`, zero matches, and no-op (old==new).
    - `read_file`: offset/limit slicing, and base64 for explicitly requested images/PDFs.
    - `write_file`: overwrite vs create.
    - `list_directory`: ignore patterns, `.gitignore` honors (best-effort), sorting.
    - `glob`: pattern matching, newest-first ordering.
    - `search_file_content`: `git grep` fast-path vs fallback.
    - `read_many_files`: concatenation, excludes, explicit binary handling.
- End-to-end
  - Small scenario: `read_file` → `replace` on a temporary file; verify results and diffs.

## Evaluation Plan

- Run SWE-bench (or comparable benchmark) with Gemini + Gemini tools.
- Compare against baseline Gemini + `str_replace_editor` (current default stack) and against non-Gemini models, tracking success rates and regressions.
- If Gemini+tools outperforms baseline without regressions, proceed with PRs (OpenHands + openhands-aci).

## Rollout Plan

1) Implement Phase 1 across both repos (tools, runtime, tests) behind Gemini model gating.
2) Run evaluation and analyze results.
3) Open PRs; address feedback; merge on positive outcome.

## File-level Checklist (initial PRs)

OpenHands:
- Add Gemini tool definitions:
  - `openhands/agenthub/codeact_agent/tools/gemini/replace.py`
  - `openhands/agenthub/codeact_agent/tools/gemini/read_file.py`
  - `openhands/agenthub/codeact_agent/tools/gemini/write_file.py`
  - `openhands/agenthub/codeact_agent/tools/gemini/list_directory.py`
  - `openhands/agenthub/codeact_agent/tools/gemini/glob.py`
  - `openhands/agenthub/codeact_agent/tools/gemini/search_file_content.py`
  - `openhands/agenthub/codeact_agent/tools/gemini/read_many_files.py`
- Gating in `codeact_agent.py` to swap toolsets for Gemini.
- Update `function_calling.py` to produce `GeminiToolAction` for each tool.
- Add unit tests for mapping and gating.

openhands-aci:
- Add `openhands_aci/editor/gemini_editor.py` with methods listed above.
- Add a dispatcher in the ACI runtime to execute `GeminiToolAction` by calling the corresponding `GeminiEditor` method.
- Unit tests per method as outlined.

Notes:
- Commit co-author trailer to use: `Co-authored-by: OpenHands-GPT-5 openhands@all-hands.dev`.
- Ensure schema trimming for Gemini (removing unsupported JSON Schema formats) continues to apply via `llm_utils.check_tools`.

## Mapping to existing OpenHands Actions (pragmatic reuse)

To minimize churn and keep the model-level tool API clean while reusing proven runtime pathways:
- read_file → FileReadAction (impl_source=OH_ACI). Map offset/limit → view_range.
- write_file → FileWriteAction (direct file write path).
- replace → FileEditAction (impl_source=OH_ACI) with command='replace' and parameters old_str/new_str/expected_replacements routed to GeminiEditor.replace().
- For list_directory, glob, search_file_content, read_many_files: introduce lightweight dedicated Actions (e.g., DirectoryListAction, GlobAction, SearchFileContentAction, ReadManyFilesAction) so we can pass tool-specific parameters (ignore, include, respect_git_ignore, etc.) without overloading FileReadAction. These remain internal plumbing; the LLM still sees Gemini-CLI-compatible tool names and schemas.

This approach keeps the external tool surface identical to Gemini CLI while leveraging OpenHands’ existing Action types wherever they naturally fit.

## Clarifications and routing details (pre-implementation)

- No extra HTTP parameters: Editor selection is derived from FileEditAction.command. We will route 'replace' to GeminiEditor and keep legacy commands ('str_replace', 'create', 'insert', 'undo_edit', 'view') on OHEditor.
- read_file must NOT use impl_source=OH_ACI: The OH_ACI view path adds line numbers. For Gemini read_file we will use the default FileReadAction path (non-OH_ACI) so the model receives raw file contents. Mapping: offset → start, end → offset + limit (or -1 when limit is not provided). Binary handling remains as in current runtime (images/PDFs → data URLs).
- write_file uses FileWriteAction with full-file overwrite-or-create semantics. We will not expose start/end to Gemini; the tool schema remains exactly as in Gemini-CLI (file_path, content).
- Replace parameters: Add expected_replacements (optional int) to FileEditAction and wire it through ActionExecutionServer._execute_file_editor to GeminiEditor.replace(). Behavior: replace all occurrences of old_string; enforce expected_replacements when provided; CRLF→LF normalization; create new file when old_string == '' and file does not exist; error when no-op or mismatch.
- Path policy: Tools require absolute paths within the workspace. We will keep prompts/descriptions aligned with Gemini-CLI (absolute paths) and enforce workspace boundaries in the runtime. Relative paths will still resolve under the current working directory but the model will be instructed to supply absolute paths per CLI guidance.

## Phased execution order

- Phase 1a (initial PR scope):
  - Implement replace (GeminiEditor.replace + server routing + FileEditAction expected_replacements support).
  - Implement read_file (tool def + default FileReadAction mapping) and write_file (tool def + FileWriteAction mapping).
  - Gate tools in CodeActAgent for Gemini and disable str_replace_editor for Gemini.
- Phase 1b:
  - Implement list_directory, glob, search_file_content, read_many_files with Gemini-CLI-compatible schemas. Attempt to reuse existing runtime paths; add minimal internal wiring only if necessary.
- Phase 2 (optional):
  - Add confirmation/diff previews and content-correction loops similar to Gemini-CLI for write_file/replace if desired.

## Tool schema source of truth

- We will mirror tool names, parameter names, and descriptions from google-gemini/gemini-cli (packages/core/src/tools/*.ts and docs/tools/file-system.md). Any deviations will be documented inline in the tool definitions.
