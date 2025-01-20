---
name: gitlab
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- gitlab
- git
---

You have access to an environment variable, `GIT_TOKEN`, which allows you to interact with
the Gitlab API.

You can use `curl` with the `GIT_TOKEN` to interact with Gitlab's API.
ALWAYS use the Gitlab API for operations instead of a web browser.

Here are some instructions for pushing, but ONLY do this if the user asks you to:
* NEVER push directly to the `main` or `master` branch
* Git config (username and email) is pre-set. Do not modify.
* You may already be on a branch starting with `openhands-workspace`. Create a new branch with a better name before pushing.
* Use the Gitlab API to create a pull request, if you haven't already
* Once you've created your own branch or a pull request, continue to update it. Do NOT create a new one unless you are explicitly asked to. Update the PR title and description as necessary, but don't change the branch name.
* Use the main branch as the base branch, unless the user requests otherwise
* After opening or updating a pull request, send the user a short message with a link to the pull request.
* Prefer "Draft" pull requests when possible
* Do all of the above in as few steps as possible. E.g. you could open a PR with one step by running the following bash commands:
```bash
git remote -v && git branch # to find the current org, repo and branch
git checkout -b create-widget && git add . && git commit -m "Create widget" && git push -u origin create-widget
curl --request POST \
  --url "https://gitlab.com/api/v4/projects/${ORG_NAME}/${REPO_NAME}/merge_requests" \
  --header "Authorization: Bearer $GIT_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{
    "source_branch": "create-widget",
    "target_branch": "openhands-workspace",
    "title": "Create widget"
  }'

```
