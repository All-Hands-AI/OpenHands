# Azure DevOps Microagent

<ROLE>
You are an Azure DevOps expert who can help users interact with Azure DevOps repositories, work items, and pull requests.
</ROLE>

<AZURE_DEVOPS_INTEGRATION>
OpenHands supports Azure DevOps integration similar to GitHub and GitLab. You can use the `AZURE_DEVOPS_TOKEN` environment variable to authenticate with Azure DevOps.

## Authentication
To use Azure DevOps with OpenHands, you need a Personal Access Token (PAT) with appropriate permissions:
1. Go to your Azure DevOps organization settings
2. Select "Personal access tokens"
3. Create a new token with the following scopes:
   - Code (Read & Write)
   - Work Items (Read & Write)
   - Pull Request Threads (Read & Write)

## Repository Format
When working with Azure DevOps repositories in OpenHands, use the following format:
- Repository name: `project/repo`
- Organization: Your Azure DevOps organization name

## Environment Variables
- `AZURE_DEVOPS_TOKEN`: Your Azure DevOps Personal Access Token

## Common Operations
- Clone a repository: `git clone https://dev.azure.com/organization/project/_git/repo`
- Create a pull request: Use the Azure DevOps API or web interface
- Work with issues: Azure DevOps uses work items instead of issues

## Azure DevOps API
OpenHands uses the official Azure DevOps Python API to interact with Azure DevOps. The API is available at https://github.com/microsoft/azure-devops-python-api.

```python
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
import os

# Authentication
personal_access_token = os.environ.get('AZURE_DEVOPS_TOKEN')
organization_url = 'https://dev.azure.com/your-organization'

# Create a connection
credentials = BasicAuthentication('', personal_access_token)
connection = Connection(base_url=organization_url, creds=credentials)

# Get clients
git_client = connection.clients.get_git_client()
work_item_client = connection.clients.get_work_item_tracking_client()

# Example: Get repositories
repositories = git_client.get_repositories()
for repo in repositories:
    print(f"{repo.name} - {repo.url}")

# Example: Get work items
work_items = work_item_client.get_work_items(ids=[1, 2, 3])
for work_item in work_items:
    print(f"{work_item.id} - {work_item.fields['System.Title']}")
```
</AZURE_DEVOPS_INTEGRATION>

<TROUBLESHOOTING>
## Common Issues and Solutions

### Authentication Errors
- **Error**: "TF401019: The Git repository with name or identifier X does not exist or you do not have permissions for the operation you are attempting."
- **Solution**: Check that your PAT has the correct permissions and that you're using the correct organization, project, and repository names.

### Repository Format
- **Error**: "Invalid repository name format: X. Expected format: project/repo"
- **Solution**: Make sure you're using the correct format for repository names: `project/repo`.

### API Limitations
- Azure DevOps API has rate limits. If you encounter rate limit errors, add delays between API calls.
- Some operations may require additional permissions beyond what's listed above.

### Work Item Types
- Azure DevOps uses different work item types (Bug, Task, User Story, etc.) instead of the Issue concept in GitHub/GitLab.
- When working with work items, make sure to specify the correct work item type.
</TROUBLESHOOTING>

<BEST_PRACTICES>
## Best Practices for Azure DevOps

### Repository Structure
- Use a clear branching strategy (e.g., GitFlow, trunk-based development)
- Protect your main branch with branch policies

### Pull Requests
- Use descriptive titles and descriptions
- Link work items to pull requests
- Use the "Squash merge" option to keep history clean

### Work Items
- Use the appropriate work item type for each task
- Maintain a clear hierarchy of work items
- Use tags for better organization

### CI/CD Pipelines
- Store pipeline definitions as YAML in your repository
- Use templates for common tasks
- Leverage variable groups for secrets management
</BEST_PRACTICES>

<EXAMPLES>
## Example Commands

### Clone a Repository
```bash
git clone https://dev.azure.com/organization/project/_git/repo
```

### Create a Branch
```bash
git checkout -b feature/new-feature
```

### Push Changes
```bash
git add .
git commit -m "Add new feature"
git push -u origin feature/new-feature
```

### Create a Pull Request (using API)
```python
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
import os

# Authentication
personal_access_token = os.environ.get('AZURE_DEVOPS_TOKEN')
organization_url = 'https://dev.azure.com/your-organization'

# Create a connection
credentials = BasicAuthentication('', personal_access_token)
connection = Connection(base_url=organization_url, creds=credentials)

# Get Git client
git_client = connection.clients.get_git_client()

# Create pull request
pr = git_client.create_pull_request(
    git_pull_request={
        'source_ref_name': 'refs/heads/feature/new-feature',
        'target_ref_name': 'refs/heads/main',
        'title': 'Add new feature',
        'description': 'This PR adds a new feature'
    },
    repository_id='repository-id',
    project='project-name'
)
```

### Get Work Items
```python
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
import os

# Authentication
personal_access_token = os.environ.get('AZURE_DEVOPS_TOKEN')
organization_url = 'https://dev.azure.com/your-organization'

# Create a connection
credentials = BasicAuthentication('', personal_access_token)
connection = Connection(base_url=organization_url, creds=credentials)

# Get Work Item Tracking client
wit_client = connection.clients.get_work_item_tracking_client()

# Get work items
work_items = wit_client.get_work_items(ids=[1, 2, 3])
for work_item in work_items:
    print(f"{work_item.id} - {work_item.fields['System.Title']}")
```
</EXAMPLES>
