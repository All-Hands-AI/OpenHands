from typing import List, Protocol, Tuple, Dict
from opendevin.logger import opendevin_logger as logger
from opendevin.sandbox.plugins.requirement import PluginRequirement


class HasExecuteProtocol(Protocol):
    # https://stackoverflow.com/questions/51930339/ how-do-i-correctly-add-type-hints-to-mixin-classes

    plugins: Dict[str, str]

    def execute(self, cmd: str) -> Tuple[int, str]:
        ...


class PluginMixin:
    """Mixin for Sandbox to support plugins."""

    def load_plugins(self: HasExecuteProtocol,
                     requirements: List[PluginRequirement]):
        """Load a plugin into the sandbox."""
        for requirement in requirements:
            self.plugins[requirement.name] = requirement.bash_script_path
            # Execute the bash script
            logger.info(f"Initalizing plugin {requirement.name} by executing [{requirement.bash_script_path}]")
            self.execute(requirement.bash_script_path)
