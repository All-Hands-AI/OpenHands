---
sidebar_label: manager
title: opendevin.server.agent.manager
---

## AgentManager Objects

```python
class AgentManager()
```

#### register\_agent

```python
def register_agent(sid: str)
```

Registers a new agent.

**Arguments**:

- `sid` - The session ID of the agent.

#### dispatch

```python
async def dispatch(sid: str, action: str | None, data: dict)
```

Dispatches actions to the agent from the client.

