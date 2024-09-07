---
name: github
agent: CodeActAgent
require_env_var:
    SANDBOX_ENV_GITHUB_TOKEN: "Create a GitHub Personal Access Token (https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) and set it as SANDBOX_GITHUB_TOKEN in your environment variables."
---

# How to Interact with Github

## Environment Variable Available

- `GITHUB_TOKEN`: A read-only token for Github.

## Using GitHub's RESTful API

Use `curl` with the `GITHUB_TOKEN` to interact with GitHub's API. Here are some common operations:

Here's a template for API calls:

```sh
curl -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/{endpoint}"
```

First replace `{endpoint}` with the specific API path. Common operations:

1. View an issue or pull request:
   - Issues: `/repos/{owner}/{repo}/issues/{issue_number}`
   - Pull requests: `/repos/{owner}/{repo}/pulls/{pull_request_number}`

2. List repository issues or pull requests:
   - Issues: `/repos/{owner}/{repo}/issues`
   - Pull requests: `/repos/{owner}/{repo}/pulls`

3. Search issues or pull requests:
   - `/search/issues?q=repo:{owner}/{repo}+is:{type}+{search_term}+state:{state}`
   - Replace `{type}` with `issue` or `pr`

4. List repository branches:
   `/repos/{owner}/{repo}/branches`

5. Get commit details:
   `/repos/{owner}/{repo}/commits/{commit_sha}`

6. Get repository details:
   `/repos/{owner}/{repo}`

7. Get user information:
   `/user`

8. Search repositories:
   `/search/repositories?q={query}`

9. Get rate limit status:
   `/rate_limit`

Replace `{owner}`, `{repo}`, `{commit_sha}`, `{issue_number}`, `{pull_request_number}`,
`{search_term}`, `{state}`, and `{query}` with appropriate values.

## Important Notes

1. Always use the GitHub API for operations instead of a web browser.
2. The `GITHUB_TOKEN` is read-only. Avoid operations that require write access.
3. Git config (username and email) is pre-set. Do not modify.
4. Edit and test code locally. Never push directly to remote.
5. Verify correct branch before committing.
6. Commit changes frequently.
7. If the issue or task is ambiguous or lacks sufficient detail, always request clarification from the user before proceeding.
8. You should avoid using command line tools like `sed` for file editing.
