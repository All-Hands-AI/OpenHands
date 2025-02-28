import asyncio

from openhands.controller import AgentController
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import AgentState
from openhands.runtime.base import Runtime


async def run_agent_until_done(
    controller: AgentController,
    runtime: Runtime,
    end_states: list[AgentState],
):
    """
    run_agent_until_done takes a controller and a runtime, and will run
    the agent until it reaches a terminal state.
    Note that runtime must be connected before being passed in here.
    """

    def status_callback(msg_type, msg_id, msg):
        if msg_type == 'error':
            logger.error(msg)
            if controller:
                controller.state.last_error = msg
                asyncio.create_task(controller.set_agent_state_to(AgentState.ERROR))
        else:
            logger.info(msg)

    if hasattr(runtime, 'status_callback') and runtime.status_callback:
        raise ValueError(
            'Runtime status_callback was set, but run_agent_until_done will override it'
        )
    if hasattr(controller, 'status_callback') and controller.status_callback:
        raise ValueError(
            'Controller status_callback was set, but run_agent_until_done will override it'
        )

    runtime.status_callback = status_callback
    controller.status_callback = status_callback

    while controller.state.agent_state not in end_states:
        await asyncio.sleep(1)
