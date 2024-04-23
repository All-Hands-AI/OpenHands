from typing import List

from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.state import State
from opendevin.action import (
    Action,
    CmdRunAction,
    FileWriteAction,
    FileReadAction,
    AgentFinishAction,
    AgentThinkAction,
    AddTaskAction,
    ModifyTaskAction,
    AgentRecallAction,
    BrowseURLAction,
)


class DummyAgent(Agent):
    '''
    The DummyAgent is used for e2e testing. It just sends the same set of actions deterministically,
    without making any LLM calls.
    '''

    def __init__(self, llm: LLM):
        super().__init__(llm)
        self.steps = [
            AddTaskAction(parent='0', goal='check the current directory'),
            AddTaskAction(parent='0.0', goal='run ls'),
            ModifyTaskAction(id='0.0', state='in_progress'),
            AgentThinkAction(thought='Time to get started!'),
            CmdRunAction(command='ls'),
            FileWriteAction(content='echo "Hello, World!"', path='hello.sh'),
            FileReadAction(path='hello.sh'),
            CmdRunAction(command='bash hello.sh'),
            CmdRunAction(command='echo "This is in the background"', background=True),
            AgentRecallAction(query='who am I?'),
            BrowseURLAction(url='https://google.com'),
            AgentFinishAction(),
        ]

    def step(self, state: State) -> Action:
        return self.steps[state.iteration]

    def search_memory(self, query: str) -> List[str]:
        return ['I am a computer.']
