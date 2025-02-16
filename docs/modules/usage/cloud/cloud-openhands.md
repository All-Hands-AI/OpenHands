# Cloud OpenHands

This document provides information about the hosted version of OpenHands and how it integrates with GitHub for authentication and repository access.

## Authentication and Security

### GitHub App Integration
OpenHands uses a GitHub App for authentication and repository access. This integration provides a secure and controlled way to access your repositories while maintaining the principle of least privilege.

### Security Features
- **Short-Lived Tokens**: For enhanced security, OpenHands uses GitHub's short-lived access tokens that expire after 8 hours.
- **Fine-Grained Permissions**: The GitHub App requests only the specific permissions needed for its functionality. These permissions include:

[TO BE FILLED: List of specific permissions]

## Repository Access

### Adding Repositories
1. You can manage repository access through the "repo dropdown" in the OpenHands interface
2. To add new repositories, select "add more repos" from the dropdown menu
3. You'll be redirected to GitHub to choose which repositories to grant access to

### Access Control
Access to repositories in OpenHands is controlled by two factors:
1. The GitHub App must be installed on the repository
2. You must have appropriate access to the repository on GitHub (either as an owner or collaborator)

This dual-layer access control ensures that:
- You can only access repositories where the GitHub App is installed
- Your access level matches your GitHub permissions
- Repository owners maintain control over who can access their code through OpenHands

## Getting Started
1. Log in using your GitHub account
2. Install the GitHub App on your desired repositories
3. Use the repo dropdown to select which repository you want to work with
4. If you need access to additional repositories, use the "add more repos" option to grant access to more repositories

Remember that you can always manage the GitHub App's access to your repositories through your GitHub account settings.
