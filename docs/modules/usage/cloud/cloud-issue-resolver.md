# Cloud Issue Resolver

The Cloud Issue Resolver automates code fixes and provides intelligent assistance for your repositories on GitHub.

## Setup

The Cloud Issue Resolver is available automatically when you grant OpenHands Cloud repository access:
- [GitHub repository access](./github-installation#adding-repository-access)

![Adding repository access to OpenHands](/img/cloud/add-repo.png)

## Usage

After granting OpenHands Cloud repository access, you can use the Cloud Issue Resolver on issues and pull requests in your repositories.

### Working with Issues

On your repository, label an issue with `openhands` or add a message starting with
`@openhands`. OpenHands will:
1. Comment on the issue to let you know it is working on it
   - You can click on the link to track the progress on OpenHands Cloud
2. Open a pull request if it determines that the issue has been successfully resolved
3. Comment on the issue with a summary of the performed tasks and a link to the PR

![OpenHands issue resolver in action](/img/cloud/issue-resolver.png)

#### Example Commands for Issues

Here are some examples of commands you can use with the issue resolver:

```
@openhands read the issue description and fix it
```

### Working with Pull Requests

To get OpenHands to work on pull requests, mention `@openhands` in comments to:
- Ask questions
- Request updates
- Get code explanations

OpenHands will:
1. Comment to let you know it is working on it
2. Perform the requested task

#### Example Commands for Pull Requests

Here are some examples of commands you can use with pull requests:

```
@openhands reflect the review comments
```

```
@openhands fix the merge conflicts and make sure that CI passes
```
