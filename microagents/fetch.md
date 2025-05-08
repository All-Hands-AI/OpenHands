---
name: fetch
type: knowledge
version: 1.0.0
agent: CodeActAgent
trigger_type: always
mcp_tools:
  stdio_servers:
    - name: "fetch"
      command: "python"
      args: ["-m", "mcp.fetch"]
      env:
        MCP_FETCH_TIMEOUT: "30"
---

# Fetch Microagent

This microagent provides access to the MCP "fetch" tool, which allows you to read content from websites. The fetch tool is always available and can be used to retrieve information from the internet.

## Capabilities

The fetch tool allows you to:
- Retrieve content from any URL
- Convert HTML content to markdown for better readability
- Control the amount of content retrieved with pagination options
- Optionally retrieve raw HTML content

## Usage

You can use the fetch tool to retrieve content from a URL:

```
fetch(url="https://example.com")
```

### Parameters

- `url` (required): The URL to fetch content from
- `max_length` (optional, default=5000): Maximum number of characters to return
- `start_index` (optional, default=0): Start index for pagination when retrieving large content
- `raw` (optional, default=False): Whether to return raw HTML instead of converted markdown

### Examples

Basic usage:
```
fetch(url="https://example.com")
```

Retrieving raw HTML:
```
fetch(url="https://example.com", raw=True)
```

Pagination for large content:
```
# First request
content = fetch(url="https://example.com")

# If content is truncated, get more content starting from where the previous request ended
more_content = fetch(url="https://example.com", start_index=5000)
```

## Limitations

- Some websites may block automated access through their robots.txt file
- Very large pages may need to be retrieved in multiple requests using pagination
- JavaScript-rendered content may not be fully captured

## Best Practices

- Always check if the content was truncated and use pagination if needed
- Prefer using the markdown conversion (default) for better readability
- Be respectful of website terms of service and robots.txt restrictions