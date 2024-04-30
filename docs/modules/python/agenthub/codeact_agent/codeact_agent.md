---
sidebar_label: codeact_agent
title: agenthub.codeact_agent.codeact_agent
---

## CodeActAgent Objects

```python
class CodeActAgent(Agent)
```

The Code Act Agent is a minimalist agent.
The agent works by passing the model a list of action-observation pairs and prompting the model to take the next step.

#### \_\_init\_\_

```python
def __init__(llm: LLM) -> None
```

Initializes a new instance of the CodeActAgent class.

**Arguments**:

  - llm (LLM): The llm to be used by this agent

#### step

```python
def step(state: State) -> Action
```

Performs one step using the Code Act Agent.
This includes gathering info on previous steps and prompting the model to make a command to execute.

**Arguments**:

  - state (State): used to get updated info and background commands
  

**Returns**:

  - CmdRunAction(command) - command action to run
  - AgentEchoAction(content=INVALID_INPUT_MESSAGE) - invalid command output
  

**Raises**:

  - NotImplementedError - for actions other than CmdOutputObservation or AgentMessageObservation

