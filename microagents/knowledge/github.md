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

Here are some instructions for pushing, but ONLY do this if the user asks you to:
* NEVER push directly to the `main` or `master` branch
* Git config (username and email) is pre-set. Do not modify.
* You may already be on a branch starting with `openhands-workspace`. Create a new branch with a better name before pushing.
* Use the GitHub API to create a pull request, if you haven't already
* Create only ONE pull request per session/issue unless explicitly instructed to create additional pull requests.
* Once you've created your own branch or a pull request, continue to update it with new commits as needed. DO NOT create a new pull request for additional changes related to the same issue.
* If you need to make additional changes after creating a pull request, commit those changes to the same branch and push them to update the existing pull request.
* Preserve the original pull request title and purpose, only updating the description when necessary to reflect significant changes in approach or implementation.
* Use the main branch as the base branch, unless the user requests otherwise
* After opening or updating a pull request, send the user a short message with a link to the pull request.
* Prefer "Draft" pull requests when possible
* Do all of the above in as few steps as possible. E.g. you could open a PR with one step by running the following bash commands:
```bash
git remote -v && git branch # to find the current org, repo and branch
git checkout -b create-widget && git add . && git commit -m "Create widget" && git push -u origin create-widget
curl -X POST "https://api.github.com/repos/$ORG_NAME/$REPO_NAME/pulls" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -d '{"title":"Create widget","head":"create-widget","base":"openhands-workspace"}'
```
