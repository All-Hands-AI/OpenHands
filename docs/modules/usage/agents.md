# 🧠 Agents and Capabilities

## CodeAct Agent

### Description

The CodeAct agent implements the CodeAct idea ([paper](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) that consolidates LLM agents' **actions** into a unified **code** action space for both _simplicity_ and _performance_.

At each turn, the agent can:

1. **Converse**: Communicate with humans in natural language.
2. **CodeAct**: Perform tasks by executing code:
   - Execute any valid Linux `bash` command
   - Execute any valid `Python` code with an interactive Python interpreter (simulated through `bash` commands)

![CodeAct Concept](https://github.com/OpenDevin/OpenDevin/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### Plugin System

The CodeAct agent uses OpenDevin's plugin system:

- [Jupyter plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/jupyter): for IPython execution via bash command
- [SWE-agent tool plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/swe_agent_commands): Powerful bash command line tools for software development tasks

### Demo

[CodeActAgent Demo Video](https://github.com/OpenDevin/OpenDevin/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac)

### Components

#### Actions
- `Action`, `CmdRunAction`, `IPythonRunCellAction`, `AgentEchoAction`, `AgentFinishAction`, `AgentTalkAction`

#### Observations
- `CmdOutputObservation`, `IPythonRunCellObservation`, `AgentMessageObservation`, `UserMessageObservation`

#### Methods

| Method          | Description                                                                                     |
|------------------|-------------------------------------------------------------------------------------------------|
| `__init__`       | Initializes an agent with `llm` and a list of messages `list[Mapping[str, str]]`                |
| `step`           | Performs one step using the CodeAct Agent                                                       |
| `search_memory`  | Not yet implemented                                                                             |

### Work-in-progress & Next Steps

- [ ] Support web-browsing
- [ ] Complete the workflow for CodeAct agent to submit Github PRs

## Monologue Agent

### Description

The Monologue Agent uses long and short-term memory to complete tasks:
- Long-term memory: stored as a `LongTermMemory` object
- Short-term memory: stored as a `Monologue` object (can be condensed as needed)

### Components

#### Actions
- `Action`, `NullAction`, `CmdRunAction`, `FileWriteAction`, `FileReadAction`, `AgentRecallAction`, `BrowseURLAction`, `GithubPushAction`, `AgentThinkAction`

#### Observations
- `Observation`, `NullObservation`, `CmdOutputObservation`, `FileReadObservation`, `AgentRecallObservation`, `BrowserOutputObservation`

#### Methods

| Method          | Description                                                                                     |
|------------------|-------------------------------------------------------------------------------------------------|
| `__init__`       | Initializes the agent with long-term memory and internal monologue                              |
| `_add_event`     | Appends events to the monologue and condenses with summary if too long                          |
| `_initialize`    | Uses `INITIAL_THOUGHTS` to provide context for capabilities and navigating `/workspace`         |
| `step`           | Modifies current state and prompts model for next action                                        |
| `search_memory`  | Uses `VectorIndexRetriever` to find related memories in long-term memory                        |

## Planner Agent

### Description

The Planner Agent uses a special prompting strategy to create long-term plans for problem-solving. It receives:
- Previous action-observation pairs
- Current task
- Hint based on the last action taken

### Components

#### Actions
- `NullAction`, `CmdRunAction`, `CmdKillAction`, `BrowseURLAction`, `GithubPushAction`, `FileReadAction`, `FileWriteAction`, `AgentRecallAction`, `AgentThinkAction`, `AgentFinishAction`, `AgentSummarizeAction`, `AddTaskAction`, `ModifyTaskAction`

#### Observations
- `Observation`, `NullObservation`, `CmdOutputObservation`, `FileReadObservation`, `AgentRecallObservation`, `BrowserOutputObservation`

#### Methods

| Method          | Description                                                                                     |
|------------------|-------------------------------------------------------------------------------------------------|
| `__init__`       | Initializes an agent with `llm`                                                                 |
| `step`           | Checks if current step is completed, creates a plan prompt, and determines next action          |
| `search_memory`  | Not yet implemented                                                                             |