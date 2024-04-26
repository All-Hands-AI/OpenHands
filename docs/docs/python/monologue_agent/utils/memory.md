---
sidebar_label: memory
title: monologue_agent.utils.memory
---

## LongTermMemory Objects

```python
class LongTermMemory()
```

Responsible for storing information that the agent can call on later for better insights and context.
Uses chromadb to store and search through memories.

#### \_\_init\_\_

```python
def __init__()
```

Initialize the chromadb and set up ChromaVectorStore for later use.

#### add\_event

```python
def add_event(event: dict)
```

Adds a new event to the long term memory with a unique id.

**Arguments**:

  - event (dict): The new event to be added to memory

#### search

```python
def search(query: str, k: int = 10)
```

Searches through the current memory using VectorIndexRetriever

**Arguments**:

  - query (str): A query to match search results to
  - k (int): Number of top results to return
  

**Returns**:

  - List[str]: List of top k results found in current memory

