# MCP Integration

## Capabilities
- Dynamic capability registration via `register_mcp_capability()`
- Automatic server selection based on required capabilities  
- Built-in retry logic with configurable attempts
- Endpoint routing with capability matching

## Usage Example
```python
# Initialize agent with MCP support
agent = AgentController(llm, config)

# Register capabilities
agent.register_mcp_capability("vision")

# Make MCP request
response = await agent.mcp_request(
    endpoint="config",
    payload={"action": "get_settings"},
    required_capabilities=["llm", "vision"]
)
```

## Configuration
```yaml
mcp:
  retries: 3               # Max retry attempts
  timeout: 5000            # Timeout in ms
  retry_delay: 0.5         # Delay between retries in seconds
  capabilities:            # Default capabilities
    - general
```

> Note: MCP requires AgentController context for full functionality