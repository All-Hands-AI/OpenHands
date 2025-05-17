# GitLab Installation

This guide walks you through the process of installing and configuring OpenHands Cloud for your GitLab repositories.

## Prerequisites

- A GitLab account
- Access to OpenHands Cloud

## Installation Steps

1. Log in to [OpenHands Cloud](https://app.all-hands.dev)
2. If you haven't connected your GitLab account yet:
   - Click on `Connect to GitLab`
   - Review and accept the terms of service
   - Authorize the OpenHands AI application

## Adding Repository Access

You can grant OpenHands access to specific repositories:

1. Click on the `Select a GitLab project` dropdown, then select `Add more repositories...`
2. Select your organization and choose the specific repositories to grant OpenHands access to.
   - OpenHands requests permissions with these scopes:
     - api: Full API access
     - read_user: Read user information
     - read_repository: Read repository information
     - write_repository: Write to repository
   - Repository access for a user is granted based on:
     - Permission granted for the repository
     - User's GitLab permissions (owner/maintainer/developer)
3. Click `Install & Authorize`

## Modifying Repository Access

You can modify repository access at any time:
* Using the same `Select a GitLab project > Add more repositories` workflow, or
* By visiting the Settings page and selecting `Configure GitLab Repositories` in the `GitLab Settings` section.

## Using OpenHands with GitLab

Once you've granted repository access, you can use OpenHands with your GitLab repositories in several ways:

### With Issues

Label an issue with `openhands` and OpenHands will:
1. Comment on the issue to let you know it's working on it
2. Open a merge request if it determines that the issue has been successfully resolved
3. Comment on the issue with a summary of the performed tasks and a link to the merge request

### With Merge Requests

Use `@openhands` in comments to:
- Ask questions
- Request updates
- Get code explanations

## Next Steps

- [Access the OpenHands Cloud UI](./cloud-ui.md) to interact with the web interface
- [Use the OpenHands Cloud API](./cloud-api.md) to programmatically interact with OpenHands
