# OpenHands Git Hooks

This directory contains git hooks that are automatically installed in the OpenHands runtime environment.

## prepare-commit-msg

This hook serves as a fallback mechanism to ensure that OpenHands contributions are properly attributed. It automatically adds `Co-authored-by: openhands <openhands@all-hands.dev>` to commit messages when the co-authorship line is not already present (case-insensitive check).

### Behavior

- **Primary workflow**: The OpenHands agent should manually add co-authorship lines to commit messages as instructed in the system prompt
- **Fallback**: If the agent forgets to add the co-authorship line, this hook will automatically add it
- **No-op**: If the co-authorship line is already present (in any case variation), the hook does nothing

### Installation

#### Docker Runtime

The hook is automatically installed during Docker runtime build via the `Dockerfile.j2` template:

1. Copied from `/openhands/code/openhands/runtime/utils/git_hooks/` to `/openhands/git-hooks/hooks/`
2. Made executable with `chmod +x`
3. Configured globally via `git config --global core.hooksPath /openhands/git-hooks/hooks`
4. Set as template for new repositories via `git config --global init.templateDir /openhands/git-hooks`

This ensures the hook works for both existing repositories and newly created ones.

#### CLI Runtime

For CLI runtime, git co-authorship is always enabled automatically. A git wrapper script is set up that intercepts git commit commands and automatically adds co-authorship. This approach is non-invasive as it doesn't modify the user's git configuration or install hooks in their repositories. Instead, it transparently wraps git commands to add the co-authorship line when needed.
