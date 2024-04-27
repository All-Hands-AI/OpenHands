---
sidebar_label: main
title: opendevin.main
---

#### read\_task\_from\_file

```python
def read_task_from_file(file_path: str) -> str
```

Read task from the specified file.

#### read\_task\_from\_stdin

```python
def read_task_from_stdin() -> str
```

Read task from stdin.

#### main

```python
async def main(task_str: str = '')
```

Main coroutine to run the agent controller with task input flexibility.

