---
name: github
agent: CodeActAgent
triggers:
- github
- git
---

You have access to an environment variable, `GITHUB_TOKEN`, which allows you to interact with
the GitHub API.

Use `curl` with the `GITHUB_TOKEN` to interact with GitHub's API.
ALWAYS use the GitHub API for operations instead of a web browser.

If you're asked to push your changes to a repository:
* NEVER push directly to the `main` or `master` branch
* Git config (username and email) is pre-set. Do not modify.
* You may already be on a branch called `openhands-workspace`. Create a new branch with a better name before pushing.
* Use the GitHub API to create a pull request, if you haven't already
* After opening or updating a pull request, send the user a short message with a link to the pull request.
* Do all of the above in as few steps as possible. E.g. you could open a PR with one step by doing:
```bash
<execute_bash>
git checkout -b create-widget
git add .
git commit -m "Create widget"
git push origin create-widget
curl -X POST "https://api.github.com/repos/CodeActOrg/openhands/pulls" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -d '{"title":"Create widget","head":"create-widget","base":"openhands-workspace"}'
</execute_bash>
```
