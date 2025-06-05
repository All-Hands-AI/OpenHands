#!/usr/bin/env python3
"""
OpenHands Communication Bridge

En bridge som kan koble seg på OpenHands kommunikasjonskanaler
og videresende meldinger til eksterne applikasjoner.

Fungerer både når OpenHands kjører lokalt og i Docker.
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

import requests
import socketio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OpenHandsMessage:
    """Representerer en melding mellom bruker og OpenHands"""

    direction: str  # 'user_to_agent' eller 'agent_to_user'
    message_type: str  # 'action', 'observation', etc.
    content: dict[str, Any]
    timestamp: float
    conversation_id: str
    connection_id: Optional[str] = None


class BridgeHandler(ABC):
    """Abstract base class for å håndtere meldinger fra OpenHands"""

    @abstractmethod
    async def handle_user_input(self, message: OpenHandsMessage) -> None:
        """Håndter input fra bruker til OpenHands"""
        pass

    @abstractmethod
    async def handle_agent_output(self, message: OpenHandsMessage) -> None:
        """Håndter output fra OpenHands til bruker"""
        pass

    @abstractmethod
    async def handle_error(self, error: str, context: dict[str, Any]) -> None:
        """Håndter feil"""
        pass


class LoggingBridgeHandler(BridgeHandler):
    """Enkel handler som logger alle meldinger"""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        if log_file:
            self.file_handler = open(log_file, 'a', encoding='utf-8')

    async def handle_user_input(self, message: OpenHandsMessage) -> None:
        log_msg = f'[USER→AGENT] {message.timestamp}: {json.dumps(message.content, ensure_ascii=False)}'
        logger.info(log_msg)
        if hasattr(self, 'file_handler'):
            self.file_handler.write(log_msg + '\n')
            self.file_handler.flush()

    async def handle_agent_output(self, message: OpenHandsMessage) -> None:
        log_msg = f'[AGENT→USER] {message.timestamp}: {json.dumps(message.content, ensure_ascii=False)}'
        logger.info(log_msg)
        if hasattr(self, 'file_handler'):
            self.file_handler.write(log_msg + '\n')
            self.file_handler.flush()

    async def handle_error(self, error: str, context: dict[str, Any]) -> None:
        log_msg = f'[ERROR] {time.time()}: {error} - Context: {json.dumps(context, ensure_ascii=False)}'
        logger.error(log_msg)
        if hasattr(self, 'file_handler'):
            self.file_handler.write(log_msg + '\n')
            self.file_handler.flush()


class WebSocketBridgeHandler(BridgeHandler):
    """Handler som sender meldinger til en WebSocket server"""

    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.sio = socketio.AsyncClient()
        self.connected = False

    async def connect(self):
        try:
            await self.sio.connect(self.websocket_url)
            self.connected = True
            logger.info(f'Connected to WebSocket: {self.websocket_url}')
        except Exception as e:
            logger.error(f'Failed to connect to WebSocket: {e}')
            self.connected = False

    async def handle_user_input(self, message: OpenHandsMessage) -> None:
        if self.connected:
            await self.sio.emit('openhands_user_input', message.__dict__)

    async def handle_agent_output(self, message: OpenHandsMessage) -> None:
        if self.connected:
            await self.sio.emit('openhands_agent_output', message.__dict__)

    async def handle_error(self, error: str, context: dict[str, Any]) -> None:
        if self.connected:
            await self.sio.emit('openhands_error', {'error': error, 'context': context})


class HTTPBridgeHandler(BridgeHandler):
    """Handler som sender meldinger til HTTP endpoints"""

    def __init__(self, base_url: str, timeout: int = 5):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

    async def handle_user_input(self, message: OpenHandsMessage) -> None:
        try:
            response = self.session.post(
                f'{self.base_url}/user_input',
                json=message.__dict__,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f'Failed to send user input to HTTP endpoint: {e}')

    async def handle_agent_output(self, message: OpenHandsMessage) -> None:
        try:
            response = self.session.post(
                f'{self.base_url}/agent_output',
                json=message.__dict__,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f'Failed to send agent output to HTTP endpoint: {e}')

    async def handle_error(self, error: str, context: dict[str, Any]) -> None:
        try:
            response = self.session.post(
                f'{self.base_url}/error',
                json={'error': error, 'context': context},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f'Failed to send error to HTTP endpoint: {e}')


class OpenHandsBridge:
    """Hovedklasse for OpenHands Bridge"""

    def __init__(self, openhands_url: str = 'http://localhost:3000'):
        self.openhands_url = openhands_url
        self.handlers: list[BridgeHandler] = []
        self.sio = socketio.AsyncClient()
        self.connected = False
        self.conversation_id = None
        self.connection_id = None

        # Setup event handlers
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('oh_event', self._on_oh_event)

    def add_handler(self, handler: BridgeHandler):
        """Legg til en handler for å behandle meldinger"""
        self.handlers.append(handler)

    async def _on_connect(self):
        """Callback når WebSocket kobler til"""
        self.connected = True
        logger.info('Connected to OpenHands WebSocket')

    async def _on_disconnect(self):
        """Callback når WebSocket kobler fra"""
        self.connected = False
        logger.info('Disconnected from OpenHands WebSocket')

    async def _on_oh_event(self, data):
        """Callback for OpenHands events (agent output)"""
        try:
            message = OpenHandsMessage(
                direction='agent_to_user',
                message_type=data.get('action', 'unknown'),
                content=data,
                timestamp=time.time(),
                conversation_id=self.conversation_id or 'unknown',
                connection_id=self.connection_id,
            )

            # Send til alle handlers
            for handler in self.handlers:
                try:
                    await handler.handle_agent_output(message)
                except Exception as e:
                    logger.error(f'Handler error: {e}')
                    await handler.handle_error(str(e), {'message': message.__dict__})

        except Exception as e:
            logger.error(f'Error processing oh_event: {e}')

    async def connect_to_conversation(
        self, conversation_id: str, latest_event_id: int = -1
    ):
        """Koble til en spesifikk samtale"""
        self.conversation_id = conversation_id

        # Bygg WebSocket URL
        parsed = urlparse(self.openhands_url)
        ws_scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        ws_url = f'{ws_scheme}://{parsed.netloc}/socket.io/'

        query_params = {
            'conversation_id': conversation_id,
            'latest_event_id': latest_event_id,
        }

        try:
            await self.sio.connect(
                ws_url, socketio_path='/socket.io/', query=query_params
            )
            logger.info(f'Connected to conversation: {conversation_id}')
            return True
        except Exception as e:
            logger.error(f'Failed to connect to conversation: {e}')
            return False

    async def send_user_message(self, message: str, message_type: str = 'message'):
        """Send en melding fra bruker til OpenHands"""
        if not self.connected:
            logger.error('Not connected to OpenHands')
            return False

        try:
            user_data = {
                'action': message_type,
                'args': {'content': message} if message_type == 'message' else message,
                'timestamp': time.time(),
            }

            # Send til OpenHands
            await self.sio.emit('oh_user_action', user_data)

            # Opprett melding for handlers
            bridge_message = OpenHandsMessage(
                direction='user_to_agent',
                message_type=message_type,
                content=user_data,
                timestamp=time.time(),
                conversation_id=self.conversation_id or 'unknown',
                connection_id=self.connection_id,
            )

            # Send til alle handlers
            for handler in self.handlers:
                try:
                    await handler.handle_user_input(bridge_message)
                except Exception as e:
                    logger.error(f'Handler error: {e}')
                    await handler.handle_error(
                        str(e), {'message': bridge_message.__dict__}
                    )

            return True

        except Exception as e:
            logger.error(f'Failed to send user message: {e}')
            return False

    async def disconnect(self):
        """Koble fra OpenHands"""
        if self.connected:
            await self.sio.disconnect()

    def discover_openhands_url(self) -> Optional[str]:
        """Prøv å finne OpenHands URL automatisk"""

        # Sjekk vanlige porter
        common_ports = [3000, 8000, 8080, 12000, 12001]
        common_hosts = ['localhost', '127.0.0.1']

        # Sjekk om vi kjører i Docker og kan finne OpenHands container
        if self._is_running_in_docker():
            docker_hosts = self._find_openhands_in_docker()
            common_hosts.extend(docker_hosts)

        for host in common_hosts:
            for port in common_ports:
                url = f'http://{host}:{port}'
                if self._test_openhands_connection(url):
                    logger.info(f'Found OpenHands at: {url}')
                    return url

        return None

    def _is_running_in_docker(self) -> bool:
        """Sjekk om vi kjører i Docker"""
        return os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')

    def _find_openhands_in_docker(self) -> list[str]:
        """Finn OpenHands containers i Docker nettverk"""
        hosts = []
        try:
            # Prøv å finne via Docker API eller nettverk discovery
            # Dette er en forenklet versjon
            import subprocess

            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'openhands' in line.lower():
                        hosts.append(line.strip())
        except Exception:
            pass

        return hosts

    def _test_openhands_connection(self, url: str) -> bool:
        """Test om OpenHands kjører på gitt URL"""
        try:
            response = requests.get(f'{url}/api/health', timeout=2)
            return response.status_code == 200
        except Exception:
            return False


class BridgeServer:
    """HTTP server for å motta meldinger fra eksterne applikasjoner"""

    def __init__(self, bridge: OpenHandsBridge, port: int = 8888):
        self.bridge = bridge
        self.port = port
        self.app = None

    def start(self):
        """Start HTTP server"""
        try:
            from flask import Flask, jsonify, request

            self.app = Flask(__name__)

            @self.app.route('/send_message', methods=['POST'])
            def send_message():
                data = request.get_json()
                message = data.get('message', '')
                message_type = data.get('type', 'message')

                # Send asynkront
                asyncio.create_task(
                    self.bridge.send_user_message(message, message_type)
                )

                return jsonify({'status': 'sent'})

            @self.app.route('/status', methods=['GET'])
            def status():
                return jsonify(
                    {
                        'connected': self.bridge.connected,
                        'conversation_id': self.bridge.conversation_id,
                    }
                )

            # Start server i egen tråd
            def run_server():
                self.app.run(host='0.0.0.0', port=self.port, debug=False)

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            logger.info(f'Bridge HTTP server started on port {self.port}')

        except ImportError:
            logger.warning('Flask not available, HTTP server disabled')


def load_config(config_path: str = None) -> dict:
    """Last konfigurasjon fra fil"""
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f'Failed to load config from {config_path}: {e}')

    # Default config
    return {
        'openhands_urls': [],
        'bridge_settings': {
            'auto_discover': True,
            'retry_attempts': 3,
            'retry_delay': 5,
            'log_level': 'INFO',
        },
        'handlers': {
            'logging': {'enabled': True, 'log_file': '/tmp/openhands_bridge.log'}
        },
    }


async def main():
    """Hovedfunksjon for testing"""
    import argparse

    parser = argparse.ArgumentParser(description='OpenHands Bridge')
    parser.add_argument('--url', help='OpenHands URL')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--conversation-id', help='Conversation ID to connect to')
    parser.add_argument(
        '--server-port', type=int, default=8888, help='HTTP server port'
    )
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')

    args = parser.parse_args()

    # Last konfigurasjon
    config = load_config(args.config)

    # Opprett bridge
    bridge = OpenHandsBridge(args.url or 'http://localhost:3000')

    # Prøv å finne OpenHands automatisk hvis ikke spesifisert
    if not args.url and config['bridge_settings']['auto_discover']:
        openhands_url = bridge.discover_openhands_url()
        if openhands_url:
            bridge.openhands_url = openhands_url
        elif config['openhands_urls']:
            # Prøv URLs fra config
            for url in config['openhands_urls']:
                if bridge._test_openhands_connection(url):
                    bridge.openhands_url = url
                    break

    # Legg til handlers basert på config
    if config['handlers']['logging']['enabled']:
        log_file = config['handlers']['logging'].get(
            'log_file', '/tmp/openhands_bridge.log'
        )
        bridge.add_handler(LoggingBridgeHandler(log_file))

    if config['handlers'].get('websocket', {}).get('enabled'):
        ws_url = config['handlers']['websocket']['url']
        ws_handler = WebSocketBridgeHandler(ws_url)
        await ws_handler.connect()
        bridge.add_handler(ws_handler)

    if config['handlers'].get('http', {}).get('enabled'):
        http_url = config['handlers']['http']['url']
        bridge.add_handler(HTTPBridgeHandler(http_url))

    # Start HTTP server
    server = BridgeServer(bridge, args.server_port)
    server.start()

    logger.info(f'Bridge server started on port {args.server_port}')
    logger.info(f'OpenHands URL: {bridge.openhands_url}')

    if args.daemon:
        # Daemon mode - kjør kontinuerlig
        logger.info('Running in daemon mode')

        # Prøv å koble til default conversation
        conversation_id = args.conversation_id or 'bridge-daemon'
        success = await bridge.connect_to_conversation(conversation_id)

        if success:
            logger.info(f'Connected to conversation: {conversation_id}')

            # Hold programmet kjørende
            try:
                while True:
                    await asyncio.sleep(10)
                    if not bridge.connected:
                        logger.warning('Lost connection, attempting to reconnect...')
                        await bridge.connect_to_conversation(conversation_id)
            except KeyboardInterrupt:
                logger.info('Shutting down...')
        else:
            logger.error('Failed to connect in daemon mode')

    else:
        # Interaktiv mode
        conversation_id = args.conversation_id
        if not conversation_id:
            conversation_id = input(
                'Enter conversation ID (or press Enter for demo): '
            ).strip()
            if not conversation_id:
                conversation_id = 'demo-conversation'

        success = await bridge.connect_to_conversation(conversation_id)
        if not success:
            logger.error('Failed to connect to OpenHands')
            return

        print("Connected! Type messages (or 'quit' to exit):")

        # Hold programmet kjørende
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
            logger.info('Bridge disconnected')


if __name__ == '__main__':
    # Installer nødvendige pakker hvis de mangler
    try:
        import requests
        import socketio
    except ImportError:
        print('Installing required packages...')
        import subprocess

        subprocess.check_call(
            [
                sys.executable,
                '-m',
                'pip',
                'install',
                'python-socketio[asyncio]',
                'requests',
            ]
        )
        import requests
        import socketio

    # Kjør main
    asyncio.run(main())
