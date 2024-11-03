import asyncio
import time

from fastapi import WebSocket, WebSocketDisconnect

from openhands.controller.agent import Agent
from openhands.core.config import AppConfig
from openhands.core.const.guide_url import TROUBLESHOOTING_URL
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import AgentState
from openhands.core.schema.action import ActionType
from openhands.core.schema.config import ConfigType
from openhands.events.action import ChangeAgentStateAction, MessageAction, NullAction
from openhands.events.event import Event, EventSource
from openhands.events.observation import (
    AgentStateChangedObservation,
    CmdOutputObservation,
    NullObservation,
)
from openhands.events.observation.error import ErrorObservation
from openhands.events.serialization import event_from_dict, event_to_dict
from openhands.events.stream import EventStreamSubscriber
from openhands.llm.llm import LLM
from openhands.runtime.utils.shutdown_listener import should_continue
from openhands.server.session.agent_session import AgentSession
from openhands.storage.files import FileStore


class Session:
    sid: str
    websocket: WebSocket | None
    last_active_ts: int = 0
    is_alive: bool = True
    agent_session: AgentSession
    loop: asyncio.AbstractEventLoop

    def __init__(
        self, sid: str, ws: WebSocket | None, config: AppConfig, file_store: FileStore
    ):
        self.sid = sid
        self.websocket = ws
        self.last_active_ts = int(time.time())
        self.agent_session = AgentSession(sid, file_store)
        self.agent_session.event_stream.subscribe(
            EventStreamSubscriber.SERVER, self.on_event
        )
        self.config = config
        self.loop = asyncio.get_event_loop()

    async def close(self):
        self.is_alive = False
        await self.agent_session.close()

    async def _heartbeat(self):
        """Send periodic heartbeat to check connection is alive"""
        while self.is_alive and should_continue():
            try:
                await asyncio.wait_for(
                    self.websocket.send_json({"type": "heartbeat"}),
                    timeout=5
                )
                await asyncio.sleep(1)  # Send heartbeat every 30 seconds
            except (asyncio.TimeoutError, WebSocketDisconnect, RuntimeError):
                self.is_alive = False
                break
            except Exception as e:
                logger.exception("Error in heartbeat: %s", e)
                self.is_alive = False
                break

    async def loop_recv(self):
        """Main websocket receive loop with heartbeat"""
        if self.websocket is None:
            return

        # Start heartbeat in background task
        heartbeat_task = asyncio.create_task(self._heartbeat())
        
        try:
            while self.is_alive and should_continue():
                try:
                    # Use timeout to prevent blocking forever
                    data = await asyncio.wait_for(
                        self.websocket.receive_json(),
                        timeout=35  # Slightly longer than heartbeat interval
                    )
                    await self.dispatch(data)
                except asyncio.TimeoutError:
                    # No message received within timeout, check if heartbeat is still alive
                    if not heartbeat_task.done():
                        continue
                    else:
                        logger.error("Heartbeat task failed, closing connection")
                        break
                except ValueError:
                    await self.send_error('Invalid JSON')
                    continue
                except WebSocketDisconnect:
                    logger.debug('WebSocket disconnected, sid: %s', self.sid)
                    break
                except Exception as e:
                    logger.exception("Error processing message: %s", e)
                    await self.send_error(f"Error processing message: {str(e)}")
                    continue

        except Exception as e:
            logger.exception("Fatal error in receive loop: %s", e)
        finally:
            # Cancel heartbeat task
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            
            # Close the session
            await self.close()

    async def _initialize_agent(self, data: dict):
        self.agent_session.event_stream.add_event(
            ChangeAgentStateAction(AgentState.LOADING), EventSource.ENVIRONMENT
        )
        self.agent_session.event_stream.add_event(
            AgentStateChangedObservation('', AgentState.LOADING),
            EventSource.ENVIRONMENT,
        )
        # Extract the agent-relevant arguments from the request
        args = {key: value for key, value in data.get('args', {}).items()}
        agent_cls = args.get(ConfigType.AGENT, self.config.default_agent)
        self.config.security.confirmation_mode = args.get(
            ConfigType.CONFIRMATION_MODE, self.config.security.confirmation_mode
        )
        self.config.security.security_analyzer = data.get('args', {}).get(
            ConfigType.SECURITY_ANALYZER, self.config.security.security_analyzer
        )
        max_iterations = args.get(ConfigType.MAX_ITERATIONS, self.config.max_iterations)
        # override default LLM config
        default_llm_config = self.config.get_llm_config()
        default_llm_config.model = args.get(
            ConfigType.LLM_MODEL, default_llm_config.model
        )
        default_llm_config.api_key = args.get(
            ConfigType.LLM_API_KEY, default_llm_config.api_key
        )
        default_llm_config.base_url = args.get(
            ConfigType.LLM_BASE_URL, default_llm_config.base_url
        )

        # TODO: override other LLM config & agent config groups (#2075)

        llm = LLM(config=self.config.get_llm_config_from_agent(agent_cls))
        agent_config = self.config.get_agent_config(agent_cls)
        agent = Agent.get_cls(agent_cls)(llm, agent_config)

        # Create the agent session
        try:
            await self.agent_session.start(
                runtime_name=self.config.runtime,
                config=self.config,
                agent=agent,
                max_iterations=max_iterations,
                max_budget_per_task=self.config.max_budget_per_task,
                agent_to_llm_config=self.config.get_agent_to_llm_config_map(),
                agent_configs=self.config.get_agent_configs(),
                status_message_callback=self.queue_status_message,
            )
        except Exception as e:
            logger.exception(f'Error creating controller: {e}')
            await self.send_error(
                f'Error creating controller. Please check Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information..'
            )
            return

    async def on_event(self, event: Event):
        """Callback function for events that mainly come from the agent.
        Event is the base class for any agent action and observation.

        Args:
            event: The agent event (Observation or Action).
        """
        if isinstance(event, NullAction):
            return
        if isinstance(event, NullObservation):
            return
        if event.source == EventSource.AGENT:
            await self.send(event_to_dict(event))
        # NOTE: ipython observations are not sent here currently
        elif event.source == EventSource.ENVIRONMENT and isinstance(
            event, (CmdOutputObservation, AgentStateChangedObservation)
        ):
            # feedback from the environment to agent actions is understood as agent events by the UI
            event_dict = event_to_dict(event)
            event_dict['source'] = EventSource.AGENT
            await self.send(event_dict)
        elif isinstance(event, ErrorObservation):
            # send error events as agent events to the UI
            event_dict = event_to_dict(event)
            event_dict['source'] = EventSource.AGENT
            await self.send(event_dict)

    async def dispatch(self, data: dict):
        """Dispatch incoming websocket messages to appropriate handlers"""
        action = data.get('action', '')
        
        # Handle initialization separately
        if action == ActionType.INIT:
            try:
                async with asyncio.timeout(120):
                    await self._initialize_agent(data)
            except asyncio.TimeoutError:
                await self.send_error('Agent initialization timed out')
            except Exception as e:
                logger.exception("Error initializing agent: %s", e)
                await self.send_error(f'Failed to initialize agent: {str(e)}')
            return

        # Convert message to event
        try:
            event = event_from_dict(data.copy())
        except Exception as e:
            logger.error("Failed to parse event: %s", e)
            await self.send_error('Invalid event format')
            return

        # Handle image validation
        if isinstance(event, MessageAction) and event.images_urls:
            controller = self.agent_session.controller
            if controller:
                if controller.agent.llm.config.disable_vision:
                    await self.send_error(
                        'Support for images is disabled for this model, try without an image.'
                    )
                    return
                if not controller.agent.llm.vision_is_active():
                    await self.send_error(
                        'Model does not support image upload, change to a different model or try without an image.'
                    )
                    return


        try:
            # Use asyncio.wait_for to prevent blocking indefinitely
            future = asyncio.run_coroutine_threadsafe(
                self._add_event(event, EventSource.USER), 
                asyncio.get_running_loop()
            )
            # Wait for the event to be processed with timeout
            await asyncio.wait_for(
                asyncio.wrap_future(future),
                timeout=10
            )
        except asyncio.TimeoutError:
            logger.error("Event processing timed out")
            await self.send_error('Event processing timed out')
        except Exception as e:
            logger.exception("Error processing event: %s", e)
            await self.send_error(f'Failed to process event: {str(e)}')

    async def _add_event(self, event, event_source):
        self.agent_session.event_stream.add_event(event, EventSource.USER)

    async def send(self, data: dict[str, object]) -> bool:
        try:
            if self.websocket is None or not self.is_alive:
                return False
            await self.websocket.send_json(data)
            await asyncio.sleep(0.001)  # This flushes the data to the client
            self.last_active_ts = int(time.time())
            return True
        except RuntimeError:
            self.is_alive = False
            return False
        except WebSocketDisconnect:
            self.is_alive = False
            return False

    async def send_error(self, message: str) -> bool:
        """Sends an error message to the client."""
        return await self.send({'error': True, 'message': message})

    async def send_status_message(self, message: str) -> bool:
        """Sends a status message to the client."""
        return await self.send({'status': message})

    def queue_status_message(self, message: str):
        """Queues a status message to be sent asynchronously."""
        # Ensure the coroutine runs in the main event loop
        asyncio.run_coroutine_threadsafe(self.send_status_message(message), self.loop)
