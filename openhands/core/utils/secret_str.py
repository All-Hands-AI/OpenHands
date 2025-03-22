from __future__ import annotations

from pydantic import SecretStr as PydanticSecretStr


class SecretStr(PydanticSecretStr):
    """Custom SecretStr class that uses <hidden> instead of ******** for display."""
    
    def _display(self) -> str:
        """Override the default display method to use <hidden> instead of ********."""
        return "<hidden>"