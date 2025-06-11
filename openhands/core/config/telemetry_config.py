"""
OpenHands Telemetry Configuration.

This module defines the configuration model for the OpenHands telemetry system,
which integrates with OpenTelemetry and Logfire for comprehensive logging,
tracing, and metrics collection.
"""

from typing import Any, ClassVar, Dict, Literal

from pydantic import BaseModel, Field

from openhands import __version__ as openhands_version


class TelemetryConfig(BaseModel):
    """Configuration for the OpenHands telemetry system.

    Attributes:
        service_name: Name of the service for OpenTelemetry Scope.
        service_version: Version of the service for OpenTelemetry Scope.
        logfire_enabled: Whether to enable Logfire integration.
        logfire_token: Logfire API token. Follow this guide to obtain token: https://logfire.pydantic.dev/docs/how-to-guides/create-write-tokens/
        logfire_scrubbing: Whether to scrubbing sensitive data. See more details at https://logfire.pydantic.dev/docs/how-to-guides/scrubbing/
    """

    service_name: str = Field(default="openhands")
    service_version: str = Field(default=openhands_version)
    logfire_enabled: bool = Field(default=False)
    logfire_token: str = Field(default="")
    logfire_scrubbing: Literal[False] | None = None

    defaults_dict: ClassVar[Dict[str, Any]] = {}

    model_config = {"extra": "forbid"}

    @classmethod
    def from_toml_section(cls, section: dict) -> dict[str, "TelemetryConfig"]:
        """Create TelemetryConfig instances from a TOML section.

        Args:
            section: The TOML section containing telemetry configurations.

        Returns:
            A dictionary mapping configuration names to TelemetryConfig instances.
        """
        result = {}

        # Process the base telemetry section (no subsection)
        base_config = {}
        for key, value in section.items():
            if not isinstance(value, dict):
                base_config[key] = value

        if base_config:
            result["telemetry"] = cls(**base_config)

        # Process named telemetry configurations
        for key, value in section.items():
            if isinstance(value, dict):
                result[key] = cls(**value)

        return result
