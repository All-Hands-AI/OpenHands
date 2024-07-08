from dataclasses import dataclass

from opendevin.core.schema import ActionType

from .action import Action


@dataclass
class MessageAction(Action):
    content: str
    images_base64: list | None = None
    wait_for_response: bool = False
    action: str = ActionType.MESSAGE

    @property
    def message(self) -> str:
        return self.content

    def __str__(self) -> str:
        ret = f'**MessageAction** (source={self.source})\n'
        ret += f'CONTENT: {self.content}'
        if self.images_base64:
            for url in self.images_base64:
                ret += f'\nIMAGE_URL: {url}'
        return ret
