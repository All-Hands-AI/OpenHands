---
sidebar_label: listen
title: opendevin.server.listen
---

#### get\_litellm\_models

```python
@app.get('/api/litellm-models')
async def get_litellm_models()
```

Get all models supported by LiteLLM.

#### get\_agents

```python
@app.get('/api/agents')
async def get_agents()
```

Get all agents supported by LiteLLM.

#### get\_token

```python
@app.get('/api/auth')
async def get_token(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme))
```

Generate a JWT for authentication when starting a WebSocket connection. This endpoint checks if valid credentials
are provided and uses them to get a session ID. If no valid credentials are provided, it generates a new session ID.

