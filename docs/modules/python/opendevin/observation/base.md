---
sidebar_label: base
title: opendevin.observation.base
---

## Observation Objects

```python
@dataclass
class Observation()
```

This data class represents an observation of the environment.

#### to\_dict

```python
def to_dict() -> dict
```

Converts the observation to a dictionary and adds user message.

#### to\_memory

```python
def to_memory() -> dict
```

Converts the observation to a dictionary.

#### message

```python
@property
def message() -> str
```

Returns a message describing the observation.

## NullObservation Objects

```python
@dataclass
class NullObservation(Observation)
```

This data class represents a null observation.
This is used when the produced action is NOT executable.

