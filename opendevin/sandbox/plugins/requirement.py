from dataclasses import dataclass


@dataclass
class PluginRequirement:
    """Requirement for a plugin."""
    name: str
    # NOTE: bash_script_path shoulds be relative to the `plugin` directory
    bash_script_path: str
