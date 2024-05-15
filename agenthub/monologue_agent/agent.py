import agenthub.monologue_agent.utils.prompts as prompts
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import config
from opendevin.core.exceptions import AgentNoInstructionError
from opendevin.core.schema import ActionType
from opendevin.events.action import (
    Action,
    AgentRecallAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    MessageAction,
    NullAction,
)
from opendevin.events.observation import (
    AgentRecallObservation,
    BrowserOutputObservation,
    CmdOutputObservation,
    FileReadObservation,
    NullObservation,
    Observation,
)
from opendevin.events.serialization.event import event_to_memory
from opendevin.llm.llm import LLM
from opendevin.memory.condenser import MemoryCondenser
from opendevin.memory.history import ShortTermHistory

if config.agent.memory_enabled:
    from opendevin.memory.memory import LongTermMemory

MAX_TOKEN_COUNT_PADDING = 512
MAX_OUTPUT_LENGTH = 5000

INITIAL_THOUGHTS = [
    'I exist!',
    'Hmm...looks like I can type in a command line prompt',
    'Looks like I have a web browser too!',
    "Here's what I want to do: $TASK",
    'How am I going to get there though?',
    'It seems like I have some kind of short term memory.',
    'Each of my thoughts seems to be stored in a JSON array.',
    'It seems whatever I say next will be added as an object to the list.',
    'But no one has perfect short-term memory. My list of thoughts will be summarized and condensed over time, losing information in the process.',
    'Fortunately I have long term memory!',
    'I can just perform a recall action, followed by the thing I want to remember. And then related thoughts just spill out!',
    "Sometimes they're random thoughts that don't really have to do with what I wanted to remember. But usually they're exactly what I need!",
    "Let's try it out!",
    'RECALL what it is I want to do',
    "Here's what I want to do: $TASK",
    'How am I going to get there though?',
    "Neat! And it looks like it's easy for me to use the command line too! I just have to perform a run action and include the command I want to run in the command argument. The command output just jumps into my head!",
    'RUN echo "hello world"',
    'hello world',
    'Cool! I bet I can write files too using the write action.',
    'WRITE echo "console.log(\'hello world\')" > test.js',
    '',
    "I just created test.js. I'll try and run it now.",
    'RUN node test.js',
    'hello world',
    'It works!',
    "I'm going to try reading it now using the read action.",
    'READ test.js',
    "console.log('hello world')",
    'Nice! I can read files too!',
    'And if I want to use the browser, I just need to use the browse action and include the url I want to visit in the url argument',
    "Let's try that...",
    'BROWSE google.com',
    '<form><input type="text"></input><button type="submit"></button></form>',
    'I can browse the web too!',
    'And once I have completed my task, I can use the finish action to stop working.',
    "But I should only use the finish action when I'm absolutely certain that I've completed my task and have tested my work.",
    'Very cool. Now to accomplish my task.',
    "I'll need a strategy. And as I make progress, I'll need to keep refining that strategy. I'll need to set goals, and break them into sub-goals.",
    'In between actions, I must always take some time to think, strategize, and set new goals. I should never take two actions in a row.',
    "OK so my task is to $TASK. I haven't made any progress yet. Where should I start?",
    'It seems like there might be an existing project here. I should probably start by running `pwd` and `ls` to orient myself.',
]


