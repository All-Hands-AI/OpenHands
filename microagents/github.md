---
name: github
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- github
- git
---

You have access to an environment variable, `GITHUB_TOKEN`, which allows you to interact with
the GitHub API.

You can use `curl` with the `GITHUB_TOKEN` to interact with GitHub's API.
ALWAYS use the GitHub API for operations instead of a web browser.

If you encounter authentication issues when pushing to GitHub (such as password prompts or permission errors), the old token may have expired. In such case, update the remote URL to include the current token: `git remote set-url origin https://${GITHUB_TOKEN}@github.com/username/repo.git`

## IMPORTANT: ALWAYS USE THE MCP TOOL FOR CREATING PULL REQUESTS

When creating pull requests, ALWAYS use the MCP (Model Context Protocol) tool instead of directly using the GitHub API. The MCP tool provides a standardized interface for creating pull requests and handles authentication automatically.

To create a pull request using the MCP tool:
1. Push your changes to a branch
2. Use the MCP `create_github_pr` tool to create the pull request

Example of using the MCP tool to create a pull request:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "callTool",
  "params": {
    "name": "create_github_pr",
    "arguments": {
      "repository": "owner/repo",
      "title": "Your PR title",
      "body": "Description of your changes",
      "head": "your-feature-branch",
      "base": "main",
      "draft": true
    }
  }
}
```

The MCP server will handle authentication and create the pull request using the appropriate GitHub token from the user's settings.

Here are some instructions for pushing, but ONLY do this if the user asks you to:
* NEVER push directly to the `main` or `master` branch
* Git config (username and email) is pre-set. Do not modify.
* You may already be on a branch starting with `openhands-workspace`. Create a new branch with a better name before pushing.
* Once you've created your own branch or a pull request, continue to update it. Do NOT create a new one unless you are explicitly asked to. Update the PR title and description as necessary, but don't change the branch name.
* Use the main branch as the base branch, unless the user requests otherwise
* After opening or updating a pull request, send the user a short message with a link to the pull request.
* Prefer "Draft" pull requests when possible
* Do NOT mark a pull request as ready to review unless the user explicitly says so
* Do all of the above in as few steps as possible. E.g. you could open a PR with one step by running the following bash commands and then using the MCP tool:
```bash
git remote -v && git branch # to find the current org, repo and branch
git checkout -b create-widget && git add . && git commit -m "Create widget" && git push -u origin create-widget

# Then use the MCP tool to create the PR instead of directly using the GitHub API
```

If for some reason the MCP tool is not available, you can fall back to using the GitHub API directly:
```bash
curl -X POST "https://api.github.com/repos/$ORG_NAME/$REPO_NAME/pulls" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -d '{"title":"Create widget","head":"create-widget","base":"openhands-workspace"}'
```
