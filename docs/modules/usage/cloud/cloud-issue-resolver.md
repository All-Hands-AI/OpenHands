# Cloud Issue Resolver

The Cloud Issue Resolver automates code fixes and provides intelligent assistance for your repositories on GitHub and GitLab.

## Setup

The Cloud Issue Resolver is available automatically when you grant OpenHands Cloud repository access:
- [GitHub repository access](./github-installation#adding-repository-access)
- [GitLab repository access](./gitlab-installation#adding-repository-access)

## Usage

After granting OpenHands Cloud repository access, you can use the Cloud Issue Resolver on issues, pull requests, and merge requests in your repositories.

### GitHub Usage

#### Issues

On your GitHub repository, label an issue with `openhands`. OpenHands will:
1. Comment on the issue to let you know it is working on it.
    - You can click on the link to track the progress on OpenHands Cloud.
2. Open a pull request if it determines that the issue has been successfully resolved.
3. Comment on the issue with a summary of the performed tasks and a link to the pull request.

#### Pull Requests

To get OpenHands to work on pull requests, use `@openhands` in top level or inline comments to:
- Ask questions
- Request updates
- Get code explanations

OpenHands will:
1. Comment on the PR to let you know it is working on it.
2. Perform the task.

### GitLab Usage

#### Issues

On your GitLab repository, label an issue with `openhands`. OpenHands will:
1. Comment on the issue to let you know it is working on it.
    - You can click on the link to track the progress on OpenHands Cloud.
2. Open a merge request if it determines that the issue has been successfully resolved.
3. Comment on the issue with a summary of the performed tasks and a link to the merge request.

#### Merge Requests

To get OpenHands to work on merge requests, use `@openhands` in comments to:
- Ask questions
- Request updates
- Get code explanations

OpenHands will:
1. Comment on the merge request to let you know it is working on it.
2. Perform the task.
