import difflib
import re
from dataclasses import dataclass

from openhands.core.logger import openhands_logger as logger
from openhands.core.exceptions import LLMMalformedActionError

# Regex patterns for search / replace
HEAD = r'^<{5,9} SEARCH\s*$'
DIVIDER = r'^={5,9}\s*$'
UPDATED = r'^>{5,9} REPLACE\s*$'

HEAD_ERR = '<<<<<<< SEARCH'
DIVIDER_ERR = '======='
UPDATED_ERR = '>>>>>>> REPLACE'

DEFAULT_FENCE = ('```', '```')
TRIPLE_BACKTICKS = '```'


@dataclass
class DiffBlock:
    """Represents a parsed SEARCH/REPLACE diff block."""
    filename: str
    search: str
    replace: str


def strip_filename(filename: str, fence: tuple[str, str] = DEFAULT_FENCE) -> str | None:
    """Strips potential wrapping characters from a filename line."""
    filename = filename.strip()

    if filename == '...':
        return None

    start_fence = fence[0]
    if filename.startswith(start_fence) or filename.startswith(TRIPLE_BACKTICKS):
        return None  # Should not start with fence

    filename = filename.rstrip(':')
    filename = filename.lstrip('#')
    filename = filename.strip()
    filename = filename.strip('`')
    filename = filename.strip('*')

    return filename if filename else None


def find_filename(
    lines: list[str],
    fence: tuple[str, str] = DEFAULT_FENCE,
    valid_fnames: list[str] | None = None,
) -> str | None:
    """
    Searches preceding lines for a filename, handling potential fences.
    Adapted from Aider's find_filename.
    """
    if valid_fnames is None:
        valid_fnames = []

    # Go back through the 3 preceding lines (already reversed in caller)
    lines = lines[:3]

    filenames = []
    for line in lines:
        filename = strip_filename(line, fence)
        if filename:
            filenames.append(filename)

        # Stop searching if we hit a non-fence line before finding a filename
        if not filename and not line.startswith(fence[0]) and not line.startswith(TRIPLE_BACKTICKS):
            break
        # Only continue searching past fences if we haven't found a filename yet
        if not filenames and not line.startswith(fence[0]) and not line.startswith(TRIPLE_BACKTICKS):
             break


    if not filenames:
        return None

    # Pick the *best* filename found

    # Check for exact match first
    for fname in filenames:
        if fname in valid_fnames:
            return fname

    # Perform fuzzy matching with valid_fnames
    for fname in filenames:
        close_matches = difflib.get_close_matches(fname, valid_fnames, n=1, cutoff=0.8)
        if len(close_matches) == 1:
            return close_matches[0]

    # If no fuzzy match, look for a file w/extension as a heuristic
    for fname in filenames:
        if '.' in fname:
            return fname

    # Fallback to the last potential filename found
    if filenames:
        return filenames[0]

    return None


