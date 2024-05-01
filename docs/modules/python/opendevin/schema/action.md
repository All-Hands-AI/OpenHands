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

#### USER\_MESSAGE

Sends a message from the user. Only sent by the client.

#### START

Starts a new development task OR send chat from the user. Only sent by the client.

#### READ

Reads the content of a file.

#### WRITE

Writes the content to a file.

#### RUN

Runs a command.

#### RUN\_IPYTHON

Runs a IPython cell.

#### KILL

Kills a background command.

#### BROWSE

Opens a web page.

#### RECALL

Searches long-term memory

#### THINK

Allows the agent to make a plan, set a goal, or record thoughts

#### TALK

Allows the agent to respond to the user.

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

#### PUSH

Push a branch to github.

#### SEND\_PR

Send a PR to github.

