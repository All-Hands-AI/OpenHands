# Azure DevOps Integration

This microagent provides information about working with Azure DevOps repositories, work items, and pull requests in OpenHands.

## Authentication

To authenticate with Azure DevOps, you need to provide a Personal Access Token (PAT) with the appropriate permissions. You can create a PAT in Azure DevOps by following these steps:

1. Sign in to your Azure DevOps organization (https://dev.azure.com/{your-organization})
2. Click on your profile picture in the top right corner
3. Select "Personal access tokens"
4. Click "New Token"
5. Give your token a name and select the appropriate scopes (at minimum: "Code (read)" and "Work Items (read)")
6. Click "Create" and copy the token

You can then use this token with OpenHands by setting the `AZURE_DEVOPS_TOKEN` environment variable or providing it when prompted.

## Repository Format

Azure DevOps repositories are referenced in the format `{project}/{repository}`, where:
- `{project}` is the name of the Azure DevOps project
- `{repository}` is the name of the Git repository within that project

For example: `MyProject/MyRepository`

## Work Items

In Azure DevOps, issues are called "Work Items". They can be of different types, such as "Bug", "Task", "User Story", etc. OpenHands treats all these types as issues.

Work items are referenced by their ID, which is a number. For example: `#123`

## Pull Requests

Azure DevOps uses the term "Pull Request" (PR) similar to GitHub. Pull requests are referenced by their ID, which is a number. For example: `PR #456`

## Azure DevOps REST API

OpenHands uses the official Azure DevOps Python SDK to interact with Azure DevOps. This SDK is a wrapper around the Azure DevOps REST API.

The base URL for the Azure DevOps REST API is: `https://dev.azure.com/{organization}`

## Common Operations

- List repositories: `GET https://dev.azure.com/{organization}/{project}/_apis/git/repositories`
- Get work items: `GET https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{id}`
- List pull requests: `GET https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repositoryId}/pullrequests`

## Limitations

- Azure DevOps API rate limits may apply depending on your organization's settings
- Some operations may require additional permissions beyond the basic read access
