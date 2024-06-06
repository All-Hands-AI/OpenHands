# Agent Framework Research

In this folder, there may exist multiple implementations of `Agent` that will be used by the framework.

For example, `agenthub/monologue_agent`, `agenthub/metagpt_agent`, `agenthub/codeact_agent`, etc.
Contributors from different backgrounds and interests can choose to contribute to any (or all!) of these directions.

## Constructing an Agent

The abstraction for an agent can be found [here](../opendevin/controller/agent.py).

Agents are run inside of a loop. At each iteration, `agent.step()` is called with a
[State](../opendevin/controller/state/state.py) input, and the agent must output an [Action](../opendevin/events/action).

Every agent also has a `self.llm` which it can use to interact with the LLM configured by the user.
See the [LiteLLM docs for `self.llm.completion`](https://docs.litellm.ai/docs/completion).

## State

The `state` contains:

- A history of actions taken by the agent, as well as any observations (e.g. file content, command output) from those actions
- A list of actions/observations that have happened since the most recent step
- A [`root_task`](../opendevin/controller/state/task.py), which contains a plan of action
  - The agent can add and modify subtasks through the `AddTaskAction` and `ModifyTaskAction`

## Actions

Here is a list of some of the available Actions, which can be returned by `agent.step()`:

- [General Commands](../opendevin/events/action/commands.py)
  - `CmdRunAction` - Runs a command inside a sandboxed terminal
  - `CmdKillAction` - Kills a background command
  - `IPythonRunCellAction` - Execute a block of Python code interactively (in Jupyter notebook) and receives `CmdOutputObservation`. Requires setting up `jupyter` [plugin](../opendevin/sandbox/plugins) as a requirement.
- [File Editing](../opendevin/events/action/files.py)
  - `FileReadAction` - Reads the content of a file
  - `FileWriteAction` - Writes new content to a file
- [Tasks](../opendevin/action/tasks.py)
  - `AddTaskAction` - Adds a subtask to the plan
  - `ModifyTaskAction` - Changes the state of a subtask
- [Agent](../opendevin/action/agent.py)
  - `AgentRecallAction` - Searches memory (e.g. a vector database)
  - `AgentThinkAction` - A no-op that allows the agent to add plaintext to the history (as well as the chat log)
  - `AgentTalkAction` - A no-op that allows the agent to add plaintext to the history and talk to the user.
  - `AgentFinishAction` - Stops the control loop, allowing the user/delegator agent to enter a new task
  - `AgentRejectAction` - Stops the control loop, allowing the user/delegator agent to enter a new task
  - `AgentFinishAction` - Stops the control loop, allowing the user to enter a new task
- Other
  - [`MessageAction`](../opendevin/action/message.py) - Represents a message from an agent or the user
  - [`BrowseURLAction`](../opendevin/action/browse.py) - Gets the content of a URL

You can use `action.to_dict()` and `action_from_dict` to serialize and deserialize actions.

## Observations

There are also several types of Observations. These are typically available in the step following the corresponding Action.
But they may also appear as a result of asynchronous events (e.g. a message from the user, logs from a command running
in the background).

Here is a list of some of the available Observations:

- [`CmdOutputObservation`](../opendevin/events/observation/commands.py)
- [`BrowserOutputObservation`](../opendevin/events/observation/browse.py)
- [`FileReadObservation`](../opendevin/events/observation/files.py)
- [`FileWriteObservation`](../opendevin/events/observation/files.py)
- [`AgentRecallObservation`](../opendevin/events/observation/recall.py)
- [`ErrorObservation`](../opendevin/events/observation/error.py)
- [`SuccessObservation`](../opendevin/events/observation/success.py)

You can use `observation.to_dict()` and `observation_from_dict` to serialize and deserialize observations.

## Interface

Every agent must implement the following methods:

### `step`

```py
def step(self, state: "State") -> "Action"
```

`step` moves the agent forward one step towards its goal. This probably means
sending a prompt to the LLM, then parsing the response into an `Action`.

### `search_memory`

```py
def search_memory(self, query: str) -> list[str]:
```

`search_memory` should return a list of events that match the query. This will be used
for the `recall` action.

You can optionally just return `[]` for this method, meaning the agent has no long-term memory.
