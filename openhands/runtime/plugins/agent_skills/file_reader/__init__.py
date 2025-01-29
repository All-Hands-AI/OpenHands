"""File reader module for agent skills.

DEPRECATED: This module is deprecated and will be removed in version 0.22.0.
Please migrate to the function calling interface.
See https://docs.all-hands.dev/usage/migration/agent-skills-to-function-calls for details.
"""

import warnings

warnings.warn(
    "The file_reader module is deprecated and will be removed in version 0.22.0. "
    "Please migrate to the function calling interface. "
    "See https://docs.all-hands.dev/usage/migration/agent-skills-to-function-calls for details.",
    DeprecationWarning,
    stacklevel=2
)

from openhands.runtime.plugins.agent_skills.file_reader import file_readers
from openhands.runtime.plugins.agent_skills.utils.dependency import import_functions

import_functions(
    module=file_readers, function_names=file_readers.__all__, target_globals=globals()
)
__all__ = file_readers.__all__
