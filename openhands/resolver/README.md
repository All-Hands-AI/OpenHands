# OpenHands Github Issue Resolver 🙌

Need help resolving a GitHub issue but don't have the time to do it yourself? Let an AI agent help you out!

This tool allows you to use open-source AI agents based on [OpenHands](https://github.com/all-hands-ai/openhands)
to attempt to resolve GitHub issues automatically. While it can handle multiple issues, it's primarily designed
to help you resolve one issue at a time with high quality.

Getting started is simple - just follow the instructions below.

## Using the GitHub Actions Workflow

This repository includes a GitHub Actions workflow that can automatically attempt to fix individual issues labeled with 'fix-me'.
Follow these steps to use this workflow in your own repository:

1. [Create a personal access token](https://github.com/settings/tokens?type=beta) with read/write scope for "contents", "issues", "pull requests", and "workflows"

   Note: If you're working with an organizational repository, you may need to configure the organization's personal access token policy first. See [Setting a personal access token policy for your organization](https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization) for details.

2. Create an API key for the [Claude API](https://www.anthropic.com/api) (recommended) or another supported LLM service

3. Copy `examples/openhands-resolver.yml` to your repository's `.github/workflows/` directory

4. Configure repository permissions:
    - Go to `Settings -> Actions -> General -> Workflow permissions`
    - Select "Read and write permissions"
    - Enable "Allow Github Actions to create and approve pull requests"

    Note: If the "Read and write permissions" option is greyed out:
    - First check if permissions need to be set at the organization level
    - If still greyed out at the organization level, permissions need to be set in the [Enterprise policy settings](https://docs.github.com/en/enterprise-cloud@latest/admin/enforcing-policies/enforcing-policies-for-your-enterprise/enforcing-policies-for-github-actions-in-your-enterprise#enforcing-a-policy-for-workflow-permissions-in-your-enterprise)

5. Set up [GitHub secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions):
   - Required:
    - `LLM_API_KEY`: Your LLM API key
   - Optional:
     - `PAT_USERNAME`: GitHub username for the personal access token
     - `PAT_TOKEN`: The personal access token
     - `LLM_BASE_URL`: Base URL for LLM API (only if using a proxy)

   Note: You can set these secrets at the organization level to use across multiple repositories.

6. Set up any [custom configurations required](https://docs.all-hands.dev/modules/usage/how-to/github-action#custom-configurations)

7. Usage:
   There are two ways to trigger the OpenHands agent:

   a. Using the 'fix-me' label:
      - Add the 'fix-me' label to any issue you want the AI to resolve
      - The agent will consider all comments in the issue thread when resolving
      - The workflow will:
        1. Attempt to resolve the issue using OpenHands
        2. Create a draft PR if successful, or push a branch if unsuccessful
        3. Comment on the issue with the results
        4. Remove the 'fix-me' label once processed

   b. Using `@openhands-agent` mention:
      - Create a new comment containing `@openhands-agent` in any issue
      - The agent will only consider the comment where it's mentioned
      - The workflow will:
        1. Attempt to resolve the issue based on the specific comment
        2. Create a draft PR if successful, or push a branch if unsuccessful
        3. Comment on the issue with the results

Need help? Feel free to [open an issue](https://github.com/all-hands-ai/openhands/issues) or email us at [contact@all-hands.dev](mailto:contact@all-hands.dev).

## Manual Installation

If you prefer to run the resolver programmatically instead of using GitHub Actions, follow these steps:

1. Install the package:

```bash
pip install openhands-ai
```

2. Create a GitHub access token:
   - Visit [GitHub's token settings](https://github.com/settings/personal-access-tokens/new)
   - Create a fine-grained token with these scopes:
     - "Content"
     - "Pull requests"
     - "Issues"
     - "Workflows"
   - If you don't have push access to the target repo, you can fork it first

3. Set up environment variables:

```bash

# GitHub credentials

export GITHUB_TOKEN="your-github-token"
export GITHUB_USERNAME="your-github-username"  # Optional, defaults to token owner

# LLM configuration

export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"  # Recommended
export LLM_API_KEY="your-llm-api-key"
export LLM_BASE_URL="your-api-url"  # Optional, for API proxies
```

Note: OpenHands works best with powerful models like Anthropic's Claude or OpenAI's GPT-4. While other models are supported, they may not perform as well for complex issue resolution.

## Resolving Issues

The resolver can automatically attempt to fix a single issue in your repository using the following command:

```bash
python -m openhands.resolver.resolve_issue --repo [OWNER]/[REPO] --issue-number [NUMBER]
```

For instance, if you want to resolve issue #100 in this repo, you would run:

```bash
python -m openhands.resolver.resolve_issue --repo all-hands-ai/openhands --issue-number 100
```

The output will be written to the `output/` directory.

If you've installed the package from source using poetry, you can use:

```bash
poetry run python openhands/resolver/resolve_issue.py --repo all-hands-ai/openhands --issue-number 100
```

For resolving multiple issues at once (e.g., in a batch process), you can use the `resolve_all_issues` command:

```bash
python -m openhands.resolver.resolve_all_issues --repo [OWNER]/[REPO] --issue-numbers [NUMBERS]
```

For example:

```bash
python -m openhands.resolver.resolve_all_issues --repo all-hands-ai/openhands --issue-numbers 100,101,102
```

## Responding to PR Comments

The resolver can also respond to comments on pull requests using:

```bash
python -m openhands.resolver.send_pull_request --issue-number PR_NUMBER --issue-type pr
```

This functionality is available both through the GitHub Actions workflow and when running the resolver locally.

## Visualizing successful PRs

To find successful PRs, you can run the following command:

```bash
grep '"success":true' output/output.jsonl | sed 's/.*\("number":[0-9]*\).*/\1/g'
```

Then you can go through and visualize the ones you'd like.

```bash
python -m openhands.resolver.visualize_resolver_output --issue-number ISSUE_NUMBER --vis-method json
```

## Uploading PRs

If you find any PRs that were successful, you can upload them.
There are three ways you can upload:

1. `branch` - upload a branch without creating a PR
2. `draft` - create a draft PR
3. `ready` - create a non-draft PR that's ready for review

```bash
python -m openhands.resolver.send_pull_request --issue-number ISSUE_NUMBER --github-username YOUR_GITHUB_USERNAME --pr-type draft
```

If you want to upload to a fork, you can do so by specifying the `fork-owner`:

```bash
python -m openhands.resolver.send_pull_request --issue-number ISSUE_NUMBER --github-username YOUR_GITHUB_USERNAME --pr-type draft --fork-owner YOUR_GITHUB_USERNAME
```

## Providing Custom Instructions

You can customize how the AI agent approaches issue resolution by adding a `.openhands_instructions` file to the root of your repository. If present, this file's contents will be injected into the prompt for openhands edits.

## Troubleshooting

If you have any issues, please open an issue on this github repo, we're happy to help!
Alternatively, you can [email us](mailto:contact@all-hands.dev) or join the [OpenHands Slack workspace](https://join.slack.com/t/openhands-ai/shared_invite/zt-2wkh4pklz-w~h_DVDtEe9H5kyQlcNxVw) and ask there.
