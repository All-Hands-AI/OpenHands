from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk


@dataclass
class BrowseURLAction(Action):
    url: str
    thought: str = ""
    action: str = ActionType.BROWSE
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk | None = None
    return_axtree: bool = False

    @property
    def message(self) -> str:
        return f"I am browsing the URL: {self.url}"

    def __str__(self) -> str:
        ret = "**BrowseURLAction**\n"
        if self.thought:
            ret += f"THOUGHT: {self.thought}\n"
        ret += f"URL: {self.url}"
        return ret


@dataclass
class BrowseInteractiveAction(Action):
    browser_actions: str
    thought: str = ""
    browsergym_send_msg_to_user: str = ""
    action: str = ActionType.BROWSE_INTERACTIVE
    runnable: ClassVar[bool] = True
    security_risk: ActionSecurityRisk | None = None
    return_axtree: bool = False

    @property
    def message(self) -> str:
        return f"I am interacting with the browser:\n```\n{self.browser_actions}\n```"

    def __str__(self) -> str:
        ret = "**BrowseInteractiveAction**\n"
        if self.thought:
            ret += f"THOUGHT: {self.thought}\n"
        ret += f"BROWSER_ACTIONS: {self.browser_actions}"
        return ret
