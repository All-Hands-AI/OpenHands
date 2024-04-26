---
sidebar_label: prompts
title: monologue_agent.utils.prompts
---

#### get\_summarize\_monologue\_prompt

```python
def get_summarize_monologue_prompt(thoughts: List[dict])
```

Gets the prompt for summarizing the monologue

**Returns**:

  - str: A formatted string with the current monologue within the prompt

#### get\_request\_action\_prompt

```python
def get_request_action_prompt(
        task: str,
        thoughts: List[dict],
        background_commands_obs: List[CmdOutputObservation] = [])
```

Gets the action prompt formatted with appropriate values.

**Arguments**:

  - task (str): The current task the agent is trying to accomplish
  - thoughts (List[dict]): The agent&#x27;s current thoughts
  - background_commands_obs (List[CmdOutputObservation]): List of all observed background commands running
  

**Returns**:

  - str: Formatted prompt string with hint, task, monologue, and background included

#### parse\_action\_response

```python
def parse_action_response(response: str) -> Action
```

Parses a string to find an action within it

**Arguments**:

  - response (str): The string to be parsed
  

**Returns**:

  - Action: The action that was found in the response string

#### parse\_summary\_response

```python
def parse_summary_response(response: str) -> List[dict]
```

Parses a summary of the monologue

**Arguments**:

  - response (str): The response string to be parsed
  

**Returns**:

  - List[dict]: The list of summaries output by the model