class MonologueAgent(Agent):
    """
    The Monologue Agent utilizes long and short term memory to complete tasks.
    Long term memory is stored as a LongTermMemory object and the model uses it to search for examples from the past.
    Short term memory is stored as a Monologue object and the model can condense it as necessary.
    """

    _initialized = False
    monologue: ShortTermHistory
    memory: 'LongTermMemory | None'
    memory_condenser: MemoryCondenser

    def __init__(self, llm: LLM):
        """
        Initializes the Monologue Agent with an llm, monologue, and memory.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)

    def _add_event(self, event_dict: dict):
        """
        Adds a new event to the agent's monologue and memory.
        Monologue automatically condenses when it gets too large.

        Parameters:
        - event (dict): The event that will be added to monologue and memory
        """

        if (
            'args' in event_dict
            and 'output' in event_dict['args']
            and len(event_dict['args']['output']) > MAX_OUTPUT_LENGTH
        ):
            event_dict['args']['output'] = (
                event_dict['args']['output'][:MAX_OUTPUT_LENGTH] + '...'
            )

        self.monologue.add_event(event_dict)
        if self.memory is not None:
            self.memory.add_event(event_dict)

        # Test monologue token length
        prompt = prompts.get_request_action_prompt(
            '',
            self.monologue.get_events(),
            [],
        )
        messages = [{'content': prompt, 'role': 'user'}]
        token_count = self.llm.get_token_count(messages)

        if token_count + MAX_TOKEN_COUNT_PADDING > self.llm.max_input_tokens:
            prompt = prompts.get_summarize_monologue_prompt(self.monologue.events)
            summary_response = self.memory_condenser.condense(
                summarize_prompt=prompt, llm=self.llm
            )
            self.monologue.events = prompts.parse_summary_response(summary_response)

    def _initialize(self, task: str):
        """
        Utilizes the INITIAL_THOUGHTS list to give the agent a context for its capabilities
        and how to navigate the WORKSPACE_MOUNT_PATH_IN_SANDBOX in `config` (e.g., /workspace by default).
        Short circuited to return when already initialized.
        Will execute again when called after reset.

        Parameters:
        - task (str): The initial goal statement provided by the user

        Raises:
        - AgentNoInstructionError: If task is not provided
        """

        if self._initialized:
            return

        if task is None or task == '':
            raise AgentNoInstructionError()

        self.monologue = ShortTermHistory()
        if config.agent.memory_enabled:
            self.memory = LongTermMemory()
        else:
            self.memory = None

        self.memory_condenser = MemoryCondenser()

        self._add_initial_thoughts(task)
        self._initialized = True

    def _add_initial_thoughts(self, task):
        previous_action = ''
        for thought in INITIAL_THOUGHTS:
            thought = thought.replace('$TASK', task)
            if previous_action != '':
                observation: Observation = NullObservation(content='')
                if previous_action in {ActionType.RUN, ActionType.PUSH}:
                    observation = CmdOutputObservation(
                        content=thought, command_id=0, command=''
                    )
                elif previous_action == ActionType.READ:
                    observation = FileReadObservation(content=thought, path='')
                elif previous_action == ActionType.RECALL:
                    observation = AgentRecallObservation(content=thought, memories=[])
                elif previous_action == ActionType.BROWSE:
                    observation = BrowserOutputObservation(
                        content=thought, url='', screenshot=''
                    )
                self._add_event(event_to_memory(observation))
                previous_action = ''
            else:
                action: Action = NullAction()
                if thought.startswith('RUN'):
                    command = thought.split('RUN ')[1]
                    action = CmdRunAction(command)
                    previous_action = ActionType.RUN
                elif thought.startswith('WRITE'):
                    parts = thought.split('WRITE ')[1].split(' > ')
                    path = parts[1]
                    content = parts[0]
                    action = FileWriteAction(path=path, content=content)
                elif thought.startswith('READ'):
                    path = thought.split('READ ')[1]
                    action = FileReadAction(path=path)
                    previous_action = ActionType.READ
                elif thought.startswith('RECALL'):
                    query = thought.split('RECALL ')[1]
                    action = AgentRecallAction(query=query)
                    previous_action = ActionType.RECALL
                elif thought.startswith('BROWSE'):
                    url = thought.split('BROWSE ')[1]
                    action = BrowseURLAction(url=url)
                    previous_action = ActionType.BROWSE
                else:
                    action = MessageAction(thought)
                self._add_event(event_to_memory(action))

    def step(self, state: State) -> Action:
        """
        Modifies the current state by adding the most recent actions and observations, then prompts the model to think about it's next action to take using monologue, memory, and hint.

        Parameters:
        - state (State): The current state based on previous steps taken

        Returns:
        - Action: The next action to take based on LLM response
        """

        goal = state.get_current_user_intent()
        self._initialize(goal)
        for prev_action, obs in state.updated_info:
            self._add_event(event_to_memory(prev_action))
            self._add_event(event_to_memory(obs))

        state.updated_info = []

        prompt = prompts.get_request_action_prompt(
            goal,
            self.monologue.get_events(),
            state.background_commands_obs,
        )
        messages = [{'content': prompt, 'role': 'user'}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        state.num_of_chars += len(prompt) + len(action_resp)
        action = prompts.parse_action_response(action_resp)
        self.latest_action = action
        return action

    def search_memory(self, query: str) -> list[str]:
        """
        Uses VectorIndexRetriever to find related memories within the long term memory.
        Uses search to produce top 10 results.

        Parameters:
        - query (str): The query that we want to find related memories for

        Returns:
        - list[str]: A list of top 10 text results that matched the query
        """
        if self.memory is None:
            return []
        return self.memory.search(query)

    def reset(self) -> None:
        super().reset()

        # Reset the initial monologue and memory
        self._initialized = False
