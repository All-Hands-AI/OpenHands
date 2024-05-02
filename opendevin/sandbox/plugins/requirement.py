from dataclasses import dataclass


@dataclass
class PluginRequirement:
    """Requirement for a plugin."""

    name: str
    # FOLDER/FILES to be copied to the sandbox
    host_src: str
    sandbox_dest: str
    # NOTE: bash_script_path should be relative to the `sandbox_dest` path
    bash_script_path: str
