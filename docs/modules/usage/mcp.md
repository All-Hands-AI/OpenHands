# Model Context Protocol (MCP)

:::note
This page outlines how to configure and use the Model Context Protocol (MCP) in OpenHands, allowing you to extend the
agent's capabilities with custom tools.
:::

## Overview

Model Context Protocol (MCP) is a mechanism that allows OpenHands to communicate with external tool servers. These
servers can provide additional functionality to the agent, such as specialized data processing, external API access,
or custom tools. MCP is based on the open standard defined at [modelcontextprotocol.io](https://modelcontextprotocol.io).

## Configuration

MCP configuration is defined in the `[mcp]` section of your `config.toml` file.

### Configuration Example

```toml
[mcp]
# SSE Servers - External servers that communicate via Server-Sent Events
sse_servers = [
    # Basic SSE server with just a URL
    "http://example.com:8080/mcp",

    # SSE server with API key authentication
    {url="https://secure-example.com/mcp", api_key="your-api-key"}
]

# Stdio Servers - Local processes that communicate via standard input/output
stdio_servers = [
    # Basic stdio server
    {name="fetch", command="uvx", args=["mcp-server-fetch"]},

    # Stdio server with environment variables
    {
        name="data-processor",
        command="python",
        args=["-m", "my_mcp_server"],
        env={
            "DEBUG": "true",
            "PORT": "8080"
        }
    }
]
```

## Configuration Options

### SSE Servers

SSE servers are configured using either a string URL or an object with the following properties:

- `url` (required)
  - Type: `str`
  - Description: The URL of the SSE server

### Stdio Servers

Stdio servers are configured using an object with the following properties:

- `name` (required)
  - Type: `str`
  - Description: A unique name for the server

- `command` (required)
  - Type: `str`
  - Description: The command to run the server

- `args` (optional)
  - Type: `list of str`
  - Default: `[]`
  - Description: Command-line arguments to pass to the server

- `env` (optional)
  - Type: `dict of str to str`
  - Default: `{}`
  - Description: Environment variables to set for the server process

## How MCP Works

When OpenHands starts, it:

1. Reads the MCP configuration from `config.toml`.
2. Connects to any configured SSE servers.
3. Starts any configured stdio servers.
4. Registers the tools provided by these servers with the agent.

The agent can then use these tools just like any built-in tool. When the agent calls an MCP tool:

1. OpenHands routes the call to the appropriate MCP server.
2. The server processes the request and returns a response.
3. OpenHands converts the response to an observation and presents it to the agent.
