---
sidebar_label: agent
title: agenthub.delegator_agent.agent
---

## DelegatorAgent Objects

```python
class DelegatorAgent(Agent)
```

The planner agent utilizes a special prompting strategy to create long term plans for solving problems.
The agent is given its previous action-observation pairs, current task, and hint based on last action taken at every step.

#### \_\_init\_\_

```python
def __init__(llm: LLM)
```

Initialize the Delegator Agent with an LLM

**Arguments**:

  - llm (LLM): The llm to be used by this agent

#### step

```python
def step(state: State) -> Action
```

Checks to see if current step is completed, returns AgentFinishAction if True.
Otherwise, creates a plan prompt and sends to model for inference, returning the result as the next action.

**Arguments**:

  - state (State): The current state given the previous actions and observations
  

**Returns**:

  - AgentFinishAction: If the last state was &#x27;completed&#x27;, &#x27;verified&#x27;, or &#x27;abandoned&#x27;
  - Action: The next action to take based on llm response

