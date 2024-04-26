---
sidebar_label: agent
title: SWE_agent.agent
---

## SWEAgent Objects

```python
class SWEAgent(Agent)
```

An attempt to recreate swe_agent with output parsing, prompting style, and Application Computer Interface (ACI).

SWE-agent includes ACI functions like &#x27;goto&#x27;, &#x27;search_for&#x27;, &#x27;edit&#x27;, &#x27;scroll&#x27;, &#x27;run&#x27;

#### step

```python
def step(state: State) -> Action
```

SWE-Agent step:
    1. Get context - past actions, custom commands, current step
    2. Perform think-act - prompt model for action and reasoning
    3. Catch errors - ensure model takes action (5 attempts max)

#### reset

```python
def reset() -> None
```

Used to reset the agent

