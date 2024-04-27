---
sidebar_label: task
title: opendevin.schema.task
---

## TaskState Objects

```python
class TaskState(str, Enum)
```

#### INIT

Initial state of the task.

#### RUNNING

The task is running.

#### PAUSED

The task is paused.

#### STOPPED

The task is stopped.

#### FINISHED

The task is finished.

#### ERROR

An error occurred during the task.

## TaskStateAction Objects

```python
class TaskStateAction(str, Enum)
```

#### START

Starts the task.

#### PAUSE

Pauses the task.

#### RESUME

Resumes the task.

#### STOP

Stops the task.

