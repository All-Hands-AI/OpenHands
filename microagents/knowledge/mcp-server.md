---
 name: mcp-server
 type: knowledge
 agent: CodeActAgent
 version: 1.0.0
 triggers:
 - mcp
 - mcp-server
 - mcp-client
---

# General guide to interact with the MCP servers provided by users

This document provides instructions to interact with MCP servers via custom utility functions.

## What is MCP?

MCP is an open protocol that standardizes how applications provide context to LLMs. Think of MCP
like a USB-C port for AI applications. Just as USB-C provides a standardized way to connect your
devices to various peripherals and accessories, MCP provides a standardized way to connect AI models
to different data sources and tools.

Core concepts of MCP include:
- *Resources*: Resources represent any kind of data that an MCP server wants to make available to
  clients.
- *Tools*: Tools in MCP allow servers to expose executable functions that can be invoked by clients
  and used by LLMs to perform actions.
- *Prompts*: Prompts in MCP are predefined templates, enable servers to define reusable prompt templates and workflows that clients can easily surface to users and LLMs.

If you need more details when working with MCP, you can refer to the official document [here](https://modelcontextprotocol.io/).


### Architecture

MCP follows a client-server architecture where:
- Hosts are LLM applications (like Claude Desktop or IDEs) that initiate connections
- Clients maintain 1:1 connections with servers, inside the host application
- Servers provide context, tools, and prompts to clients


### Typical Requests Supported by MCP Servers

Below is the full list of requests supported by the MCP servers, note that not all servers support
all requests:

- ListTools: Lists available tools.
- CallTool: Calls a specific tool.
- ListResources: Lists available resources.
- ReadResource: Reads a specific resource.
- ListPrompts: Lists available prompts.
- GetPrompt: Retrieves a specific prompt.
- Complete: Provides completions for prompts and resource templates.


## Prerequisites

First, you will always need to ask the user to provide the mcp server configurations, which contains the commands
and arguments to start the server locally if the user has not supplied it yet, as the utility functions will need
them to start and connect to the server.

Example:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
      }
    }
  }
}
```

Always ensure the user provides this configuration information before proceeding. Do not assume the
server is running or take any further steps without confirmation.


## Create a session to interact with the MCP server using the provided utility functions

The `call_tool` and `list_tools` functions provide a simple interface to interact with MCP servers. These functions automatically handle connections and cleanup for each request, making them robust and easy to use.

Also, those functions will automatically spawn the server, so please don't try to start the server manually.

Below is the sample code to create a session to use tools via the MCP server in Python.

```python
# We don't need to import the functions as they are already available
config = {
    "command": "your_command",
    "args": ["--arg1", "--arg2"],
    "env": {"ENV_VAR": "value"}
}

# List available tools and check their signatures
tools = await list_tools(config)
print(tools)

# Call a specific tool
result = await call_tool(config, "tool_name", {"param1": "value1"})
print(result)
```

If anything is unclear or you need more details, you can refer to the official documentation.
