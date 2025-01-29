# Environment Variables in OpenHands Runtime

## Overview
Environment variables in OpenHands runtime are used to configure various aspects of the system. Some variables, like `GITHUB_TOKEN`, need to persist across runtime restarts and shell sessions.

## Persistence
To ensure environment variables persist across runtime restarts and shell sessions, they are stored in two locations:

1. **Current Session**: Variables are set in the current shell session using `export VAR=value`
2. **Persistent Storage**: Variables are also stored in `~/.bashrc` to ensure they are reloaded when a new shell session starts

## Important Environment Variables
- `GITHUB_TOKEN`: Used for GitHub API authentication
- Other environment variables as documented in the [OpenHands documentation](https://docs.all-hands.dev)

## Setting Environment Variables
When setting environment variables through OpenHands, they are automatically added to both:
1. The current session via `export`
2. The user's `~/.bashrc` file

This ensures that variables persist even when the runtime restarts or a new shell session begins.

## Manual Configuration
If you need to manually set environment variables to persist across sessions:

1. Add the variable to your `~/.bashrc`:
   ```bash
   echo 'export VARIABLE_NAME="value"' >> ~/.bashrc
   ```

2. Source the updated `.bashrc` file:
   ```bash
   source ~/.bashrc
   ```

## Troubleshooting
If environment variables are not persisting:
1. Check if the variable is properly set in `~/.bashrc`
2. Ensure the variable is being exported (has `export` keyword)
3. Try sourcing `~/.bashrc` manually: `source ~/.bashrc`
