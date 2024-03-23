from dataclasses import dataclass
from typing import Mapping

@dataclass
class State:
    background_commands: Mapping[int, str]
