# Plan: Decoupling File Utilities from Editing Mode

## Problem

The OpenHands CodeAct agent offers three primary ways to handle file edits:
1.  **`str_replace_editor` (Default, OH_ACI):** A comprehensive tool (loaded via `create_str_replace_editor_tool`) with commands for viewing files/dirs, creating, replacing, inserting, and undoing edits. This is the default mode.
2.  **`LLMBasedFileEditTool` (Optional):** An alternative editor tool enabled by `codeact_enable_llm_editor=True`, using line ranges and LLM refinement.
3.  **`LLM_DIFF` Mode (Optional):** An alternative mode enabled by `codeact_enable_llm_diff=True`, where the agent parses Aider-style fenced diffs directly from the LLM's text response (not a tool call).

When either of the optional modes (`LLMBasedFileEditTool` or `LLM_DIFF`) is enabled, the default `str_replace_editor` tool (and its bundled utilities like view, list, undo) is not loaded. This creates a need to provide viewing/listing capabilities separately in these optional modes, while acknowledging that `undo` is inherently tied to the default mode's server-side implementation.

## Goal

Allow the use of the optional editing modes (`LLMBasedFileEditTool` or `LLM_DIFF` mode) while still providing access to the viewing (file/directory) capabilities originally part of the default `str_replace_editor`.

Important: the original `str_replace_editor` tool must remain available *unchanged* when neither alternative editor/mode is enabled, to maintain compatibility with models post-trained on it like Sonnet.

**Challenge:** The `undo_edit` command relies on the internal history of the `OHEditor` instance on the server, which is only populated when *it* performs edits using the `OH_ACI` source. Edits made client-side (`LLMBasedFileEditTool`, `LLM_DIFF` mode) bypass this history, rendering `undo_edit` ineffective for them.

## Current Solution: Conditional Tool Loading

The current implementation addresses the goal of providing viewing/listing utilities by conditionally loading tools based on the agent configuration flags in `openhands/agenthub/codeact_agent/function_calling.py: get_tools`:

1.  **Default Mode (`codeact_enable_llm_editor=False`, `codeact_enable_llm_diff=False`):**
    *   Loads the full `create_str_replace_editor_tool()`. This single tool definition provides commands for editing (`replace`, `insert`, etc.), viewing (`view` file/directory), and `undo_edit`. All operations use `impl_source=OH_ACI` and are executed server-side by `OHEditor`.

2.  **LLM-Based Editor Mode (`codeact_enable_llm_editor=True`):**
    *   Loads the `LLMBasedFileEditTool` for editing (client-side execution).
    *   Loads separate `ViewFileTool` and `ListDirectoryTool`. These tools generate `FileReadAction`s with `impl_source=OH_ACI`, ensuring they are still executed server-side by the `OHEditor`'s viewing capabilities.
    *   Does **not** load `UndoEditTool`.

3.  **LLM_DIFF Mode (`codeact_enable_llm_diff=True`):**
    *   Loads **no** editing tools (edits are parsed from LLM text response and executed client-side).
    *   Loads separate `ViewFileTool` and `ListDirectoryTool` (same as above, executed server-side via `OH_ACI`).
    *   Does **not** load `UndoEditTool`.

This approach successfully decouples the viewing/listing functionality from the chosen editing method by falling back to the `OH_ACI` implementation for viewing/listing even when alternative editing modes are active.

## Conclusion

The current conditional tool loading mechanism effectively provides file/directory viewing capabilities regardless of the selected editing mode (`str_replace_editor`, `LLMBasedFileEditTool`, or `LLM_DIFF`). However, the `undo_edit` functionality remains intrinsically linked to the server-side edit history managed by `OHEditor` and is therefore only available when using the default `str_replace_editor` tool. Edits performed via the client-side `LLMBasedFileEditTool` or `LLM_DIFF` mode cannot be undone using the `undo_edit` command.
