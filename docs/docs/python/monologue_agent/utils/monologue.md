---
sidebar_label: monologue
title: monologue_agent.utils.monologue
---

## Monologue Objects

```python
class Monologue()
```

The monologue is a representation for the agent&#x27;s internal monologue where it can think.
The agent has the capability of using this monologue for whatever it wants.

#### \_\_init\_\_

```python
def __init__()
```

Initialize the empty list of thoughts

#### add\_event

```python
def add_event(t: dict)
```

Adds an event to memory if it is a valid event.

**Arguments**:

  - t (dict): The thought that we want to add to memory
  

**Raises**:

  - AgentEventTypeError: If t is not a dict

#### get\_thoughts

```python
def get_thoughts()
```

Get the current thoughts of the agent.

**Returns**:

  - List: The list of thoughts that the agent has.

#### get\_total\_length

```python
def get_total_length()
```

Gives the total number of characters in all thoughts

**Returns**:

  - Int: Total number of chars in thoughts.

#### condense

```python
def condense(llm: LLM)
```

Attempts to condense the monologue by using the llm

**Arguments**:

  - llm (LLM): llm to be used for summarization
  

**Raises**:

  - Exception: the same exception as it got from the llm or processing the response

