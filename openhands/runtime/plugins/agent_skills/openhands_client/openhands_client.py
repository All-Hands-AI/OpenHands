import asyncio
import time
from typing import Any, Optional

import requests
import socketio

SERVER_READY_TIMEOUT = 120
STATUS_UPDATE_TIMEOUT = 3


class OpenhandsClient:
    """
    A simple client for interacting with an OpenHands server.
    """

    def __init__(
        self,
        base_url: str,
        conversation_id: str = '',
        timeout: int = SERVER_READY_TIMEOUT,
    ):
        self.base_url = base_url.rstrip('/')
        self.server_ready_timeout = timeout
        self.sio = socketio.AsyncClient()
        self._set_event_handlers()

        if conversation_id:
            self.conversation_id = conversation_id
        else:
            self.conversation_id = self._get_conversation_id(base_url)

        self.agent_state = None
        self.agent_ready = False
        self.history_loaded = False
        self.force_ready_task: Optional[asyncio.Task[Any]] = None

    def _set_event_handlers(self):
        @self.sio.event
        async def connect():
            print('--- Connected to server and finished loading history ---')
            print('Conversation_id is: ', self.conversation_id)
            print(
                'Use this conversation_id to reconnect to the same session later again'
            )
            print('--------------------------------------------------------')
            self.history_loaded = True
            self.force_ready_task = asyncio.create_task(
                self._force_ready_after_timeout()
            )

        @self.sio.event
        async def disconnect():
            print('Disconnected from server')

        @self.sio.event
        async def oh_event(event):
            print(event)
            if self.history_loaded:
                if event.get('observation') == 'agent_state_changed' and event.get(
                    'extras'
                ).get('agent_state'):
                    self.agent_state = event.get('extras').get('agent_state')
                    if self.agent_state in ['init', 'awaiting_user_input', 'finished']:
                        self.agent_ready = True
                if event.get('status_update'):
                    if self.force_ready_task:
                        self.force_ready_task.cancel()

    async def _force_ready_after_timeout(self):
        """
        This method is called if the agent_ready remains unset even STATUS_UPDATE_TIMEOUT seconds after the history loading has completed.
        If client does not receive "status_update" message, it means previous session is still alive and already ready.
        """
        await asyncio.sleep(STATUS_UPDATE_TIMEOUT)
        if not self.agent_ready:
            self.agent_ready = True

    def _get_conversation_id(self, base_url: str):
        response = requests.post(base_url + '/api/conversations', json={})
        response.raise_for_status()
        return response.json()['conversation_id']

    async def connect(self):
        await self.sio.connect(
            f'{self.base_url}?conversation_id={self.conversation_id}'
        )

    async def close(self):
        await self.sio.disconnect()

    async def wait_ready(self):
        start_time = time.time()
        while True:
            if time.time() - start_time > self.server_ready_timeout:
                raise Exception(
                    'Timeout: Server or agent is not ready after waiting for '
                    + str(self.server_ready_timeout)
                    + ' seconds.'
                )
            if self.history_loaded and self.agent_ready:
                return True
            await asyncio.sleep(1)

    async def send_message_action(self, message: str):
        if not self.history_loaded or not self.agent_ready:
            raise Exception('The server or agent is not ready for receiving messages.')

        data = {'action': 'message', 'args': {'content': message}}
        await self.sio.emit('oh_action', data)
        self.agent_ready = False


async def message_to_remote_OH(message: str, url: str, conversation_id: str = ''):
    """Send a message to an agent hosted on another OpenHands instance.
    Args:
      message: message to send
      url: url where the remote OpenHands server is
      conversation_id(optional): id to identify session
    """
    client = OpenhandsClient(url, conversation_id)

    await client.connect()

    try:
        if await client.wait_ready():
            await client.send_message_action(message)
            await client.wait_ready()
    except Exception as e:
        print(e)
    finally:
        await client.close()


__all__ = ['message_to_remote_OH', 'OpenhandsClient']
