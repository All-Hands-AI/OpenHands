# OpenHands Gitlab Issue Resolver 🙌

Need help resolving a Gitlab issue but don't have the time to do it yourself? Let an AI agent help you out!

This tool allows you to use open-source AI agents based on [OpenHands](https://gitlab.com/all-hands-ai/openhands)
to attempt to resolve GitLab issues automatically. While it can handle multiple issues, it's primarily designed
to help you resolve one issue at a time with high quality.

Getting started is simple - just follow the instructions below.

## Manual Installation

If you prefer to run the resolver programmatically instead of using GitLab Actions, follow these steps:

1. Install the package:

```bash
pip install openhands-ai
```

2. Create a GitLab access token:
   - Visit [GitLab's token settings](https://gitlab.com/-/user_settings/personal_access_tokens)
   - Create a fine-grained token with these scopes:
     - 'api'
     - 'read_api'
     - 'read_user'
     - 'read_repository'
     - 'write_repository'
   - If you don't have push access to the target repo, you can fork it first

3. Create an API key for the [Claude API](https://www.anthropic.com/api) (recommended) or another supported LLM service

4. Set up environment variables:

```bash

# GitLab credentials

export GITLAB_TOKEN="your-gitlab-token"
export GIT_USERNAME="your-gitlab-username"  # Optional, defaults to token owner

# LLM configuration

export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"  # Recommended
export LLM_API_KEY="your-llm-api-key"
export LLM_BASE_URL="your-api-url"  # Optional, for API proxies
```

Note: OpenHands works best with powerful models like Anthropic's Claude or OpenAI's GPT-4. While other models are supported, they may not perform as well for complex issue resolution.

## Resolving Issues

The resolver can automatically attempt to fix a single issue in your repository using the following command:

```bash
python -m openhands.resolver.resolve_issue --repo [OWNER_OR_GROUP]/[REPO] --issue-number [NUMBER]
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
python -m openhands.resolver.resolve_all_issues --repo [OWNER_OR_GROUP]/[REPO] --issue-numbers [NUMBERS]
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

This functionality is available both through the GitLab Actions workflow and when running the resolver locally.

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
python -m openhands.resolver.send_pull_request --issue-number ISSUE_NUMBER --username YOUR_GITLAB_USERNAME --pr-type draft
```

If you want to upload to a fork, you can do so by specifying the `fork-owner`:

```bash
python -m openhands.resolver.send_pull_request --issue-number ISSUE_NUMBER --username YOUR_GITLAB_USERNAME --pr-type draft --fork-owner YOUR_GITLAB_USERNAME
```

## Providing Custom Instructions

You can customize how the AI agent approaches issue resolution by adding a `.openhands_instructions` file to the root of your repository. If present, this file's contents will be injected into the prompt for openhands edits.

## Troubleshooting

If you have any issues, please open an issue on this gitlab repo, we're happy to help!
Alternatively, you can [email us](mailto:contact@all-hands.dev) or join the OpenHands Slack workspace (see [the README](/README.md) for an invite link).
