---
sidebar_label: agent
title: opendevin.agent
---

## Agent Objects

```python
class Agent(ABC)
```

This abstract base class is an general interface for an agent dedicated to
executing a specific instruction and allowing human interaction with the
agent during execution.
It tracks the execution status and maintains a history of interactions.

#### complete

```python
@property
def complete() -> bool
```

Indicates whether the current instruction execution is complete.

**Returns**:

  - complete (bool): True if execution is complete; False otherwise.

#### step

```python
@abstractmethod
def step(state: 'State') -> 'Action'
```

Starts the execution of the assigned instruction. This method should
be implemented by subclasses to define the specific execution logic.

#### search\_memory

```python
@abstractmethod
def search_memory(query: str) -> List[str]
```

Searches the agent&#x27;s memory for information relevant to the given query.

**Arguments**:

  - query (str): The query to search for in the agent&#x27;s memory.
  

**Returns**:

  - response (str): The response to the query.

#### reset

```python
def reset() -> None
```

Resets the agent&#x27;s execution status and clears the history. This method can be used
to prepare the agent for restarting the instruction or cleaning up before destruction.

#### register

```python
@classmethod
def register(cls, name: str, agent_cls: Type['Agent'])
```

Registers an agent class in the registry.

**Arguments**:

  - name (str): The name to register the class under.
  - agent_cls (Type[&#x27;Agent&#x27;]): The class to register.
  

**Raises**:

  - AgentAlreadyRegisteredError: If name already registered

#### get\_cls

```python
@classmethod
def get_cls(cls, name: str) -> Type['Agent']
```

Retrieves an agent class from the registry.

**Arguments**:

  - name (str): The name of the class to retrieve
  

**Returns**:

  - agent_cls (Type[&#x27;Agent&#x27;]): The class registered under the specified name.
  

**Raises**:

  - AgentNotRegisteredError: If name not registered

#### list\_agents

```python
@classmethod
def list_agents(cls) -> list[str]
```

Retrieves the list of all agent names from the registry.

**Raises**:

  - AgentNotRegisteredError: If no agent is registered

