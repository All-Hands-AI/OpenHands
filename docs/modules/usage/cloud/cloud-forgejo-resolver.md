# Forgejo Integration

OpenHands supports integration with Forgejo, a self-hosted Git service that is a fork of Gitea. This integration allows you to interact with Forgejo instances like Codeberg.org and other self-hosted Forgejo servers.

## Setting Up Forgejo Integration

To use the Forgejo integration, you need to:

1. Generate a personal access token from your Forgejo instance
2. Configure OpenHands to use this token

### Generating a Personal Access Token

1. Log in to your Forgejo instance (e.g., Codeberg.org)
2. Go to your user settings (click on your profile picture in the top right corner, then "Settings")
3. In the left sidebar, click on "Applications"
4. Under "Generate New Token", enter a name for your token (e.g., "OpenHands")
5. Select the appropriate scopes for your token (at minimum, you'll need "repo" access)
6. Click "Generate Token"
7. Copy the generated token (you won't be able to see it again)

### Configuring OpenHands

You can provide your Forgejo token to OpenHands in one of these ways:

#### Environment Variable

Set the `FORGEJO_TOKEN` environment variable:

```bash
export FORGEJO_TOKEN=your_token_here
```

#### Configuration File

Add your token to the OpenHands configuration file:

```yaml
provider_tokens:
  forgejo:
    token: your_token_here
```

## Using the Forgejo Integration

Once configured, you can use the Forgejo integration to:

- Browse and search repositories
- View issues and pull requests
- Clone repositories
- Create pull requests
- Request reviewers for pull requests
- Comment on issues and pull requests
- View and interact with review threads

The Forgejo integration works similarly to the GitHub and GitLab integrations, with the same interface and functionality. Our implementation handles API differences transparently, so you can use the same code regardless of which Git service you're using.

## Customizing the Base URL

By default, the Forgejo integration uses Codeberg.org as the base URL (`https://codeberg.org/api/v1`). If you're using a different Forgejo instance, you can customize the base URL in several ways:

### Using Environment Variables

You can set the `FORGEJO_BASE_URL` environment variable:

```bash
export FORGEJO_BASE_URL=https://your-forgejo-instance.com/api/v1
```

### Using Configuration File

Add the base URL to your OpenHands configuration file:

```yaml
forgejo:
  base_url: https://your-forgejo-instance.com/api/v1
```

### Programmatically

You can also set the base URL programmatically when creating a Forgejo service:

```python
from openhands.integrations.forgejo.forgejo_service import ForgejoService
from pydantic import SecretStr

# Create a Forgejo service with a custom base URL
forgejo_service = ForgejoService(
    token=SecretStr("your_token_here"),
    base_url="https://your-forgejo-instance.com/api/v1"
)
```

The base URL should always point to the API endpoint of your Forgejo instance, which typically ends with `/api/v1`.

## Limitations and Considerations

- API rate limits may vary depending on the Forgejo instance
- Some Forgejo instances may have different API configurations or versions
- The implementation includes robust error handling and timeouts to ensure reliability
- Network connectivity issues are handled gracefully with appropriate fallbacks

## Implementation Details

Our Forgejo integration includes several key features:

- **Error Handling**: All API calls include proper error handling to ensure robustness
- **Timeouts**: API calls include timeouts to prevent hanging on slow or unresponsive servers
- **Fallbacks**: When certain API calls fail, the implementation falls back to alternative methods
- **Review Threads**: Support for code review threads, organized by file path and line number
- **Reviewer Requests**: Support for requesting reviewers on pull requests

## Testing

The Forgejo integration has been tested against Codeberg.org, which is one of the most popular public Forgejo instances. If you encounter any issues with other Forgejo instances, please report them so we can improve the integration.