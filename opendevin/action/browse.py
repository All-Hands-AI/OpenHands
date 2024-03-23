from dataclasses import dataclass
import requests

from .base import Action


@dataclass
class BrowseURLAction(Action):
    url: str

    def run(self, *args, **kwargs) -> str:
        response = requests.get(self.url)
        return response.text
