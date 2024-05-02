---
sidebar_label: agent_controller
title: opendevin.controller.agent_controller
---

## AgentController Objects

```python
class AgentController()
```

#### \_\_init\_\_

```python
def __init__(agent: Agent,
             sid: str = 'default',
             max_iterations: int = MAX_ITERATIONS,
             max_chars: int = MAX_CHARS,
             callbacks: List[Callable] = [])
```

Initializes a new instance of the AgentController class.

**Arguments**:

- `agent` - The agent instance to control.
- `sid` - The session ID of the agent.
- `max_iterations` - The maximum number of iterations the agent can run.
- `max_chars` - The maximum number of characters the agent can output.
- `callbacks` - A list of callback functions to run after each action.

#### setup\_task

```python
async def setup_task(task: str, inputs: dict = {})
```

Sets up the agent controller with a task.

#### start

```python
async def start(task: str)
```

Starts the agent controller with a task.
If task already run before, it will continue from the last step.

#### get\_task\_state

```python
def get_task_state()
```

Returns the current state of the agent task.

