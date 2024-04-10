# Agents and Capabilities

## Monologue Agent:

### Description:
The Monologue Agent utilizes long and short term memory to complete tasks.
Long term memory is stored as a LongTermMemory object and the model uses it to search for examples from the past.
Short term memory is stored as a Monologue object and the model can condense it as necessary.

### Actions:
`Action`,
`NullAction`,
`CmdRunAction`,
`FileWriteAction`,
`FileReadAction`,
`AgentRecallAction`,
`BrowseURLAction`,
`AgentThinkAction`

### Observations:
`Observation`,
`NullObservation`,
`CmdOutputObservation`,
`FileReadObservation`,
`AgentRecallObservation`,
`BrowserOutputObservation`


### Methods:
`__init__`: Initializes the agent with a long term memory, and an internal monologue

`_add_event`: Appends events to the monologue of the agent and condenses with summary automatically if the monologue is too long

`_initialize`: Utilizes the `INITIAL_THOUGHTS` list to give the agent a context for its capabilities and how to navigate the `/workspace`

`step`: Modifies the current state by adding the most rescent actions and observations, then prompts the model to think about its next action to take. 

`search_memory`: Uses `VectorIndexRetriever` to find related memories within the long term memory.

## Planner Agent:

### Description:
The planner agent utilizes a special prompting strategy to create long term plans for solving problems.
The agent is given its previous action-observation pairs, current task, and hint based on last action taken at every step.

### Actions:
`NullAction`,
`CmdRunAction`,
`CmdKillAction`,
`BrowseURLAction`,
`FileReadAction`,
`FileWriteAction`,
`AgentRecallAction`,
`AgentThinkAction`,
`AgentFinishAction`,
`AgentSummarizeAction`,
`AddTaskAction`,
`ModifyTaskAction`,


### Observations:
`Observation`,
`NullObservation`,
`CmdOutputObservation`,
`FileReadObservation`,
`AgentRecallObservation`,
`BrowserOutputObservation`

### Methods:
`__init__`: Initializes an agent with `llm`

`step`: Checks to see if current step is completed, returns `AgentFinishAction` if True. Otherwise, creates a plan prompt and sends to model for inference, adding the result as the next action.

`search_memory`: Not yet implemented

## CodeAct Agent:

### Description:
The Code Act Agent is a minimalist agent. The agent works by passing the model a list of action-observaiton pairs and prompting the model to take the next step.

### Actions:
`Action`,
`CmdRunAction`,
`AgentEchoAction`,
`AgentFinishAction`,

### Observations:
`CmdOutputObservation`,
`AgentMessageObservation`,

### Methods:
`__init__`: Initializes an agent with `llm` and a list of messages `List[Mapping[str, str]]`

`step`: First, gets messages from state and then compiles them into a list for context. Next, pass the context list with the prompt to get the next command to execute. Finally, Execute command if valid, else return `AgentEchoAction(INVALID_INPUT_MESSAGE)` 

`search_memory`: Not yet implemented