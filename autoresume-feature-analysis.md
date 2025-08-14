# OpenHands CLI --autoresume Feature Analysis

## Issue Reference
GitHub Issue: https://github.com/All-Hands-AI/OpenHands/issues/9371

## Problem Statement
Users want to automatically resume their most recent OpenHands session without having to remember or specify session names. Currently, users must use `-n sessionname` to resume a specific session, but they often want to just continue where they left off.

## Current `-n` Parameter Behavior

The `-n` parameter allows specifying a session name:
1. OpenHands generates a deterministic session ID based on `session_name + JWT_secret`
2. If a session with that ID exists, it automatically resumes from where it left off
3. If no session exists, it creates a new one with that name
4. Session resumption includes:
   - Restoring agent state and conversation history
   - Handling error states (if last session ended in error)
   - Continuing from the exact point where the session was interrupted

## Proposed `--autoresume` Feature

### Core Functionality
The `--autoresume` flag would:
1. Query the conversation store to find the most recent session
2. Use that session's ID to resume, leveraging the existing resumption mechanism
3. If no previous sessions exist, start a new session normally
4. Provide user feedback about which session is being resumed

### Technical Implementation Plan

#### 1. CLI Argument Addition
- Add `--autoresume` flag to argument parser in `openhands/core/config/utils.py`
- Type: `action='store_true'`
- Help text: "Automatically resume the most recent session"

#### 2. Session Discovery Logic
- Use existing `ConversationStore.search()` method to get recent sessions
- Sessions are already sorted by creation time (most recent first)
- Extract the first (most recent) conversation ID

#### 3. Integration with Existing Flow
- Modify session logic in `openhands/cli/main.py`
- When `--autoresume` is specified:
  - Query conversation store for most recent session
  - Set session name/ID for resumption using existing mechanisms
  - Leverage existing `generate_sid()` and session restoration logic

#### 4. Key Code Locations
- **Argument parsing**: `openhands/core/config/utils.py` (around line 746)
- **Session logic**: `openhands/cli/main.py` (`run_session()` function)
- **Session ID generation**: `openhands/core/setup.py` (`generate_sid()` function)
- **Conversation store**: `openhands/storage/conversation/file_conversation_store.py`

## Design Questions

### 1. Argument Precedence
**Question**: Should `--autoresume` conflict with `-n`?
- **Option A**: Mutually exclusive - error if both specified
- **Option B**: `-n` takes precedence over `--autoresume`
- **Option C**: `--autoresume` takes precedence over `-n`

**Recommendation**: Option A (mutually exclusive) for clarity

### 2. Timestamp Selection
**Question**: Which timestamp should determine "most recent"?
- **Option A**: `created_at` (when session was first created)
- **Option B**: `last_updated_at` (when session was last active)

**Current behavior**: File conversation store sorts by `created_at`
**Recommendation**: Use `last_updated_at` if available, fallback to `created_at`

### 3. User Feedback
**Question**: Should we show which session is being resumed?
**Recommendation**: Yes, display something like:
```
Resuming session: project-work-abc123 (last active: 2 hours ago)
```

### 4. Scope Considerations
**Question**: Should autoresume be scoped by working directory?
- **Option A**: Global - resume most recent session regardless of directory
- **Option B**: Directory-scoped - only resume sessions from current directory
- **Option C**: Configurable behavior

**Recommendation**: Start with Option A (global) for simplicity

### 5. Error Handling
**Question**: How to handle edge cases?
- No previous sessions → Start new session (current behavior)
- Previous session ended in error → Use existing error handling
- Conversation store unavailable → Graceful fallback to new session

## Implementation Complexity
- **Low complexity**: Leverages existing session management infrastructure
- **Main work**: CLI argument parsing and session discovery logic
- **Testing**: Verify interaction with existing `-n` parameter and session resumption

## Benefits
- Improved user experience for common workflow
- Natural extension of existing session management
- Maintains backward compatibility
- Aligns with user expectations from the issue description

## Next Steps
1. Clarify design questions above
2. Implement CLI argument parsing
3. Add session discovery logic
4. Test integration with existing session management
5. Add appropriate user feedback and error handling
