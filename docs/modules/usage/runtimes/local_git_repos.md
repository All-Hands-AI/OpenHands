# Working with Local Git Repositories

When using OpenHands with Docker runtime, you can mount a local directory containing git repositories using the `WORKSPACE_BASE` environment variable. OpenHands will automatically detect and list these repositories in the repositories API endpoint.

## How It Works

1. Set the `WORKSPACE_BASE` environment variable to the path of your local directory containing git repositories.
2. OpenHands will scan this directory and one level deep for git repositories (directories containing a `.git` folder).
3. These repositories will be included in the list of repositories returned by the API endpoint.
4. Local repositories are identified with the `local` provider type, separate from GitHub or GitLab repositories.

## Implementation Details

Local git repositories are handled by a dedicated provider type (`local`) that is automatically added when the `WORKSPACE_BASE` environment variable is set. This provider works alongside other providers like GitHub and GitLab, allowing you to see all your repositories in one place.

## Example

```bash
# Mount your local code directory
export WORKSPACE_BASE=/path/to/your/code

# Run OpenHands with the mounted directory
docker run -p 3000:3000 \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    ghcr.io/all-hands-ai/openhands:latest
```

## Repository Structure

OpenHands will look for git repositories in:
- The root of the `WORKSPACE_BASE` directory
- One level deep in subdirectories

For example, with the following structure:
```
/path/to/your/code/
├── repo1/           # Git repository (contains .git folder)
├── repo2/           # Git repository (contains .git folder)
├── not-a-repo/      # Not a git repository (no .git folder)
└── .git/            # Root directory is also a git repository
```

OpenHands will detect and list:
- `/path/to/your/code` (the root directory itself)
- `/path/to/your/code/repo1`
- `/path/to/your/code/repo2`

## Repository Information

For each local git repository, OpenHands will:
1. Try to extract the repository name and owner from the git remote URL
2. If a remote URL is not available, use the directory name as the repository name
3. Mark the repository as private
4. Include it in the list of repositories returned by the API endpoint

This allows you to work with local git repositories in the same way as GitHub or GitLab repositories in the OpenHands interface.