---
sidebar_label: manager
title: opendevin.server.session.manager
---

## SessionManager Objects

```python
class SessionManager()
```

#### send

```python
async def send(sid: str, data: Dict[str, object]) -> bool
```

Sends data to the client.

#### send\_error

```python
async def send_error(sid: str, message: str) -> bool
```

Sends an error message to the client.

#### send\_message

```python
async def send_message(sid: str, message: str) -> bool
```

Sends a message to the client.

