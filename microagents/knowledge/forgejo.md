# Forgejo Knowledge

Forgejo is a self-hosted Git service that is a fork of Gitea. It provides a lightweight, open-source alternative to GitHub and GitLab. Codeberg.org is a popular instance of Forgejo.

## API

The Forgejo API is compatible with the Gitea API. It follows a RESTful design and uses JSON for data exchange. The base URL for the API is typically:

```
https://[forgejo-instance]/api/v1
```

For Codeberg, the base URL is:

```
https://codeberg.org/api/v1
```

### Authentication

Forgejo supports several authentication methods:

1. HTTP basic authentication
2. `token=...` parameter in URL query string
3. `access_token=...` parameter in URL query string
4. `Authorization: token ...` header in HTTP headers

### Common Endpoints

- `/user` - Get authenticated user information
- `/user/repos` - List repositories for the authenticated user
- `/repos/search` - Search for repositories
- `/repos/{owner}/{repo}` - Get repository information
- `/repos/{owner}/{repo}/issues` - List issues for a repository
- `/repos/{owner}/{repo}/pulls` - List pull requests for a repository

### Pagination

The API supports pagination with the `page` and `limit` parameters. The `Link` header is returned with next, previous, and last page links if there are more than one page.

## Differences from GitHub/GitLab

- Forgejo uses `limit` instead of `per_page` for pagination
- Forgejo uses `stars_count` instead of `stargazers_count` for repository stars
- Forgejo doesn't have a direct API for requesting reviewers on pull requests
- Forgejo doesn't support replying to specific comments in the same way as GitHub

## Codeberg Specifics

Codeberg.org is a popular Forgejo instance hosted in the EU. It's a non-profit, community-driven platform focused on free and open source software.

- Base URL: `https://codeberg.org/api/v1`
- Authentication: Uses personal access tokens
- Rate Limiting: Has rate limits to prevent abuse

## Using the Forgejo Integration

To use the Forgejo integration in OpenHands:

1. Generate a personal access token from your Forgejo instance (e.g., Codeberg)
2. Set the token as an environment variable: `FORGEJO_TOKEN`
3. Use the Forgejo provider in your code

Example:
```python
from openhands.integrations.service_types import ProviderType
from openhands.integrations.provider import ProviderHandler

# Create a provider handler with Forgejo token
provider_handler = ProviderHandler({
    ProviderType.FORGEJO: ProviderToken(token=SecretStr("your_token"))
})

# Get user information
user = await provider_handler.get_user()

# Search repositories
repos = await provider_handler.search_repositories("query", 10, "updated", "desc")
```