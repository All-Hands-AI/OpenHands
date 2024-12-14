
<<<<<<< HEAD
=======

>>>>>>> 47169559606a4d2fe3b97e0685f42bfb8d0a4756
from dataclasses import dataclass


@dataclass
class SessionInitData:
    """
    Session initialization data for the web environment - a deep copy of the global config is made and then overridden with this data.
    """
<<<<<<< HEAD
<<<<<<< HEAD
=======

>>>>>>> d317a3ef (Fix pr #5248: Fix issue #2947: Feat: make use of litellm's response "usage" data)
=======
>>>>>>> 47169559606a4d2fe3b97e0685f42bfb8d0a4756
    language: str | None = None
    agent: str | None = None
    max_iterations: int | None = None
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    github_token: str | None = None
    selected_repository: str | None = None
