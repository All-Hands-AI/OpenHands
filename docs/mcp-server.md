# MCP Server for GitHub PR and GitLab MR Creation

This document describes the Model Context Protocol (MCP) server implementation in OpenHands that enables creating pull requests on GitHub and merge requests on GitLab directly from the chat interface.

## Overview

The MCP server provides a standardized interface for creating pull requests and merge requests using the JSON-RPC 2.0 protocol. It integrates with OpenHands' existing GitHub and GitLab clients to handle authentication and API calls.

## Features

- Implements the core MCP protocol using JSON-RPC 2.0
- Provides session management for MCP clients
- Exposes tools for creating pull requests on GitHub and merge requests on GitLab
- Integrates with OpenHands' existing GitHub and GitLab clients
- Follows the MCP specification for capability negotiation and tool definitions
- Properly retrieves GitHub/GitLab tokens from user secrets or environment variables

## Configuration

To configure the MCP server in your OpenHands configuration, add the following to your `config.toml` file:

```toml
[mcp]
# List of MCP SSE servers
sse_servers = [
    {
        # The URL of the MCP server
        url = "http://localhost:12000/mcp",
        # Optional API key for authentication (not required for local development)
        api_key = ""
    }
]
```

## Usage

The MCP server exposes the following tools:

### GitHub Pull Request Creation

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "callTool",
  "params": {
    "name": "create_github_pr",
    "arguments": {
      "repository": "owner/repo",
      "title": "Your PR title",
      "body": "Description of your changes",
      "head": "your-feature-branch",
      "base": "main",
      "draft": true
    }
  }
}
```

### GitLab Merge Request Creation

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

## Authentication

The MCP server retrieves GitHub and GitLab tokens from the following sources, in order of precedence:

1. User secrets stored in the OpenHands settings store
2. Environment variables (`GITHUB_TOKEN` and `GITLAB_TOKEN`)

If no token is found, the server will return an error.

## Microagent Integration

The GitHub and GitLab microagents have been updated to use the MCP server for creating pull requests and merge requests. This ensures that all PR/MR creation requests go through the standardized MCP interface, which provides better security and consistency.

## Implementation Details

The MCP server is implemented as a FastAPI router in `openhands/server/routes/mcp.py`. It handles the following MCP methods:

- `initialize`: Initialize the MCP session and negotiate capabilities
- `shutdown`: Shut down the MCP session
- `listTools`: List available tools
- `callTool`: Call a specific tool with arguments

The server maintains session state for each client, including authentication tokens and service instances.