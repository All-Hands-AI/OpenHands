# Agent Hub

In this folder, there may exist multiple implementations of `Agent` that will be used by the framework.

For example, `agenthub/codeact_agent`, etc.
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
- A [`root_task`](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/controller/state/task.py), which contains a plan of action
  - The agent can add and modify subtasks through the `AddTaskAction` and `ModifyTaskAction`

## Actions

Here is a list of available Actions, which can be returned by `agent.step()`:

- [`CmdRunAction`](../opendevin/events/action/commands.py) - Runs a command inside a sandboxed terminal
- [`IPythonRunCellAction`](../opendevin/events/action/commands.py) - Execute a block of Python code interactively (in Jupyter notebook) and receives `CmdOutputObservation`. Requires setting up `jupyter` [plugin](../opendevin/runtime/plugins) as a requirement.
- [`FileReadAction`](../opendevin/events/action/files.py) - Reads the content of a file
- [`FileWriteAction`](../opendevin/events/action/files.py) - Writes new content to a file
- [`BrowseURLAction`](../opendevin/events/action/browse.py) - Gets the content of a URL
- [`AddTaskAction`](../opendevin/events/action/tasks.py) - Adds a subtask to the plan
- [`ModifyTaskAction`](../opendevin/events/action/tasks.py) - Changes the state of a subtask.
- [`AgentFinishAction`](../opendevin/events/action/agent.py) - Stops the control loop, allowing the user/delegator agent to enter a new task
- [`AgentRejectAction`](../opendevin/events/action/agent.py) - Stops the control loop, allowing the user/delegator agent to enter a new task
- [`AgentFinishAction`](../opendevin/events/action/agent.py) - Stops the control loop, allowing the user to enter a new task
- [`MessageAction`](../opendevin/events/action/message.py) - Represents a message from an agent or the user

You can use `action.to_dict()` and `action_from_dict` to serialize and deserialize actions.

## Observations

There are also several types of Observations. These are typically available in the step following the corresponding Action.
But they may also appear as a result of asynchronous events (e.g. a message from the user).

Here is a list of available Observations:

- [`CmdOutputObservation`](../opendevin/events/observation/commands.py)
- [`BrowserOutputObservation`](../opendevin/events/observation/browse.py)
- [`FileReadObservation`](../opendevin/events/observation/files.py)
- [`FileWriteObservation`](../opendevin/events/observation/files.py)
- [`ErrorObservation`](../opendevin/events/observation/error.py)
- [`SuccessObservation`](../opendevin/events/observation/success.py)

You can use `observation.to_dict()` and `observation_from_dict` to serialize and deserialize observations.

## Interface

Every agent must implement the following methods:

### `step`

```
def step(self, state: "State") -> "Action"
```

`step` moves the agent forward one step towards its goal. This probably means
sending a prompt to the LLM, then parsing the response into an `Action`.
