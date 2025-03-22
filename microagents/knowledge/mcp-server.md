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

This document provides instructions for creating clients to interact with MCP servers.

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

- Ping: Checks if the server is alive.
- Initialize: Initializes the server and negotiates capabilities.
- ListTools: Lists available tools.
- CallTool: Calls a specific tool.
- ListResources: Lists available resources.
- ReadResource: Reads a specific resource.
- ListPrompts: Lists available prompts.
- GetPrompt: Retrieves a specific prompt.
- Complete: Provides completions for prompts and resource templates.


## Prerequisites

First, you will always need to ask the user to provide the mcp server configurations, which contains the commands
and arguments to start the server locally if the user has not supplied it yet, as the client code will need
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


## Create a session to interact with the MCP server

First, you may need to install the `mcp` library to interact with `pip install mcp` if it is not
installed yet.

Below is the sample code to create a session to use tools via the MCP server in Python:

```python
from typing import List, Dict, Any, Optional, Literal
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, stdio_client

class MCPServerSession:
    """
    A lightweight wrapper around the MCP library for connecting to MCP servers
    and calling tools, designed for use in interactive environments like IPython.
    """

    def __init__(self,
                 command: str,
                 args: List[str] = None,
                 env: Dict[str, str] = None,
                 encoding: str = "utf-8",
                 encoding_error_handler: Literal['strict', 'ignore', 'replace'] = "strict"):
        """
        Initialize an MCP server session with the provided parameters.

        Args:
            command: The command to run the server
            args: Command line arguments
            env: Environment variables
            encoding: Encoding to use for stdio
            encoding_error_handler: How to handle encoding errors
        """
        self.command = command
        self.args = args or []
        self.env = env
        self.encoding = encoding
        self.encoding_error_handler = encoding_error_handler

        # Session state
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None
        self.connected = False

    async def connect(self):
        """
        Connect to the MCP server using the parameters provided at initialization.
        """
        if self.connected:
            return

        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=self.env,
            encoding=self.encoding,
            encoding_error_handler=self.encoding_error_handler
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()
        self.connected = True

        return self

    async def list_tools(self):
        """
        List all available tools from the MCP server.

        Returns:
            List of tool objects
        """
        if not self.connected:
            await self.connect()

        response = await self.session.list_tools()
        return response.tools

    async def call_tool(self, tool_name: str, input_data: Dict[str, Any]):
        """
        Call a specific tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            input_data: Input data for the tool

        Returns:
            The tool's response
        """
        if not self.connected:
            await self.connect()

        response = await self.session.call_tool(tool_name, input_data)
        return response

    async def close(self):
        """Clean up resources and close the connection."""
        if self.connected:
            await self.exit_stack.aclose()
            self.session = None
            self.stdio = None
            self.write = None
            self.connected = False
```

You can adapt this code with the arguments provided by the user to create a session to interact with
the MCP server.

If anything is unclear or you need more details, you can refer to the official documentation.
