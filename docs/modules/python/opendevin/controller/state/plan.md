---
sidebar_label: plan
title: opendevin.controller.state.plan
---

## Task Objects

```python
class Task()
```

#### \_\_init\_\_

```python
def __init__(parent: 'Task | None',
             goal: str,
             state: str = OPEN_STATE,
             subtasks: List = [])
```

Initializes a new instance of the Task class.

**Arguments**:

- `parent` - The parent task, or None if it is the root task.
- `goal` - The goal of the task.
- `state` - The initial state of the task.
- `subtasks` - A list of subtasks associated with this task.

#### to\_string

```python
def to_string(indent='')
```

Returns a string representation of the task and its subtasks.

**Arguments**:

- `indent` - The indentation string for formatting the output.
  

**Returns**:

  A string representation of the task and its subtasks.

#### to\_dict

```python
def to_dict()
```

Returns a dictionary representation of the task.

**Returns**:

  A dictionary containing the task&#x27;s attributes.

#### set\_state

```python
def set_state(state)
```

Sets the state of the task and its subtasks.

Args:            state: The new state of the task.

**Raises**:

- `PlanInvalidStateError` - If the provided state is invalid.

#### get\_current\_task

```python
def get_current_task() -> 'Task | None'
```

Retrieves the current task in progress.

**Returns**:

  The current task in progress, or None if no task is in progress.

## Plan Objects

```python
class Plan()
```

Represents a plan consisting of tasks.

**Attributes**:

- `main_goal` - The main goal of the plan.
- `task` - The root task of the plan.

#### \_\_init\_\_

```python
def __init__(task: str)
```

Initializes a new instance of the Plan class.

**Arguments**:

- `task` - The main goal of the plan.

#### \_\_str\_\_

```python
def __str__()
```

Returns a string representation of the plan.

**Returns**:

  A string representation of the plan.

#### get\_task\_by\_id

```python
def get_task_by_id(id: str) -> Task
```

Retrieves a task by its ID.

**Arguments**:

- `id` - The ID of the task.
  

**Returns**:

  The task with the specified ID.
  

**Raises**:

- `ValueError` - If the provided task ID is invalid or does not exist.

#### add\_subtask

```python
def add_subtask(parent_id: str, goal: str, subtasks: List = [])
```

Adds a subtask to a parent task.

**Arguments**:

- `parent_id` - The ID of the parent task.
- `goal` - The goal of the subtask.
- `subtasks` - A list of subtasks associated with the new subtask.

#### set\_subtask\_state

```python
def set_subtask_state(id: str, state: str)
```

Sets the state of a subtask.

**Arguments**:

- `id` - The ID of the subtask.
- `state` - The new state of the subtask.

#### get\_current\_task

```python
def get_current_task()
```

Retrieves the current task in progress.

**Returns**:

  The current task in progress, or None if no task is in progress.

