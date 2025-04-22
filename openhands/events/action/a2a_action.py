from dataclasses import dataclass

from openhands.core.schema.action import ActionType
from openhands.events.action.action import Action


@dataclass
class A2AListRemoteAgentsAction(Action):
    action: str = ActionType.A2A_LIST_REMOTE_AGENTS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def message(self) -> str:
        return 'I am listing the available remote agents.'


@dataclass
class A2ASendTaskAction(Action):
    agent_name: str
    task_message: str
    action: str = ActionType.A2A_SEND_TASK

    def __init__(self, **kwargs):
        # Extract our specific fields before passing to parent
        agent_name = kwargs.pop('agent_name', None)
        task_message = kwargs.pop('task_message', None)
        super().__init__(**kwargs)
        # Set our fields after parent initialization
        self.agent_name = agent_name
        self.task_message = task_message

    @property
    def message(self) -> str:
        return f"""I am sending a task to the remote agent {self.agent_name} with: \n
            task_message: \n {self.task_message} \n
          """

    def __str__(self) -> str:
        return f"""A2ASendTaskAction(
            agent_name={self.agent_name},
            task_message={self.task_message},
        )"""
