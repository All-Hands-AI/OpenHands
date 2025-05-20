# Cloud Issue Resolver

The Cloud Issue Resolver automates code fixes and provides intelligent assistance for your repositories on GitHub and GitLab.

## Setup

The Cloud Issue Resolver is available automatically when you grant OpenHands Cloud repository access:
- [GitHub repository access](./github-installation#adding-repository-access)
- [GitLab repository access](./gitlab-installation#adding-repository-access)

## Usage

After granting OpenHands Cloud repository access, you can use the Cloud Issue Resolver on issues and pull/merge requests in your repositories.

### Working with Issues

On your repository, label an issue with `openhands` or add a message starting with
`@openhands`. OpenHands will:
1. Comment on the issue to let you know it is working on it
   - You can click on the link to track the progress on OpenHands Cloud
2. Open a pull request (GitHub) or merge request (GitLab) if it determines that the issue has been successfully resolved
3. Comment on the issue with a summary of the performed tasks and a link to the PR/MR

### Working with Pull/Merge Requests

To get OpenHands to work on pull requests, mention `@openhands` in comments to:
- Ask questions
- Request updates
- Get code explanations

OpenHands will:
1. Comment to let you know it is working on it
2. Perform the requested task
