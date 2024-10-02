
from dataclasses import dataclass


@dataclass
class AgentConfig:
    type: str
    llm: str
    key: str
