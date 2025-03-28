from openhands.critic.base import BaseCritic, CriticResult
from openhands.events import Event
from openhands.events.action import Action, AgentFinishAction


class AgentFinishedCritic(BaseCritic):
    """This is a simple rule-based critic that checks if the last event is an AgentFinishAction.

    If not, it will return a score of 0 and a message indicating that the agent did not finish.
    """

    def __init__(self):
        pass

    def evaluate(self, events: list[Event]) -> CriticResult:
        last_action = next((h for h in reversed(events) if isinstance(h, Action)), None)

        if isinstance(last_action, AgentFinishAction):
            return CriticResult(score=1, message='Agent finished.')
        else:
            return CriticResult(score=0, message='Agent did not finish.')
