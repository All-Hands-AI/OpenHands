from dataclasses import dataclass

from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk


@dataclass
class MessageAction(Action):
    content: str
    image_urls: list[str] | None = None
    wait_for_response: bool = False
    action: str = ActionType.MESSAGE
    security_risk: ActionSecurityRisk | None = None

    @property
    def message(self) -> str:
        return self.content

    @property
    def images_urls(self):
        # Deprecated alias for backward compatibility
        return self.image_urls

    @images_urls.setter
    def images_urls(self, value):
        self.image_urls = value

    def __str__(self) -> str:
        ret = f'**MessageAction** (source={self.source})\n'
        ret += f'CONTENT: {self.content}'
        if self.image_urls:
            for url in self.image_urls:
                ret += f'\nIMAGE_URL: {url}'
        return ret
