# Agents and Capabilities

## Monologue Agent:

### Description:
Responsible for talking to the user and acting as an overall manager of the project. The monologue agent has a long term memory that it is capable of modifying to suit its current needs. This agent is mostly responsible for managing state and long term memory.

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
`__init__`: Initilizes the agent with a long term memory, and an internal monologue

`_add_event`: Appends events to the monologue of the agent and condenses with summary automatically if the monlogue is too long

`_initilize`: Utilizes the `INTIAL_THOUGHTS` list to give the agent a context for it's capabilities and how to navigate the `/workspace`

`step`: Modifies the current state by adding the most rescent actions and observations, then prompts the model to think about its next action to take. 

`search_memeory`: Uses `VectorIndexRetriever` to find related memories withing the long term memory.

## Planner Agent:

### Description:
The planner agent is responsible for looking at the current progress of the task as well as the goal and evaluating the best coarse of action given the state. This agent will respond with either a though or an action.

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
`__init__`: Initilizes an agent with `llm`

`step`: Checks to see if current step is completed, returns `AgentFinishAction` if True. Otherwise, creates a plan prompt and sends to model for inference, adding the result as the next action.

`search_memory`: Not yet implemented

## CodeAct Agent:

### Description:
This agent is responsible for executing commands. The agent is prompted by giving it an action to try and complete along with a list of previous steps taken. The Code Act Agent has access to the terminal and can execute arbitrary code via `<execute> COMMAND </execute>`.  

### Actions:
`Action`,
`CmdRunAction`,
`AgentEchoAction`,
`AgentFinishAction`,

### Observations:
`CmdOutputObservation`,
`AgentMessageObservation`,

### Methods:
`__init__`: Initilizes an agent with `llm` and a list of messages `List[Mapping[str, str]]`

`step`: First, gets messages from state and then compiles them into a list for context. Next, pass the context list with the prompt to get the next command to execute. Finally, Execute command if valid, else return `AgentEchoAction(INVALID_INPUT_MESSAGE)` 

`search_memory`: Not yet implemented