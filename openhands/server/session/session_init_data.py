

from dataclasses import dataclass


@dataclass
class SessionInitData:
    """
    Session initialization data for the web environment - a deep copy of the global config is made and then overridden with this data.
    """
    language: str | None = None
    agent: str | None = None
    max_iterations: int | None = None
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
