from openhands.runtime.plugins.agent_skills.a2a_client import a2a_client
from openhands.runtime.plugins.agent_skills.utils.dependency import import_functions

import_functions(
    module=a2a_client,
    function_names=a2a_client.__all__,
    target_globals=globals(),
)
__all__ = a2a_client.__all__
