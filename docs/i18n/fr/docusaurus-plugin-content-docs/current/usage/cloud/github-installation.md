# GitHub Installation

This guide walks you through the process of installing and configuring OpenHands Cloud for your GitHub repositories.

## Prerequisites

- A GitHub account
- Access to OpenHands Cloud

## Installation Steps

1. Log in to [OpenHands Cloud](https://app.all-hands.dev)
2. If you haven't connected your GitHub account yet:
   - Click on `Connect to GitHub`
   - Review and accept the terms of service
   - Authorize the OpenHands AI application

## Adding Repository Access

You can grant OpenHands access to specific repositories:

1. Click on the `Select a GitHub project` dropdown, then select `Add more repositories...`
2. Select your organization and choose the specific repositories to grant OpenHands access to.
   - OpenHands requests short-lived tokens (8-hour expiration) with these permissions:
     - Actions: Read and write
     - Administration: Read-only
     - Commit statuses: Read and write
     - Contents: Read and write
     - Issues: Read and write
     - Metadata: Read-only
     - Pull requests: Read and write
     - Webhooks: Read and write
     - Workflows: Read and write
   - Repository access for a user is granted based on:
     - Permission granted for the repository
     - User's GitHub permissions (owner/collaborator)
3. Click `Install & Authorize`

## Modifying Repository Access

You can modify repository access at any time:
* Using the same `Select a GitHub project > Add more repositories` workflow, or
* By visiting the Settings page and selecting `Configure GitHub Repositories` in the `GitHub Settings` section.

## Using OpenHands with GitHub

Once you've granted repository access, you can use OpenHands with your GitHub repositories.

For details on how to use OpenHands with GitHub issues and pull requests, see the [Cloud Issue Resolver](./cloud-issue-resolver.md) documentation.

## Next Steps

- [Access the Cloud UI](./cloud-ui.md) to interact with the web interface
- [Use the Cloud Issue Resolver](./cloud-issue-resolver.md) to automate code fixes and get assistance
- [Use the Cloud API](./cloud-api.md) to programmatically interact with OpenHands
