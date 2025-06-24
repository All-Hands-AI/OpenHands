# Task: Add User Directory Support for Microagents

## Problem
Currently, microagents are read from multiple locations but not from a user-specific directory. This leads to the problem of having uncommitted local microagents in the repository, which can be accidentally lost during git operations (as we experienced when `local.md` and `local-gem.md` were lost during a `git add .` and `git reset --hard`).

## Desired Behavior
The microagents system in OpenHands should read microagents from `~/.openhands/microagents/` in addition to its existing sources. This would allow users to:

1. Store personal/local microagents in their user directory (`~/.openhands/microagents/`)
2. Avoid keeping uncommitted microagent files in repository working directories
3. Have persistent personal microagents across all OpenHands projects

## Current Microagent Sources
As of now, microagents are read from multiple locations, but the user directory is not included. We need to implement reading them from the user directory.

## Implementation Requirements
- Add `~/.openhands/microagents/` as a microagent source
- Ensure proper loading order and precedence
- Maintain compatibility with existing microagent sources
- Handle cases where the user directory doesn't exist (create it if possible)

## Best Practices for Users
- **Personal/local microagents**: Add them to `~/.openhands/microagents/` instead of keeping them uncommitted in repository directories
- **Shared microagents**: If microagents are intended to be shared with other users, commit them to the repository's `.openhands/microagents/` directory
- **Never keep microagents uncommitted** in repository working directories to avoid accidental loss during git operations

## Files Affected
- Need to identify where microagent loading logic is implemented
- Likely in the microagents system/loader code
- May need to update configuration or initialization code

## Testing
- Verify microagents are loaded from user directory
- Test precedence/priority of different microagent sources
- Ensure backward compatibility with existing microagent locations
