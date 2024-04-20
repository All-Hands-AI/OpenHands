from dataclasses import dataclass


@dataclass
class PluginRequirement:
    """Requirement for a plugin."""
    name: str
    bash_script_path: str
