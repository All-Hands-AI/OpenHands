# Docker Desktop Settings for macOS Users

If you get a "Mounts denied" error when running the container, you need to configure Docker Desktop to allow sharing files from the path where your workspace is located.

## Error Example

```
Mounts denied:
The path /app/workspace is not shared from the host and is not known to Docker.
You can configure shared paths from Docker -> Preferences... -> Resources -> File Sharing.
```

## Solution

We've changed the container configuration to use `/tmp/workspace` which should be accessible by default, but if you still have issues:

1. Open Docker Desktop
2. Go to Settings (gear icon) → Resources → File Sharing
3. Add `/tmp` to the list of shared folders if it's not there already
4. Click "Apply & Restart"

## Alternative Approach

If you prefer to use a different workspace directory, you can set the `WORKSPACE_BASE` environment variable when running the container:

```bash
WORKSPACE_BASE=~/my-workspace docker-compose -f tradejoy/containers/docker-compose.yml up
```

Make sure the directory you choose is in the Docker Desktop file sharing list.

## Using VS Code Dev Containers

If you're using VS Code with Dev Containers, you might need to add the workspace path to the devcontainer.json configuration:

```json
"mounts": [
  "source=${localWorkspaceFolder}/workspace,target=/tmp/workspace,type=bind,consistency=cached"
]
``` 