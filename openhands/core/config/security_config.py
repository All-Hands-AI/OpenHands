from pydantic import BaseModel, Field


class SecurityConfig(BaseModel):
    """Configuration for security related functionalities.

    Attributes:
        confirmation_mode: Whether to enable confirmation mode.
        security_analyzer: The security analyzer to use.
    """

    confirmation_mode: bool = Field(default=False)
    security_analyzer: str | None = Field(default=None)
