# Using the OpenHands GitHub Action

This guide explains how to use the OpenHands GitHub Action, both within the OpenHands repository and in your own projects.

## Using the Action in the OpenHands Repository

To use the OpenHands GitHub Action in a repository, you can:

1. Create an issue in the repository.
2. Add the `fix-me` label to the issue or leave a comment on the issue starting with `@openhands-agent`.

The action will automatically trigger and attempt to resolve the issue.

## Installing the Action in a New Repository

To install the OpenHands GitHub Action in your own repository, follow
the [README for the OpenHands Resolver](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md).

## Usage Tips

### Iterative resolution

1. Create an issue in the repository.
2. Add the `fix-me` label to the issue, or leave a comment starting with `@openhands-agent`.
3. Review the attempt to resolve the issue by checking the pull request.
4. Follow up with feedback through general comments, review comments, or inline thread comments.
5. Add the `fix-me` label to the pull request, or address a specific comment by starting with `@openhands-agent`.

### Label versus Macro

- Label (`fix-me`): Requests OpenHands to address the **entire** issue or pull request.
- Macro (`@openhands-agent`): Requests OpenHands to consider only the issue/pull request description and **the specific comment**.

## Advanced Settings

### Add custom repository settings

You can provide custom directions for OpenHands by following the [README for the resolver](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/resolver/README.md#providing-custom-instructions).

### Custom configurations

Github resolver will automatically check for valid [repository secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions?tool=webui#creating-secrets-for-a-repository) or [repository variables](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#creating-configuration-variables-for-a-repository) to customize its behavior.
The customization options you can set are:

| **Attribute name**               | **Type** | **Purpose**                                                                                                 | **Example**                                          |
|----------------------------------| -------- |-------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| `LLM_MODEL`                      | Variable | Set the LLM to use with OpenHands                                                                           | `LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`   |
| `OPENHANDS_MAX_ITER`             | Variable | Set max limit for agent iterations                                                                          | `OPENHANDS_MAX_ITER=10`                              |
| `OPENHANDS_MACRO`                | Variable | Customize default macro for invoking the resolver                                                           | `OPENHANDS_MACRO=@resolveit`                         |
| `OPENHANDS_BASE_CONTAINER_IMAGE` | Variable | Custom Sandbox ([learn more](https://docs.all-hands.dev/modules/usage/how-to/custom-sandbox-guide))         | `OPENHANDS_BASE_CONTAINER_IMAGE="custom_image"`      |
