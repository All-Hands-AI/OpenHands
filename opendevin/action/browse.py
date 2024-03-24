from dataclasses import dataclass
import requests

from .base import Action, Executable


@dataclass
class BrowseURLAction(Action, Executable):
    url: str

    def run(self, *args, **kwargs) -> str:
        response = requests.get(self.url)
        return response.text
