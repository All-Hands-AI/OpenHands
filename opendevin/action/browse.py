from dataclasses import dataclass
import requests

from .base import ExecutableAction


@dataclass
class BrowseURLAction(ExecutableAction):
    url: str

    def run(self, *args, **kwargs) -> str:
        response = requests.get(self.url)
        return response.text
