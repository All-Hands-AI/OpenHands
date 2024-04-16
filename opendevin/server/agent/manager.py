import atexit

from opendevin.server.session import session_manager
from opendevin.logger import opendevin_logger as logger
from .agent import AgentUnit


class AgentManager:
    sid_to_agent: dict[str, 'AgentUnit'] = {}

    def __init__(self):
        atexit.register(self.close)

    def register_agent(self, sid: str):
        """Registers a new agent.

        Args:
            sid: The session ID of the agent.
        """
        if sid not in self.sid_to_agent:
            self.sid_to_agent[sid] = AgentUnit(sid)
            return

        # TODO: confirm whether the agent is alive

    async def dispatch(self, sid: str, action: str | None, data: dict):
        """Dispatches actions to the agent from the client."""
        if sid not in self.sid_to_agent:
            # self.register_agent(sid)  # auto-register agent, may be opened later
            await session_manager.send_error(sid, 'Agent not registered')
            return

        await self.sid_to_agent[sid].dispatch(action, data)

    def close(self):
        logger.info(f'Closing {len(self.sid_to_agent)} agent(s)...')
        for sid, agent in self.sid_to_agent.items():
            agent.close()
