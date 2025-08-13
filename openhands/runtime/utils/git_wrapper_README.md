# Git Wrapper for Co-authorship

This git wrapper script (`git_wrapper.sh`) provides a non-invasive way to automatically add co-authorship to git commits without modifying the user's git configuration or installing hooks in their repositories.

## How it works

The wrapper script intercepts git commit commands and:

1. **For `git commit -m "message"` commands**: Extracts the commit message, adds co-authorship, and uses a temporary file to commit with the enhanced message.

2. **For other commit types**: Passes through to the regular git command (interactive commits, file-based commits, etc. would be handled by git hooks in Docker runtime).

## Usage

The wrapper is automatically set up in CLI runtime.

When active:
- The wrapper script is copied to the workspace as `.openhands_git_wrapper.sh`
- Git commands are transparently intercepted and processed
- Co-authorship is automatically added: `Co-authored-by: openhands <openhands@all-hands.dev>`

## Benefits

- **Non-invasive**: Doesn't modify user's git configuration or repository hooks
- **Transparent**: Agent thinks it's running regular git commands
- **Automatic**: No manual intervention required
- **Safe**: Only affects the current workspace session

## Example

```bash
# Without wrapper
git commit -m "Fix bug"
# Results in: "Fix bug"

# With wrapper enabled
git commit -m "Fix bug"
# Results in: "Fix bug\n\nCo-authored-by: openhands <openhands@all-hands.dev>"
```
