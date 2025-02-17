# Openhands Cloud

This document provides information about the hosted version of OpenHands.

## Getting Started

After visiting OpenHands Cloud, you will be asked to connect with your GitHub account:
1. After reading and accepting the terms of service, click `Connect to GitHub`.
2. Then click `Authorize OpenHands by All Hands AI`.
   - Openhands requests short-lived tokens (8-hour expiry) with these permissions:
     - Actions: Read and write
     - Administration: Read-only
     - Commit statuses: Read and write
     - Contents: Read and write
     - Issues: Read and write
     - Metadata: Read-only
     - Pull requests: Read and write
     - Webhooks: Read and write
     - Workflows: Read and write

## Adding Repositories

You can grant OpenHands specific repository access:
1. Under the `Select a GitHub project` dropdown, select `Add more repositories...`.
2. Select the organization, then choose the specific repositories to grant OpenHands access to.
   - Repository access for a user is granted based on:
     - Granted permission for the repository.
     - User's GitHub permissions (owner/collaborator).

You can manage repository access any time by following the above workflow or visiting the Settings page and selecting
`Configure GitHub Repositories` under the `GitHub Settings` section.
