from abc import abstractmethod
from dataclasses import dataclass

from opendevin.events.action import Action
from opendevin.events.observation import Observation


class Plugin:
    """Base class for a plugin.

    This will be initialized by the runtime client, which will run inside docker.
    """

    name: str

    @abstractmethod
    async def initialize(self, username: str):
        """Initialize the plugin."""
        pass

    @abstractmethod
    async def run(self, action: Action) -> Observation:
        """Run the plugin for a given action."""
        pass


@dataclass
class PluginRequirement:
    """Requirement for a plugin."""

    name: str
    # FOLDER/FILES to be copied to the sandbox
    host_src: str
    sandbox_dest: str
    # NOTE: bash_script_path should be relative to the `sandbox_dest` path
    bash_script_path: str
