---
sidebar_label: agent_controller
title: controller.agent_controller
---

## AgentController Objects

```python
class AgentController()
```

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

