# Using OpenHands with Azure DevOps Pipelines

This guide explains how to use OpenHands with Azure DevOps Pipelines in your own projects.

## Setting Up OpenHands with Azure DevOps

To use OpenHands with Azure DevOps Pipelines, you can:

1. Create a work item in your Azure DevOps project.
2. Add a custom tag like `fix-me` to the work item or leave a comment on the work item starting with `@openhands-agent`.
3. Configure a pipeline to trigger when work items with specific tags are created or updated.

## Installing the Pipeline in a New Repository

To install the OpenHands Azure DevOps Pipeline in your own repository:

1. Create a new pipeline YAML file in your repository (e.g., `.azure/pipelines/openhands.yml`).
2. Configure the pipeline to use the OpenHands resolver.
3. Set up appropriate triggers based on work item events.

Here's a sample pipeline configuration:

```yaml
trigger: none

# Trigger on work item updates with specific tags
resources:
  repositories:
    - repository: OpenHandsResolver
      type: git
      name: OpenHands/resolver

pool:
  vmImage: 'ubuntu-latest'

steps:
- checkout: self
  persistCredentials: true

- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.10'
    addToPath: true

- script: |
    pip install openhands-resolver
    python -m openhands.resolver.azure_devops_resolver
  env:
    AZURE_DEVOPS_TOKEN: $(AZURE_DEVOPS_TOKEN)
    OPENAI_API_KEY: $(OPENAI_API_KEY)
```

## Configuration

You can provide custom directions for OpenHands by following the [README for the resolver](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md#providing-custom-instructions).

The Azure DevOps resolver will automatically check for valid [pipeline variables](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables) or [variable groups](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups) to customize its behavior.

## Usage Tips

### Iterative resolution

1. Create a work item in your Azure DevOps project.
2. Add the `fix-me` tag to the work item, or leave a comment starting with `@openhands-agent`.
3. Review the attempt to resolve the issue by checking the pull request.
4. Follow up with feedback through comments on the work item or pull request.
5. Add the `fix-me` tag to the pull request, or address a specific comment by starting with `@openhands-agent`.

### Custom Instructions

You can provide custom instructions to OpenHands by:

1. Adding a `.openhands/instructions.md` file to your repository.
2. Including specific instructions in your work item description.
3. Setting pipeline variables with custom configuration.

## Security Considerations

When using OpenHands with Azure DevOps Pipelines:

1. Use [pipeline variables](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables#secret-variables) for sensitive information like API keys.
2. Consider using [service connections](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/service-endpoints) for secure authentication.
3. Review the permissions granted to the pipeline to ensure it has appropriate access to your repository and work items.
