# How to enable A2A agents

add the following field into `config.toml`:

```toml
[agent]
a2a_server_urls = ["http://localhost:10002"] # A2A servers
```

## A2A Servers

Follow [this tutorial](https://github.com/oraichain/A2A/blob/main/samples/python/agents/autogen/README.md) to start an A2A server

# Test A2A Agents

1. Disable all MCP servers, and enable only the A2A servers in `config.toml`
2. Run the server via CLI. Eg:

```bash
poetry run python -m openhands.core.cli -t "What's the ORAI balance of orai179dea42h80arp69zd779zcav5jp0kv04zx4h09"
```

Observe the result.
