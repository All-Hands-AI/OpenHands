---
sidebar_label: action
title: opendevin.schema.action
---

## ActionTypeSchema Objects

```python
class ActionTypeSchema(BaseModel)
```

#### INIT

Initializes the agent. Only sent by client.

#### START

Starts a new development task. Only sent by the client.

#### READ

Reads the content of a file.

#### WRITE

Writes the content to a file.

#### RUN

Runs a command.

#### KILL

Kills a background command.

#### BROWSE

Opens a web page.

#### RECALL

Searches long-term memory

#### THINK

Allows the agent to make a plan, set a goal, or record thoughts

#### DELEGATE

Delegates a task to another agent.

#### FINISH

If you&#x27;re absolutely certain that you&#x27;ve completed your task and have tested your work,
use the finish action to stop working.

#### PAUSE

Pauses the task.

#### RESUME

Resumes the task.

#### STOP

Stops the task. Must send a start action to restart a new task.

