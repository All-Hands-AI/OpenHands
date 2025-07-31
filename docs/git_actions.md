# Git Actions in OpenHands

This document describes the git commit and push actions that provide better control over git operations in OpenHands, along with the standardized Git behavior across different interfaces.

## Overview

Previously, agents would use `CmdRunAction` to execute git commands like `git commit` and `git push`. This approach had limitations:

- Combined operations made it difficult to control when code was committed vs pushed
- Less granular error handling
- Harder to debug git-related issues
- Limited workflow flexibility

The new git actions separate these operations into distinct tools:

- `GitCommitAction`: Handles local git commits only
- `GitPushAction`: Handles pushing to remote repositories

## GitCommitAction

Commits changes to the local git repository.

### Parameters

- `commit_message` (str): The commit message
- `files` (list[str] | None): Specific files to commit. If None, commits all staged files
- `add_all` (bool): If True, stages all changes before committing (equivalent to `git add -A`)
- `thought` (str): Optional thought/reasoning for the action

### Example Usage

```python
from openhands.events.action.git import GitCommitAction

# Commit all staged files
action = GitCommitAction(
    commit_message="Fix bug in user authentication"
)

# Commit specific files
action = GitCommitAction(
    commit_message="Update documentation",
    files=["README.md", "docs/api.md"]
)

# Stage all changes and commit
action = GitCommitAction(
    commit_message="Complete feature implementation",
    add_all=True
)
```

### Response

Returns a `GitCommitObservation` with:
- `content`: Output from the git commit command
- `commit_hash`: Hash of the created commit
- `files_committed`: List of files that were committed
- `success`: Boolean indicating if the commit was successful
- `error`: Boolean indicating if there was an error

## GitPushAction

Pushes commits to a remote git repository.

### Parameters

- `remote` (str): Remote name to push to (default: "origin")
- `branch` (str | None): Branch to push. If None, pushes current branch
- `force` (bool): If True, performs a force push (default: False)
- `set_upstream` (bool): If True, sets upstream tracking (default: False)
- `thought` (str): Optional thought/reasoning for the action

### Example Usage

```python
from openhands.events.action.git import GitPushAction

# Push to origin/main
action = GitPushAction(
    remote="origin",
    branch="main"
)

# Push current branch and set upstream
action = GitPushAction(
    set_upstream=True
)

# Force push to a specific branch
action = GitPushAction(
    remote="origin",
    branch="feature-branch",
    force=True
)
```

### Response

Returns a `GitPushObservation` with:
- `content`: Output from the git push command
- `remote`: The remote that was pushed to
- `branch`: The branch that was pushed
- `success`: Boolean indicating if the push was successful
- `error`: Boolean indicating if there was an error

## Benefits

### Better Control
Agents can commit work locally without immediately pushing to remote, allowing for:
- Multiple commits before pushing
- Local testing and validation
- Better commit history management

### Reduced Conflicts
Prevents automatic pushing that may conflict with other work or require authentication.

### User Intent
Users have better control over when their work is shared remotely.

### Debugging
Easier to debug and review changes before they are pushed to remote repositories.

### Workflow Flexibility
Supports different git workflows and branching strategies:
- Feature branch workflows
- Git flow
- GitHub flow
- Custom workflows

## Error Handling

Both actions provide detailed error information:

- **Commit errors**: No staged changes, permission issues, invalid repository
- **Push errors**: Authentication failures, network issues, rejected pushes, conflicts

Errors are returned as `ErrorObservation` objects with descriptive messages.

## Migration from CmdRunAction

### Before
```python
# Old approach - combined operation
action = CmdRunAction(command='git add . && git commit -m "Fix bug" && git push origin main')
```

### After
```python
# New approach - separate operations
commit_action = GitCommitAction(
    commit_message="Fix bug",
    add_all=True
)

push_action = GitPushAction(
    remote="origin",
    branch="main"
)
```

This separation allows for better error handling, more granular control, and improved workflow flexibility.

## Standardized Git Behavior Across Interfaces

OpenHands now provides consistent Git behavior across different interfaces through a standardized configuration system. The behavior is automatically configured based on how the conversation was initiated.

### Interface-Specific Behaviors

#### GUI Mode
- **Behavior**: Conservative approach - never push or create PRs unless explicitly requested
- **Rationale**: Users have full control and can see what's happening in the interface
- **Configuration**: `auto_push: false`, `auto_pr: false`

#### GitHub Resolver
- **Behavior**: Automatic push to the same branch when work is complete
- **Rationale**: Used for automated issue resolution where the expectation is that work will be committed
- **Configuration**: `auto_push: true`, `auto_pr: false`
- **Note**: Respects repository permissions and branch protection rules

#### Slack Integration
- **Behavior**: Always ask for user confirmation before creating PRs
- **Rationale**: Users may not have immediate visibility into changes and should have explicit control
- **Configuration**: `auto_push: false`, `auto_pr: "ask_user"`

#### CLI Mode
- **Behavior**: Conservative approach similar to GUI mode
- **Rationale**: Command-line users typically want explicit control over Git operations
- **Configuration**: `auto_push: false`, `auto_pr: false`

### How It Works

The Git behavior configuration is automatically set when a conversation is initialized based on the trigger type. This information is passed to the agent through the workspace context, providing clear guidelines on when to commit, push, and create pull requests.

The agent receives these guidelines in its prompt and follows them consistently, eliminating the previous unpredictable behavior where Git operations varied depending on the interface being used.

### Benefits

1. **Predictable Behavior**: Users know what to expect from Git operations regardless of the interface
2. **Interface-Appropriate Actions**: Each interface gets behavior that matches user expectations
3. **Centralized Configuration**: All Git behavior logic is managed in one place
4. **Clear Guidelines**: Agents receive explicit instructions about when to perform Git operations