# OpenHands GitHub & GitLab Issue Resolver 🙌

Need help resolving GitHub or GitLab issues? Let an AI agent help you out!

This tool uses [OpenHands](https://github.com/all-hands-ai/openhands) AI agents to automatically resolve issues in your repositories. It's designed to handle one issue at a time with high quality.

## 1. Setting Up for GitHub (Action Workflow)

### Prerequisites

- [Create a personal access token](https://github.com/settings/tokens?type=beta) with read/write scope for

  - "contents"
  - "issues"
  - "pull requests"
  - "workflows"

- Create an LLM API key (e,g [Claude API](https://www.anthropic.com/api))

### Installation

1. Copy `examples/openhands-resolver.yml` to your repository's `.github/workflows/` directory

2. Configure repository permissions:

   - Go to `Settings -> Actions -> General -> Workflow permissions`
   - Select **Read and write permissions**
   - Enable **Allow Github Actions to create and approve pull requests**

   > If "Read and write permissions" is greyed out:
   >
   > - Check organization settings first
   > - Otherwise, permissions might need to be set in [Enterprise policy settings](https://docs.github.com/en/enterprise-cloud@latest/admin/enforcing-policies/enforcing-policies-for-your-enterprise/enforcing-policies-for-github-actions-in-your-enterprise#enforcing-a-policy-for-workflow-permissions-in-your-enterprise)

3. Set up [GitHub secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions):

   - Required:
     - `LLM_API_KEY`: Your LLM API key
   - Optional:
     - `PAT_USERNAME`: GitHub username for the personal access token
     - `PAT_TOKEN`: The personal access token
     - `LLM_BASE_URL`: Base URL for LLM API (only if using a proxy)

## 2. Setting up GitLab (CI Runner)

### Prerequisites

Create a GitLab Personal Access Token with API, read/write access

### Installation

## 3. Triggering OpenHands Agent

You can trigger OpenHands in two shared ways (works for both GitHub and GitLab):

Using the 'fix-me' label:

- Add the 'fix-me' label to any issue you want the AI to resolve
- The agent will consider all comments in the issue thread when resolving

Using `@openhands-agent` in an issue/pr comment:

- Create a new comment containing `@openhands-agent`
- The agent will only consider the comment + comment thread where it's mentioned

## 4. Running Locally

### Installation

```bash
pip install openhands-ai
```

### Setup

Create a GitHub or GitLab access token with appropriate permissions

Set up environment variables:

```bash
# GitHub credentials
export GITHUB_TOKEN="your-github-token"
export GIT_USERNAME="your-github-username"

# GitLab credentials (if using GitLab)
export GITLAB_TOKEN="your-gitlab-token"
export GIT_USERNAME="your-gitlab-username"

# LLM configuration
export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"
export LLM_API_KEY="your-llm-api-key"
export LLM_BASE_URL="your-api-url"  # Optional
```

### Resolving Issues

Resolve a single issue:

```bash
python -m openhands.resolver.resolve_issue --selected-repo [OWNER]/[REPO] --issue-number [NUMBER]
```

### Responding to PR Comments

Respond to comments on pull requests:

```bash
python -m openhands.resolver.send_pull_request --issue-number PR_NUMBER --issue-type pr
```

### Visualizing Results

View successful PRs:

```bash
grep '"success":true' output/output.jsonl | sed 's/.*\("number":[0-9]*\).*/\1/g'
```

Visualize specific PR:

```bash
python -m openhands.resolver.visualize_resolver_output --issue-number ISSUE_NUMBER --vis-method json
```

### Uploading PRs

Upload your changes in one of three ways:

```bash
python -m openhands.resolver.send_pull_request --issue-number ISSUE_NUMBER --username YOUR_GITHUB_OR_GITLAB_USERNAME --pr-type [branch|draft|ready]
```

## Custom Instructions

Add repository-specific instructions by creating a file at `.openhands/microagents/repo.md` in your repository. For more information about repository microagents, see [Repository Instructions](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents#2-repository-instructions-private).

## Troubleshooting

If you have any issues, please open an issue on this github repo, we're happy to help!
Alternatively, you can [email us](mailto:contact@all-hands.dev) or join the OpenHands Slack workspace (see [the README](/README.md) for an invite link).
