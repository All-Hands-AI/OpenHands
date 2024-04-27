---
sidebar_label: agent
title: opendevin.server.agent.agent
---

## AgentUnit Objects

```python
class AgentUnit()
```

Represents a session with an agent.

**Attributes**:

- `controller` - The AgentController instance for controlling the agent.
- `agent_task` - The task representing the agent&#x27;s execution.

#### \_\_init\_\_

```python
def __init__(sid)
```

Initializes a new instance of the Session class.

#### send\_error

```python
async def send_error(message)
```

Sends an error message to the client.

**Arguments**:

- `message` - The error message to send.

#### send\_message

```python
async def send_message(message)
```

Sends a message to the client.

**Arguments**:

- `message` - The message to send.

#### send

```python
async def send(data)
```

Sends data to the client.

**Arguments**:

- `data` - The data to send.

#### dispatch

```python
async def dispatch(action: str | None, data: dict)
```

Dispatches actions to the agent from the client.

#### get\_arg\_or\_default

```python
def get_arg_or_default(_args: dict, key: ConfigType) -> str
```

Gets an argument from the args dictionary or the default value.

**Arguments**:

- `_args` - The args dictionary.
- `key` - The key to get.
  

**Returns**:

  The value of the key or the default value.

#### create\_controller

```python
async def create_controller(start_event: dict)
```

Creates an AgentController instance.

**Arguments**:

- `start_event` - The start event data (optional).

#### start\_task

```python
async def start_task(start_event)
```

Starts a task for the agent.

**Arguments**:

- `start_event` - The start event data.

#### set\_task\_state

```python
async def set_task_state(new_state_action: TaskStateAction)
```

Sets the state of the agent task.

#### on\_agent\_event

```python
async def on_agent_event(event: Observation | Action)
```

Callback function for agent events.

**Arguments**:

- `event` - The agent event (Observation or Action).

