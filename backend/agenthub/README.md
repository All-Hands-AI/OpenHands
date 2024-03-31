# Agent Framework Research

In this folder, there may exist multiple implementations of `Agent` that will be used by the 

For example, `agenthub/langchain_agent`, `agenthub/metagpt_agent`, `agenthub/codeact_agent`, etc.
Contributors from different backgrounds and interests can choose to contribute to any (or all!) of these directions.

## Constructing an Agent

The abstraction for an agent can be found [here](../opendevin/agent.py).

On a high-level, at each step, an agent takes in a [State](../opendevin/state.py) object and outputs an [Action](../opendevin/action).

Your agent must implement the following methods:

### `step`
```
def step(self, state: "State") -> "Action"
```
`step` moves the agent forward one step towards its goal. This probably means
sending a prompt to the LLM, then parsing the response into an `Action`.

We now have [two main categories of actions](../opendevin/action/base.py):
- `ExecutableAction`: will produces a corresponding `Observation` (source [here](../opendevin/observation.py)) for the agent to take the next `Action`.
- `NotExecutableAction`: will produces a `NullObservation` by the [controller](../opendevin/controller/__init__.py), which could means telling the agent to ignore this action.

For `ExecutableAction`, we currently have:
- `CmdRunAction` and `CmdKillAction` for bash command (see source [here](../opendevin/action/bash.py)).
- `FileReadAction` and `FileWriteAction` for file operations (see source [here](../opendevin/action/fileop.py)).
- `BrowseURLAction` to open a web page (see source [here](../opendevin/action/browse.py)).
- `AgentThinkAction`, `AgentFinishAction`: these are non-executable actions for agent to update its status to the user. For example, agent could use `AgentThink` to explain its though process to the user (see source [here](../opendevin/action/agent.py)).
- `AgentEchoAction`: the agent can produce some messages as its own Observation in the next `.step`, this will produces a `AgentMessageObservation` (see source [here](../opendevin/action/agent.py)).
- `AgentRecallAction`: recalls a past memory (see source [here](../opendevin/action/agent.py)).

### `search_memory`
```
def search_memory(self, query: str) -> List[str]:
```
`search_memory` should return a list of events that match the query. This will be used
for the `recall` action.
