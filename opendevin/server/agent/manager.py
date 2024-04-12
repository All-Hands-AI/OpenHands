import atexit
import signal

from opendevin.server.session import session_manager
from .agent import AgentUnit


class AgentManager:
    sid_to_agent: dict[str, 'AgentUnit'] = {}

    def __init__(self):
        atexit.register(self.close)
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

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

    def handle_signal(self, signum, _):
        print(f"Received signal {signum}, exiting...")
        self.close()
        exit(0)

    def close(self):
        for sid, agent in self.sid_to_agent.items():
            agent.close()
