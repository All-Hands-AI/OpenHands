# Agent Hub

In this folder, there may exist multiple implementations of `Agent` that will be used by the framework.

For example, `agenthub/codeact_agent`, etc.
Contributors from different backgrounds and interests can choose to contribute to any (or all!) of these directions.

## Constructing an Agent

The abstraction for an agent can be found [here](../openhands/controller/agent.py).

Agents are run inside of a loop. At each iteration, `agent.step()` is called with a
[State](../openhands/controller/state/state.py) input, and the agent must output an [Action](../openhands/events/action).

Every agent also has a `self.llm` which it can use to interact with the LLM configured by the user.
See the [LiteLLM docs for `self.llm.completion`](https://docs.litellm.ai/docs/completion).

## State

The `state` contains:

- A history of actions taken by the agent, as well as any observations (e.g. file content, command output) from those actions
- A list of actions/observations that have happened since the most recent step
- A [`root_task`](https://github.com/Open Hands/Open Hands/blob/main/openhands/controller/state/task.py), which contains a plan of action
  - The agent can add and modify subtasks through the `AddTaskAction` and `ModifyTaskAction`

## Actions

Here is a list of available Actions, which can be returned by `agent.step()`:

- [`CmdRunAction`](../openhands/events/action/commands.py) - Runs a command inside a sandboxed terminal
- [`IPythonRunCellAction`](../openhands/events/action/commands.py) - Execute a block of Python code interactively (in Jupyter notebook) and receives `CmdOutputObservation`. Requires setting up `jupyter` [plugin](../openhands/runtime/plugins) as a requirement.
- [`FileReadAction`](../openhands/events/action/files.py) - Reads the content of a file
- [`FileWriteAction`](../openhands/events/action/files.py) - Writes new content to a file
- [`BrowseURLAction`](../openhands/events/action/browse.py) - Gets the content of a URL
- [`AddTaskAction`](../openhands/events/action/tasks.py) - Adds a subtask to the plan
- [`ModifyTaskAction`](../openhands/events/action/tasks.py) - Changes the state of a subtask.
- [`AgentFinishAction`](../openhands/events/action/agent.py) - Stops the control loop, allowing the user/delegator agent to enter a new task
- [`AgentRejectAction`](../openhands/events/action/agent.py) - Stops the control loop, allowing the user/delegator agent to enter a new task
- [`AgentFinishAction`](../openhands/events/action/agent.py) - Stops the control loop, allowing the user to enter a new task
- [`MessageAction`](../openhands/events/action/message.py) - Represents a message from an agent or the user

You can use `action.to_dict()` and `action_from_dict` to serialize and deserialize actions.

## Observations

There are also several types of Observations. These are typically available in the step following the corresponding Action.
But they may also appear as a result of asynchronous events (e.g. a message from the user).

Here is a list of available Observations:

- [`CmdOutputObservation`](../openhands/events/observation/commands.py)
- [`BrowserOutputObservation`](../openhands/events/observation/browse.py)
- [`FileReadObservation`](../openhands/events/observation/files.py)
- [`FileWriteObservation`](../openhands/events/observation/files.py)
- [`ErrorObservation`](../openhands/events/observation/error.py)
- [`SuccessObservation`](../openhands/events/observation/success.py)

You can use `observation.to_dict()` and `observation_from_dict` to serialize and deserialize observations.

## Interface

Every agent must implement the following methods:

### `step`

```
def step(self, state: "State") -> "Action"
```

`step` moves the agent forward one step towards its goal. This probably means
sending a prompt to the LLM, then parsing the response into an `Action`.
