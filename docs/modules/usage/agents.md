---
sidebar_position: 3
---

# 🧠 Agents and Capabilities

## CodeAct Agent

### Description

This agent implements the CodeAct idea ([paper](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) that consolidates LLM agents’ **act**ions into a unified **code** action space for both _simplicity_ and _performance_ (see paper for more details).

The conceptual idea is illustrated below. At each turn, the agent can:

1. **Converse**: Communicate with humans in natural language to ask for clarification, confirmation, etc.
2. **CodeAct**: Choose to perform the task by executing code

- Execute any valid Linux `bash` command
- Execute any valid `Python` code with [an interactive Python interpreter](https://ipython.org/). This is simulated through `bash` command, see plugin system below for more details.

![image](https://github.com/OpenDevin/OpenDevin/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### Plugin System

To make the CodeAct agent more powerful with only access to `bash` action space, CodeAct agent leverages OpenDevin&#x27;s plugin system:

- [Jupyter plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/jupyter): for IPython execution via bash command
- [SWE-agent tool plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/swe_agent_commands): Powerful bash command line tools for software development tasks introduced by [swe-agent](https://github.com/princeton-nlp/swe-agent).

### Demo

https://github.com/OpenDevin/OpenDevin/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

_Example of CodeActAgent with `gpt-4-turbo-2024-04-09` performing a data science task (linear regression)_

### Actions

`Action`,
`CmdRunAction`,
`IPythonRunCellAction`,
`AgentEchoAction`,
`AgentFinishAction`,
`AgentTalkAction`

### Observations

`CmdOutputObservation`,
`IPythonRunCellObservation`,
`AgentMessageObservation`,
`UserMessageObservation`

### Methods

| Method          | Description                                                                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__`      | Initializes an agent with `llm` and a list of messages `list[Mapping[str, str]]`                                                                |
| `step`          | Performs one step using the CodeAct Agent. This includes gathering info on previous steps and prompting the model to make a command to execute. |
| `search_memory` | Not yet implemented                                                                                                                             |

### Work-in-progress &amp; Next step

[] Support web-browsing
[] Complete the workflow for CodeAct agent to submit Github PRs

## Monologue Agent

### Description

The Monologue Agent utilizes long and short term memory to complete tasks.
Long term memory is stored as a LongTermMemory object and the model uses it to search for examples from the past.
Short term memory is stored as a Monologue object and the model can condense it as necessary.

### Actions

`Action`,
`NullAction`,
`CmdRunAction`,
`FileWriteAction`,
`FileReadAction`,
`AgentRecallAction`,
`BrowseURLAction`,
`GithubPushAction`,
`AgentThinkAction`

### Observations

`Observation`,
`NullObservation`,
`CmdOutputObservation`,
`FileReadObservation`,
`AgentRecallObservation`,
`BrowserOutputObservation`

### Methods

| Method          | Description                                                                                                                                   |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__`      | Initializes the agent with a long term memory, and an internal monologue                                                                      |
| `_add_event`    | Appends events to the monologue of the agent and condenses with summary automatically if the monologue is too long                            |
| `_initialize`   | Utilizes the `INITIAL_THOUGHTS` list to give the agent a context for its capabilities and how to navigate the `/workspace`                    |
| `step`          | Modifies the current state by adding the most recent actions and observations, then prompts the model to think about its next action to take. |
| `search_memory` | Uses `VectorIndexRetriever` to find related memories within the long term memory.                                                             |

## Planner Agent

### Description

The planner agent utilizes a special prompting strategy to create long term plans for solving problems.
The agent is given its previous action-observation pairs, current task, and hint based on last action taken at every step.

### Actions

`NullAction`,
`CmdRunAction`,
`CmdKillAction`,
`BrowseURLAction`,
`GithubPushAction`,
`FileReadAction`,
`FileWriteAction`,
`AgentRecallAction`,
`AgentThinkAction`,
`AgentFinishAction`,
`AgentSummarizeAction`,
`AddTaskAction`,
`ModifyTaskAction`,

### Observations

`Observation`,
`NullObservation`,
`CmdOutputObservation`,
`FileReadObservation`,
`AgentRecallObservation`,
`BrowserOutputObservation`

### Methods

| Method          | Description                                                                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__`      | Initializes an agent with `llm`                                                                                                                                                           |
| `step`          | Checks to see if current step is completed, returns `AgentFinishAction` if True. Otherwise, creates a plan prompt and sends to model for inference, adding the result as the next action. |
| `search_memory` | Not yet implemented                                                                                                                                                                       |
