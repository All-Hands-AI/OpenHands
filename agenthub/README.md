# Agent Framework Research

In this folder, there may exist multiple implementations of `Agent` that will be used by the framework.

For example, `agenthub/monologue_agent`, `agenthub/metagpt_agent`, `agenthub/codeact_agent`, etc.
Contributors from different backgrounds and interests can choose to contribute to any (or all!) of these directions.

## Constructing an Agent

The abstraction for an agent can be found [here](../opendevin/agent.py).

Agents are run inside of a loop. At each iteration, `agent.step()` is called with a
[State](../opendevin/state.py) input, and the agent must output an [Action](../opendevin/action).

Every agent also has a `self.llm` which it can use to interact with the LLM configured by the user.
See the [LiteLLM docs for `self.llm.completion`](https://docs.litellm.ai/docs/completion).

## State

The `state` contains:

- A history of actions taken by the agent, as well as any observations (e.g. file content, command output) from those actions
- A list of actions/observations that have happened since the most recent step
- A [`root_task`](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/controller/state/task.py), which contains a plan of action
  - The agent can add and modify subtasks through the `AddTaskAction` and `ModifyTaskAction`

## Actions

Here is a list of available Actions, which can be returned by `agent.step()`:

- [`CmdRunAction`](../opendevin/action/bash.py) - Runs a command inside a sandboxed terminal
- [`CmdKillAction`](../opendevin/action/bash.py) - Kills a background command
- [`IPythonRunCellAction`](../opendevin/action/bash.py) - Execute a block of Python code interactively (in Jupyter notebook) and receives `CmdOutputObservation`. Requires setting up `jupyter` [plugin](../opendevin/sandbox/plugins) as a requirement.
- [`FileReadAction`](../opendevin/action/fileop.py) - Reads the content of a file
- [`FileWriteAction`](../opendevin/action/fileop.py) - Writes new content to a file
- [`BrowseURLAction`](../opendevin/action/browse.py) - Gets the content of a URL
- [`AgentRecallAction`](../opendevin/action/agent.py) - Searches memory (e.g. a vector database)
- [`AddTaskAction`](../opendevin/action/tasks.py) - Adds a subtask to the plan
- [`ModifyTaskAction`](../opendevin/action/tasks.py) - Changes the state of a subtask
- [`AgentThinkAction`](../opendevin/action/agent.py) - A no-op that allows the agent to add plaintext to the history (as well as the chat log)
- [`AgentTalkAction`](../opendevin/action/agent.py) - A no-op that allows the agent to add plaintext to the history and talk to the user.
- [`AgentFinishAction`](../opendevin/action/agent.py) - Stops the control loop, allowing the user/delegator agent to enter a new task
- [`AgentRejectAction`](../opendevin/action/agent.py) - Stops the control loop, allowing the user/delegator agent to enter a new task
- [`AgentFinishAction`](../opendevin/action/agent.py) - Stops the control loop, allowing the user to enter a new task
- [`MessageAction`](../opendevin/action/message.py) - Represents a message from an agent or the user

You can use `action.to_dict()` and `action_from_dict` to serialize and deserialize actions.

## Observations

There are also several types of Observations. These are typically available in the step following the corresponding Action.
But they may also appear as a result of asynchronous events (e.g. a message from the user, logs from a command running
in the background).

Here is a list of available Observations:

- [`CmdOutputObservation`](../opendevin/observation/run.py)
- [`BrowserOutputObservation`](../opendevin/observation/browse.py)
- [`FileReadObservation`](../opendevin/observation/files.py)
- [`FileWriteObservation`](../opendevin/observation/files.py)
- [`AgentRecallObservation`](../opendevin/observation/recall.py)
- [`ErrorObservation`](../opendevin/observation/error.py)
- [`SuccessObservation`](../opendevin/observation/success.py)

You can use `observation.to_dict()` and `observation_from_dict` to serialize and deserialize observations.

## Interface

Every agent must implement the following methods:

### `step`

```
def step(self, state: "State") -> "Action"
```

`step` moves the agent forward one step towards its goal. This probably means
sending a prompt to the LLM, then parsing the response into an `Action`.

### `search_memory`

```
def search_memory(self, query: str) -> list[str]:
```

`search_memory` should return a list of events that match the query. This will be used
for the `recall` action.

You can optionally just return `[]` for this method, meaning the agent has no long-term memory.