def parse_llm_response_for_diffs(
    content: str,
    fence: tuple[str, str] = DEFAULT_FENCE,
    valid_fnames: list[str] | None = None,
) -> list[DiffBlock]:
    """
    Parses LLM response content to find fenced diff blocks.

    Args:
        content: The LLM response string.
        fence: tuple of opening and closing fence markers (e.g., ('```', '```')).
        valid_fnames: Optional list of valid filenames in the context for better matching.

    Returns:
        A list of DiffBlock objects representing the parsed blocks.

    Raises:
        LLMMalformedActionError: If malformed blocks are detected.
    """
    logger.info(f'Parsing LLM response for diffs:\n{content}')

    edits: list[DiffBlock] = []
    lines = content.splitlines(keepends=True)
    i = 0
    current_filename = None

    head_pattern = re.compile(HEAD)
    divider_pattern = re.compile(DIVIDER)
    updated_pattern = re.compile(UPDATED)
    fence_pattern = re.compile(r'^' + re.escape(fence[0]) + r'\w*\s*$') # Pattern for opening fence

    missing_filename_err = (
        'Bad/missing filename. The filename must be alone on the line before the opening fence'
        f' {fence[0]}'
    )

    while i < len(lines):
        line = lines[i]
        line_len = len(line)

        # Check for SEARCH/REPLACE blocks
        if head_pattern.match(line.strip()):
            block_start_line_index = i
            try:
                # Look backwards for filename and opening fence
                fence_line_index = -1
                temp_i = i - 1
                while temp_i >= max(0, i - 4): # Look back up to 3 lines
                    prev_line = lines[temp_i]
                    if fence_pattern.match(prev_line.strip()):
                        fence_line_index = temp_i
                        break
                    temp_i -= 1

                # If fence found, look for filename between fence and head
                filename = None
                if fence_line_index != -1:
                     filename_lines = lines[fence_line_index + 1 : block_start_line_index]
                     # Pass lines in original order for find_filename
                     filename = find_filename(filename_lines, fence, valid_fnames)

                # Fallback / Contextual filename inference
                if not filename:
                    if current_filename:
                        # Use filename from previous block if available
                        filename = current_filename
                    else:
                        # Raise error if no filename found and no fence/context
                        if fence_line_index == -1:
                             raise LLMMalformedActionError(missing_filename_err)
                        else:
                             # If we found a fence but no filename, maybe it's a new file?
                             # Let the parser continue, but filename remains None for now.
                             # It might get inferred later or fail if search block isn't empty.
                             pass # Filename remains None for now

                # If filename is still None after checks, raise error before proceeding
                # unless it's potentially a new file block (empty search)
                # We'll validate the empty search later.
                if filename is None and i + 1 < len(lines) and not divider_pattern.match(lines[i + 1].strip()):
                     raise LLMMalformedActionError(missing_filename_err + " (or fence not found)")

                current_filename = filename # Remember for subsequent blocks

                # --- Start parsing block content ---
                original_text_lines = []
                i += 1 # Move past HEAD line
                while i < len(lines) and not divider_pattern.match(lines[i].strip()):
                    original_text_lines.append(lines[i])
                    i += 1

                if i >= len(lines) or not divider_pattern.match(lines[i].strip()):
                    raise LLMMalformedActionError(f'Expected `{DIVIDER_ERR}` after SEARCH block for {current_filename or "unknown file"}')

                i += 1 # Move past DIVIDER line

                updated_text_lines = []
                while i < len(lines) and not updated_pattern.match(lines[i].strip()):
                    if divider_pattern.match(lines[i].strip()): # Error: unexpected divider
                         raise LLMMalformedActionError(f'Unexpected `{DIVIDER_ERR}` inside REPLACE block for {current_filename or "unknown file"}')
                    updated_text_lines.append(lines[i])
                    i += 1

                if i >= len(lines) or not updated_pattern.match(lines[i].strip()):
                    raise LLMMalformedActionError(f'Expected `{UPDATED_ERR}` after REPLACE block for {current_filename or "unknown file"}')

                i += 1 # Move past REPLACE marker line

                # Check for closing fence (and move past it if found)
                if i < len(lines) and lines[i].strip() == fence[1]:
                    i += 1 # Move past closing fence
                else:
                    # Allow blocks without closing fence for flexibility
                    pass # Stay on the line after REPLACE marker

                # Successfully parsed a block
                original_text = ''.join(original_text_lines)
                updated_text = ''.join(updated_text_lines)

                # Final check for filename if it was initially None (new file case)
                if filename is None:
                    if original_text.strip():
                        raise LLMMalformedActionError("SEARCH block must be empty when creating a new file (filename was missing before block).")
                    # Re-attempt filename finding if it was a new file block
                    if fence_line_index != -1:
                         filename_lines = lines[fence_line_index + 1 : block_start_line_index]
                         filename = find_filename(filename_lines, fence, valid_fnames)
                    if filename is None:
                         # If still None after re-check, it's an error
                         raise LLMMalformedActionError("Could not determine filename for new file block.")

                # Create and add the DiffBlock object
                edits.append(DiffBlock(filename=filename, search=original_text, replace=updated_text))

                continue # Continue to the next line

            except (ValueError, LLMMalformedActionError) as e:
                # Add context to the error message
                processed_marker = len(edits) + 1 # Block number being processed
                # Ensure we get the original message, whether it's ValueError or LLMMalformedActionError
                original_message = e.args[0] if e.args else str(e)
                err_context = f"Error parsing block #{processed_marker} for file '{current_filename or 'unknown'}': {original_message}"
                # Add context to the error message
                processed_marker = len(edits) + 1 # Block number being processed
                # Ensure we get the original message, whether it's ValueError or LLMMalformedActionError
                original_message = e.args[0] if e.args else str(e)
                err_context = f"Error parsing block #{processed_marker} for file '{current_filename or 'unknown'}': {original_message}"
                # Re-raise as LLMMalformedActionError
                raise LLMMalformedActionError(err_context) from e

        # If not a HEAD line, just advance line index
        i += 1

    return edits
