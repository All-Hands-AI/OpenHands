# MCP (Model Context Protocol) Setup Guide

MCP servers extend OpenHands with additional tools and capabilities. This guide explains what MCP is, why you might want to use it, and how to configure it with your Ollama setup.

## What is MCP?

**Model Context Protocol (MCP)** is a standard that allows AI assistants to securely connect to external data sources and tools. MCP servers provide additional capabilities like:

- File system operations
- Database access
- Web search
- Git operations
- Time/date functions
- Memory persistence
- And much more!

## Do You Need MCP?

**MCP is completely optional.** OpenHands works perfectly fine without any MCP servers. However, MCP can enhance your experience by providing:

✅ **Enhanced File Operations**: Better file management beyond basic editing  
✅ **Database Integration**: Direct SQLite database operations  
✅ **Web Search**: Real-time web search capabilities  
✅ **Git Integration**: Advanced version control operations  
✅ **Persistent Memory**: Remember information across sessions  
✅ **Time/Date Functions**: Current time and date operations  

## Quick Start: Enable Basic MCP Servers

To get started with some useful MCP servers, edit your `config.toml` file and uncomment the servers you want:

### 1. File System Server (Recommended)
```toml
[[mcp.stdio_servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem@0.1.0", "/workspace"]
```

### 2. Git Server (Recommended for development)
```toml
[[mcp.stdio_servers]]
name = "git"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-git@0.1.0"]
```

### 3. Time Server (Useful for timestamps)
```toml
[[mcp.stdio_servers]]
name = "time"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-time@0.1.0"]
```

## Available MCP Servers

### Core Servers (No API Keys Required)

| Server | Purpose | Configuration |
|--------|---------|---------------|
| **filesystem** | File operations, directory listing | `@modelcontextprotocol/server-filesystem@0.1.0` |
| **git** | Git operations, version control | `@modelcontextprotocol/server-git@0.1.0` |
| **sqlite** | SQLite database operations | `@modelcontextprotocol/server-sqlite@0.1.0` |
| **time** | Current time and date | `@modelcontextprotocol/server-time@0.1.0` |
| **memory** | Persistent memory across sessions | `@modelcontextprotocol/server-memory@0.1.0` |

### Search Servers (API Keys Required)

| Server | Purpose | API Key Required |
|--------|---------|------------------|
| **tavily** | Web search via Tavily | Tavily API Key |
| **brave-search** | Web search via Brave | Brave Search API Key |

## Configuration Examples

### Basic Development Setup
```toml
[mcp]
[[mcp.stdio_servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem@0.1.0", "/workspace"]

[[mcp.stdio_servers]]
name = "git"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-git@0.1.0"]

[[mcp.stdio_servers]]
name = "time"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-time@0.1.0"]
```

### Full Setup with Web Search
```toml
[mcp]
[[mcp.stdio_servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem@0.1.0", "/workspace"]

[[mcp.stdio_servers]]
name = "git"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-git@0.1.0"]

[[mcp.stdio_servers]]
name = "sqlite"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-sqlite@0.1.0"]

[[mcp.stdio_servers]]
name = "time"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-time@0.1.0"]

[[mcp.stdio_servers]]
name = "memory"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-memory@0.1.0"]

[[mcp.stdio_servers]]
name = "tavily"
command = "npx"
args = ["-y", "tavily-mcp@0.2.1"]
[mcp.stdio_servers.env]
TAVILY_API_KEY = "your-tavily-api-key-here"
```

## Getting API Keys

### Tavily Search API
1. Visit [Tavily.com](https://tavily.com)
2. Sign up for an account
3. Get your API key from the dashboard
4. Add it to your configuration

### Brave Search API
1. Visit [Brave Search API](https://api.search.brave.com)
2. Sign up for an account
3. Get your API key
4. Add it to your configuration

## How to Enable MCP Servers

### Method 1: Edit config.toml directly
1. Open `config.toml` in your OpenHands directory
2. Find the `[mcp]` section
3. Uncomment the servers you want to use
4. Save the file
5. Restart OpenHands: `./start-ollama.sh restart`

### Method 2: Use the Web Interface
1. Open OpenHands at http://localhost:3000
2. Click "Edit Configuration" in the MCP section
3. Add your desired MCP servers
4. Save the configuration

## Testing MCP Servers

After enabling MCP servers, you can test them by asking OpenHands to:

### File System Server
- "List the files in the current directory"
- "Create a new file called test.txt"
- "Show me the contents of package.json"

### Git Server
- "Show me the git status"
- "Create a new branch called feature-test"
- "Show me the git log"

### Time Server
- "What's the current time?"
- "What's today's date?"

### Search Server (if configured)
- "Search the web for Python best practices"
- "Find recent news about AI development"

## Troubleshooting

### Common Issues

1. **"No MCP servers are currently configured"**
   - This is normal if you haven't enabled any MCP servers
   - MCP is optional - OpenHands works fine without it

2. **MCP server fails to start**
   - Check that Node.js/npm is available in your container
   - Verify the server package name and version
   - Check the logs: `./start-ollama.sh logs`

3. **API key errors**
   - Verify your API keys are correct
   - Check that environment variables are properly set
   - Ensure API keys have the necessary permissions

### Debugging MCP

To debug MCP issues:

1. **Check OpenHands logs**:
   ```bash
   ./start-ollama.sh logs
   ```

2. **Test MCP server manually**:
   ```bash
   npx -y @modelcontextprotocol/server-filesystem@0.1.0 /workspace
   ```

3. **Verify Node.js availability**:
   ```bash
   docker exec -it openhands-ollama node --version
   docker exec -it openhands-ollama npm --version
   ```

## Performance Considerations

- **Start with basic servers**: Begin with filesystem, git, and time servers
- **Add search gradually**: Web search servers can be slower
- **Monitor resource usage**: Each MCP server uses additional resources
- **Local vs Remote**: Local servers (filesystem, git) are faster than remote APIs

## Security Notes

- **File system access**: The filesystem server has access to your workspace
- **API keys**: Store API keys securely, don't commit them to version control
- **Network access**: Some MCP servers make external network requests
- **Permissions**: MCP servers run with the same permissions as OpenHands

## Custom MCP Servers

You can also create custom MCP servers or use community-developed ones. Check the [MCP documentation](https://modelcontextprotocol.io/) for more information.

---

**Remember**: MCP is entirely optional. If you're just getting started with OpenHands and Ollama, you can skip MCP configuration and add it later when you need additional capabilities.