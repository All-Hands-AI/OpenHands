---
sidebar_label: agent
title: agenthub.monologue_agent.agent
---

## MonologueAgent Objects

```python
class MonologueAgent(Agent)
```

The Monologue Agent utilizes long and short term memory to complete tasks.
Long term memory is stored as a LongTermMemory object and the model uses it to search for examples from the past.
Short term memory is stored as a Monologue object and the model can condense it as necessary.

#### \_\_init\_\_

```python
def __init__(llm: LLM)
```

Initializes the Monologue Agent with an llm, monologue, and memory.

**Arguments**:

  - llm (LLM): The llm to be used by this agent

#### step

```python
def step(state: State) -> Action
```

Modifies the current state by adding the most recent actions and observations, then prompts the model to think about it&#x27;s next action to take using monologue, memory, and hint.

**Arguments**:

  - state (State): The current state based on previous steps taken
  

**Returns**:

  - Action: The next action to take based on LLM response

#### search\_memory

```python
def search_memory(query: str) -> List[str]
```

Uses VectorIndexRetriever to find related memories within the long term memory.
Uses search to produce top 10 results.

**Arguments**:

  - query (str): The query that we want to find related memories for
  

**Returns**:

  - List[str]: A list of top 10 text results that matched the query

