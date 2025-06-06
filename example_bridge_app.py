#!/usr/bin/env python3
"""
Eksempel på hvordan du kan bruke OpenHands Bridge
i dine egne applikasjoner
"""

import asyncio
import json
import logging
from typing import Any

from openhands_bridge import (
    BridgeHandler,
    LoggingBridgeHandler,
    OpenHandsBridge,
    OpenHandsMessage,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomBridgeHandler(BridgeHandler):
    """Eksempel på en tilpasset handler"""

    def __init__(self, app_name: str):
        self.app_name = app_name
        self.message_count = 0
        self.conversation_history = []

    async def handle_user_input(self, message: OpenHandsMessage) -> None:
        """Behandle bruker input"""
        self.message_count += 1

        # Lagre i historikk
        self.conversation_history.append(
            {
                'type': 'user_input',
                'content': message.content,
                'timestamp': message.timestamp,
            }
        )

        logger.info(
            f'[{self.app_name}] Bruker sa: {message.content.get("args", {}).get("content", "N/A")}'
        )

        # Du kan her sende til din egen applikasjon
        await self.send_to_my_app('user_input', message.content)

    async def handle_agent_output(self, message: OpenHandsMessage) -> None:
        """Behandle agent output"""
        self.message_count += 1

        # Lagre i historikk
        self.conversation_history.append(
            {
                'type': 'agent_output',
                'content': message.content,
                'timestamp': message.timestamp,
            }
        )

        # Ekstraher relevant info
        action_type = message.content.get('action', 'unknown')

        if action_type == 'message':
            agent_message = message.content.get('args', {}).get('content', 'N/A')
            logger.info(f'[{self.app_name}] Agent sa: {agent_message}')
        elif action_type == 'run':
            command = message.content.get('args', {}).get('command', 'N/A')
            logger.info(f'[{self.app_name}] Agent kjører: {command}')
        elif action_type == 'edit':
            path = message.content.get('args', {}).get('path', 'N/A')
            logger.info(f'[{self.app_name}] Agent redigerer: {path}')

        # Send til din egen applikasjon
        await self.send_to_my_app('agent_output', message.content)

    async def handle_error(self, error: str, context: dict[str, Any]) -> None:
        """Behandle feil"""
        logger.error(f'[{self.app_name}] Feil: {error}')
        await self.send_to_my_app('error', {'error': error, 'context': context})

    async def send_to_my_app(self, message_type: str, data: dict[str, Any]):
        """Send data til din egen applikasjon"""
        # Her kan du implementere din egen logikk
        # F.eks. send til database, WebSocket, HTTP API, etc.

        # Eksempel: Lagre til fil
        with open(f'/tmp/{self.app_name}_messages.jsonl', 'a') as f:
            json.dump(
                {
                    'type': message_type,
                    'data': data,
                    'timestamp': asyncio.get_event_loop().time(),
                },
                f,
                ensure_ascii=False,
            )
            f.write('\n')

    def get_stats(self) -> dict[str, Any]:
        """Få statistikk"""
        return {
            'app_name': self.app_name,
            'message_count': self.message_count,
            'conversation_length': len(self.conversation_history),
        }


class ChatBotApp:
    """Eksempel på en chatbot som bruker OpenHands Bridge"""

    def __init__(self, name: str):
        self.name = name
        self.bridge = OpenHandsBridge()
        self.handler = CustomBridgeHandler(f'ChatBot-{name}')
        self.bridge.add_handler(self.handler)

        # Legg til logging
        self.bridge.add_handler(LoggingBridgeHandler(f'/tmp/chatbot_{name}.log'))

    async def start(self, conversation_id: str):
        """Start chatbot"""
        logger.info(f'Starting ChatBot {self.name}')

        # Prøv å finne OpenHands
        openhands_url = self.bridge.discover_openhands_url()
        if openhands_url:
            self.bridge.openhands_url = openhands_url
            logger.info(f'Found OpenHands at: {openhands_url}')

        # Koble til samtale
        success = await self.bridge.connect_to_conversation(conversation_id)
        if not success:
            logger.error('Failed to connect to OpenHands')
            return False

        logger.info(f'ChatBot {self.name} connected to conversation {conversation_id}')
        return True

    async def send_message(self, message: str):
        """Send melding til OpenHands"""
        return await self.bridge.send_user_message(message)

    async def auto_respond(self, trigger_words: list = None):
        """Automatisk respons basert på agent output"""
        if trigger_words is None:
            trigger_words = ['hjelp', 'help', 'error', 'feil']

        # Dette er en enkel implementasjon
        # I praksis ville du lytte på agent output og respondere
        while self.bridge.connected:
            await asyncio.sleep(1)

            # Sjekk siste meldinger for trigger words
            recent_messages = self.handler.conversation_history[-5:]
            for msg in recent_messages:
                if msg['type'] == 'agent_output':
                    content = str(msg['content']).lower()
                    for trigger in trigger_words:
                        if trigger in content:
                            await self.send_message(
                                f'Jeg ser du trenger hjelp med: {trigger}'
                            )
                            await asyncio.sleep(5)  # Unngå spam

    async def stop(self):
        """Stopp chatbot"""
        await self.bridge.disconnect()
        logger.info(f'ChatBot {self.name} stopped')

    def get_stats(self):
        """Få statistikk"""
        return self.handler.get_stats()


class MonitoringApp:
    """Eksempel på en monitoring applikasjon"""

    def __init__(self):
        self.bridge = OpenHandsBridge()
        self.handler = CustomBridgeHandler('Monitor')
        self.bridge.add_handler(self.handler)

        # Statistikk
        self.command_count = 0
        self.error_count = 0
        self.session_start = None

    async def start_monitoring(self, conversation_id: str):
        """Start monitoring"""
        logger.info('Starting OpenHands Monitor')

        # Finn OpenHands
        openhands_url = self.bridge.discover_openhands_url()
        if openhands_url:
            self.bridge.openhands_url = openhands_url

        # Koble til
        success = await self.bridge.connect_to_conversation(conversation_id)
        if success:
            self.session_start = asyncio.get_event_loop().time()
            logger.info('Monitor connected and running')

            # Start monitoring loop
            await self.monitoring_loop()

    async def monitoring_loop(self):
        """Hovedloop for monitoring"""
        while self.bridge.connected:
            await asyncio.sleep(10)  # Sjekk hver 10. sekund

            # Analyser aktivitet
            stats = self.handler.get_stats()
            logger.info(f'Monitor stats: {stats}')

            # Sjekk for problemer
            if self.error_count > 5:
                logger.warning('High error count detected!')
                await self.send_alert('High error count')

            # Sjekk for inaktivitet
            if len(self.handler.conversation_history) == 0:
                logger.info('No activity detected')

    async def send_alert(self, message: str):
        """Send varsel"""
        logger.warning(f'ALERT: {message}')
        # Her kan du sende til Slack, email, etc.


async def demo_multiple_apps():
    """Demo med flere applikasjoner som kobler til samme OpenHands"""

    conversation_id = 'demo-multi-app'

    # Opprett flere applikasjoner
    chatbot1 = ChatBotApp('Assistant')
    chatbot2 = ChatBotApp('Helper')
    monitor = MonitoringApp()

    # Start alle
    tasks = []

    # Start chatbots
    if await chatbot1.start(conversation_id):
        tasks.append(asyncio.create_task(chatbot1.auto_respond()))

    if await chatbot2.start(conversation_id):
        tasks.append(
            asyncio.create_task(chatbot2.auto_respond(['python', 'code', 'debug']))
        )

    # Start monitor
    tasks.append(asyncio.create_task(monitor.start_monitoring(conversation_id)))

    # Simuler noe aktivitet
    await asyncio.sleep(2)
    await chatbot1.send_message('Hei OpenHands! Kan du hjelpe meg med Python?')

    await asyncio.sleep(5)
    await chatbot2.send_message('Jeg trenger hjelp med debugging')

    # La applikasjonene kjøre
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info('Stopping all applications...')
    finally:
        await chatbot1.stop()
        await chatbot2.stop()


async def simple_demo():
    """Enkel demo"""

    # Opprett bridge
    bridge = OpenHandsBridge()

    # Legg til handlers
    bridge.add_handler(LoggingBridgeHandler('/tmp/simple_demo.log'))
    bridge.add_handler(CustomBridgeHandler('SimpleDemo'))

    # Finn OpenHands
    openhands_url = bridge.discover_openhands_url()
    if openhands_url:
        bridge.openhands_url = openhands_url
        print(f'Found OpenHands at: {openhands_url}')
    else:
        print('Could not find OpenHands, using default URL')

    # Koble til
    conversation_id = input(
        "Enter conversation ID (or press Enter for 'demo'): "
    ).strip()
    if not conversation_id:
        conversation_id = 'demo'

    success = await bridge.connect_to_conversation(conversation_id)
    if not success:
        print('Failed to connect to OpenHands')
        return

    print("Connected! Type messages (or 'quit' to exit):")

    try:
        while True:
            user_input = input('> ')
            if user_input.lower() == 'quit':
                break

            if user_input.strip():
                await bridge.send_user_message(user_input)

    except KeyboardInterrupt:
        pass

    finally:
        await bridge.disconnect()
        print('Disconnected from OpenHands')


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'multi':
        print('Running multi-app demo...')
        asyncio.run(demo_multiple_apps())
    else:
        print('Running simple demo...')
        asyncio.run(simple_demo())
