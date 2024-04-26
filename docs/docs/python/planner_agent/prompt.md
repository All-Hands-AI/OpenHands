---
sidebar_label: prompt
title: planner_agent.prompt
---

#### get\_hint

```python
def get_hint(latest_action_id: str) -> str
```

Returns action type hint based on given action_id

#### get\_prompt

```python
def get_prompt(plan: Plan, history: List[Tuple[Action, Observation]]) -> str
```

Gets the prompt for the planner agent.
Formatted with the most recent action-observation pairs, current task, and hint based on last action

**Arguments**:

  - plan (Plan): The original plan outlined by the user with LLM defined tasks
  - history (List[Tuple[Action, Observation]]): List of corresponding action-observation pairs
  

**Returns**:

  - str: The formatted string prompt with historical values

#### parse\_response

```python
def parse_response(response: str) -> Action
```

Parses the model output to find a valid action to take

**Arguments**:

  - response (str): A response from the model that potentially contains an Action.
  

**Returns**:

  - Action: A valid next action to perform from model output

