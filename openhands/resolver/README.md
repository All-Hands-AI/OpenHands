# OpenHands GitHub & GitLab Issue Resolver 🙌

Need help resolving GitHub or GitLab issues? Let an AI agent help you out!

This tool uses OpenHands AI agents to automatically resolve issues in your repositories. It's designed to handle one issue at a time with high quality.

## Using the GitHub Actions Workflow

1. [Create a personal access token](https://github.com/settings/tokens?type=beta) with read/write scope for "contents", "issues", "pull requests", and "workflows"

2. Create an API key for the [Claude API](https://www.anthropic.com/api) (recommended) or another supported LLM service

3. Copy `examples/openhands-resolver.yml` to your repository's `.github/workflows/` directory

4. Configure repository permissions:
   - Go to `Settings -> Actions -> General -> Workflow permissions`
   - Select "Read and write permissions"
   - Enable "Allow Github Actions to create and approve pull requests"

5. Set up [GitHub secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions):
   - Required:
     - `LLM_API_KEY`: Your LLM API key
   - Optional:
     - `PAT_USERNAME`: GitHub username for the personal access token
     - `PAT_TOKEN`: The personal access token
     - `LLM_BASE_URL`: Base URL for LLM API (only if using a proxy)

6. Usage:
   - Using the 'fix-me' label:
     - Add the 'fix-me' label to any issue you want the AI to resolve
   - Using `@openhands-agent` mention:
     - Create a comment containing `@openhands-agent` in any issue

## Manual Installation

1. Install the package:
```bash
pip install openhands-ai
```

2. Create a GitHub or GitLab access token with appropriate permissions

3. Set up environment variables:
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

## Resolving Issues

Resolve a single issue:
```bash
python -m openhands.resolver.resolve_issue --selected-repo [OWNER]/[REPO] --issue-number [NUMBER]
```

## Responding to PR Comments

Respond to comments on pull requests:
```bash
python -m openhands.resolver.send_pull_request --issue-number PR_NUMBER --issue-type pr
```

## Visualizing Results

View successful PRs:
```bash
grep '"success":true' output/output.jsonl | sed 's/.*\("number":[0-9]*\).*/\1/g'
```

Visualize specific PR:
```bash
python -m openhands.resolver.visualize_resolver_output --issue-number ISSUE_NUMBER --vis-method json
```

## Uploading PRs

Upload your changes in one of three ways:
```bash
python -m openhands.resolver.send_pull_request --issue-number ISSUE_NUMBER --username YOUR_USERNAME --pr-type [branch|draft|ready]
```

## Custom Instructions

Add repository-specific instructions by creating a file at `.openhands/microagents/repo.md` in your repository.

## Troubleshooting

Need help? [Open an issue](https://github.com/all-hands-ai/openhands/issues) or email [contact@all-hands.dev](mailto:contact@all-hands.dev).
