# Search Configuration

OpenHands provides a search engine capability that allows agents to perform web searches using the Brave Search API. This guide explains how to configure and use the search feature.

## Overview

The search engine feature enables agents to:
- Execute web search queries programmatically
- Get structured results including web pages, news, videos, and FAQs
- Avoid CAPTCHA challenges that often occur when using browser-based search

## Configuration

### Configuration Setup

The search engine feature is configured through the `search` section in your `config.toml`:

```toml
[search]
# Enable the search engine feature
enable_search_engine = true

# Set your Brave Search API key
# You can obtain one from the Brave Search API Dashboard: https://api.search.brave.com/app/keys
brave_api_key = "your-api-key-here"

# Optional: Override the Brave Search API URL if needed
# brave_api_url = "https://api.search.brave.com/res/v1/web/search"
```

Or when using Docker, set the environment variables:
```bash
# Enable the search engine feature
-e SEARCH_ENABLE_SEARCH_ENGINE=true

# Set your Brave Search API key
-e SEARCH_BRAVE_API_KEY="your-api-key-here"

# Optional: Override the Brave Search API URL
# -e SEARCH_BRAVE_API_URL="https://api.search.brave.com/res/v1/web/search"
```

## Search Results

When a search is performed, the results are returned in a structured format that includes:

- Web search results
- News articles
- Video content
- FAQ entries
- Discussion threads
- Infoboxes (when available)
- Location information (when relevant)

Each result type includes:
- Title
- URL (when applicable)
- Description or snippet
- Additional metadata specific to the result type

## Usage Example

When the search feature is enabled, agents can use the `search_engine` tool to perform searches. For example:

```python
# The agent can make a tool call like this:
{
    "name": "search_engine",
    "arguments": {
        "query": "latest developments in AI"
    }
}
```

The search results will be returned in a markdown-formatted structure that's easy for the agent to parse and understand.

## Best Practices

1. **Query Formulation**
   - Keep queries focused and specific
   - Include relevant keywords
   - Avoid overly complex or compound queries

2. **Rate Limiting**
   - Be mindful of API rate limits
   - Cache results when appropriate
   - Implement retries with exponential backoff for failed requests

3. **Error Handling**
   - Handle API errors gracefully
   - Provide meaningful feedback when searches fail
   - Have fallback strategies when search is unavailable

## Troubleshooting

Common issues and solutions:

1. **Search Not Working**
   - Verify `search.enable_search_engine` is set to `true` in your config
   - Confirm the Brave API key is correctly set in `search.brave_api_key`
   - Check API key permissions and quotas in the Brave Search API Dashboard

2. **No Results**
   - Verify the query is not empty
   - Try reformulating the search query
   - Check for any API response errors

3. **Rate Limiting**
   - Monitor API usage
   - Implement caching if needed
   - Consider upgrading API tier if limits are consistently hit