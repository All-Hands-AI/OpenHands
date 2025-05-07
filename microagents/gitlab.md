---
name: gitlab
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- gitlab
- git
---

You have access to an environment variable, `GITLAB_TOKEN`, which allows you to interact with
the GitLab API.

You can use `curl` with the `GITLAB_TOKEN` to interact with GitLab's API.
ALWAYS use the GitLab API for operations instead of a web browser.

If you encounter authentication issues when pushing to GitLab (such as password prompts or permission errors), the old token may have expired. In such case, update the remote URL to include the current token: `git remote set-url origin https://oauth2:${GITLAB_TOKEN}@gitlab.com/username/repo.git`

## IMPORTANT: ALWAYS USE THE MCP TOOL FOR CREATING MERGE REQUESTS

When creating merge requests, ALWAYS use the MCP (Model Context Protocol) tool instead of directly using the GitLab API. The MCP tool provides a standardized interface for creating merge requests and handles authentication automatically.

To create a merge request using the MCP tool:
1. Push your changes to a branch
2. Use the MCP `create_gitlab_mr` tool to create the merge request

Example of using the MCP tool to create a merge request:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "callTool",
  "params": {
    "name": "create_gitlab_mr",
    "arguments": {
      "project_id": "group/project",
      "title": "Your MR title",
      "description": "Description of your changes",
      "source_branch": "your-feature-branch",
      "target_branch": "main",
      "draft": true
    }
  }
}
```

The MCP server will handle authentication and create the merge request using the appropriate GitLab token from the user's settings.

Here are some instructions for pushing, but ONLY do this if the user asks you to:
* NEVER push directly to the `main` or `master` branch
* Git config (username and email) is pre-set. Do not modify.
* You may already be on a branch starting with `openhands-workspace`. Create a new branch with a better name before pushing.
* Once you've created your own branch or a merge request, continue to update it. Do NOT create a new one unless you are explicitly asked to. Update the MR title and description as necessary, but don't change the branch name.
* Use the main branch as the base branch, unless the user requests otherwise
* After opening or updating a merge request, send the user a short message with a link to the merge request.
* Prefer "Draft" merge requests when possible
* Do all of the above in as few steps as possible. E.g. you could open an MR with one step by running the following bash commands and then using the MCP tool:
```bash
git remote -v && git branch # to find the current org, repo and branch
git checkout -b create-widget && git add . && git commit -m "Create widget" && git push -u origin create-widget

# Then use the MCP tool to create the MR instead of directly using the GitLab API
```

IMPORTANT: NEVER use the GitLab API directly to create merge requests. ALWAYS use the MCP tool.
