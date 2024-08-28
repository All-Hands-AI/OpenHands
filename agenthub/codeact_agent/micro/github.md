---
name: github
agent: CodeActAgent
require_env_var:
    SANDBOX_ENV_GITHUB_TOKEN: "Create a GitHub Personal Access Token (https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) and set it as SANDBOX_GITHUB_TOKEN in your environment variables."
---

# How to Interact with Github

## Environment Variable Available

1. `GITHUB_TOKEN`: A read-only token for Github.

## Using GitHub's RESTful API

Use `curl` with the `GITHUB_TOKEN` to interact with GitHub's API. Here are some common operations:

1. View an issue:
   ```
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}
   ```

2. List repository issues:
   ```
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/repos/{owner}/{repo}/issues
   ```

3. Get repository details:
   ```
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/repos/{owner}/{repo}
   ```

4. List pull requests:
   ```
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/repos/{owner}/{repo}/pulls
   ```

5. Get user information:
   ```
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/user
   ```

Replace `{owner}`, `{repo}`, and `{issue_number}` with appropriate values.

## Important Notes

1. Always use the GitHub API for operations instead of a web browser.
2. The `GITHUB_TOKEN` is read-only. Avoid operations that require write access.
3. Git config (username and email) is pre-set. Do not modify.
4. Edit and test code locally. Never push directly to remote.
5. Verify correct branch before committing.
6. Commit changes frequently.
7. If the issue or task is ambiguous or lacks sufficient detail, always request clarification from the user before proceeding.
8. You should avoid using command line tools like `sed` for file editing.
