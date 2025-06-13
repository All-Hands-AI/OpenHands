import argparse
import asyncio
import json
import os
import threading
import time
from typing import List, Optional

import requests
import socketio
import uvloop
from prompt_toolkit import HTML, print_formatted_text

# Import required functions and classes from the first file
from openhands.core.cli import (
    DEFAULT_STYLE,
    UsageMetrics,
    display_message,
    shutdown,
    update_usage_metrics,
)
from openhands.core.schema.research import ResearchMode
from openhands.events.event import Event, EventSource
from openhands.llm.metrics import Metrics

# Configuration
API_BASE_URL = 'http://localhost:3000'
SYSTEM_PROMPT = 'You are a helpful AI assistant.'
DEFAULT_PROMPT = 'What’s the ORAI balance of these wallets: orai1f6q9wjn8qp3ll8y8ztd8290vtec2yxyx0wnd0d, orai179dea42h80arp69zd779zcav5jp0kv04zx4h09, orai1f7wcl8drgvyvhzylu54gphul0st2x87kdn6g6k, orai1unpv9tsw7d27n7wym83z4lajh4pt252jsvwgvf, orai1qv5jn7tueeqw7xqdn5rem7s09n7zletrsnc5vq, orai12ru3276mkzuuay6vhmg3t6z9hpvrsnpljq7v75, orai1azu0pge4yx6j6sd0tn8nz4x9vj7l9kga8y3arf,orai1uer4mwcq2vlt8l23ncwyjj70mug5pzx8et6u9a,orai1g35xkqtjfxw88rud2je2jyrshrdyrxv4vcu7zt,orai1mfdn23y2ydnp6j3l3f8rw6r2gzazrmprm49h8v,orai18wpvqfu9g0n8x3ysu72fcdtwz025tvg72nxll0,orai155svs6sgxe55rnvs6ghprt'
# Create a SocketIO client
sio = socketio.AsyncClient()


async def join_conversation(conversation_id: str, public_address: str):
    # Initialize usage metrics
    usage_metrics = UsageMetrics()
    metrics_lock = threading.Lock()
    sid = conversation_id  # Use conversation_id as session_id for shutdown
    metrics = Metrics(model_name='default')

    # Helper to run update_usage_metrics with lock
    def update_metrics_with_lock():
        with metrics_lock:
            event = Event()
            event.llm_metrics = metrics
            update_usage_metrics(event, usage_metrics)

    # Create query string with parameters
    query_string = (
        f'conversation_id={conversation_id}'
        f'&auth={public_address}'
        f'&latest_event_id=-1'
        f'&mode=normal'
    )

    try:
        # Connect to the server with query string
        await sio.connect(
            f'{API_BASE_URL}?{query_string}',
            socketio_path='/socket.io',
            transports=['websocket'],
            namespaces='/',
        )
        display_message(f'Connected with sid: {sio.sid}')

        # Handle connection events
        @sio.event
        async def connect():
            display_message('Connection established')

        @sio.event
        async def disconnect():
            display_message('Disconnected from server')
            # Run shutdown in executor to handle synchronous prompt_toolkit calls
            update_metrics_with_lock()
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: shutdown(usage_metrics, sid)
            )

        @sio.event
        async def oh_event(data):
            # Create an Event object using the provided dataclass
            event = Event()
            event._source = data.get('source', '')
            event._message = data.get('content', '')

            # Populate llm_metrics if available
            if event._source:
                if 'llm_metrics' in data:
                    llm_metrics = data['llm_metrics']
                    print('event data: ', json.dumps(data))
                    metrics.reset()
                    cost = llm_metrics.get('accumulated_cost', 0.0)
                    token_data = llm_metrics.get('accumulated_token_usage', {})
                    metrics.add_cost(cost)
                    metrics.add_token_usage(
                        prompt_tokens=token_data.get('prompt_tokens', 0),
                        completion_tokens=token_data.get('completion_tokens', 0),
                        cache_read_tokens=token_data.get('cache_read_tokens', 0),
                        cache_write_tokens=token_data.get('cache_write_tokens', 0),
                        response_id=token_data.get('response_id', ''),
                    )
                    print('llm_metrics: ', metrics)

                # Display agent messages, mimicking MessageAction handling
                if event.source == EventSource.AGENT and event.message:
                    display_message(event.message)

        # Start the CLI input loop in a separate task
        async def cli_input_loop():
            while True:
                try:
                    user_input = await asyncio.to_thread(
                        input, 'Enter message (or Ctrl+C to exit): '
                    )
                    if user_input.strip():
                        await sio.emit(
                            'oh_user_action',
                            {
                                'action': 'message',
                                'args': {
                                    'content': user_input,
                                    'timestamp': time.time(),
                                    'mode': ResearchMode.DEEP_RESEARCH,
                                },
                            },
                        )
                        display_message(f'Sent message: {user_input}')
                except KeyboardInterrupt:
                    print_formatted_text(
                        HTML('<grey>Received Ctrl+C, disconnecting...</grey>'),
                        style=DEFAULT_STYLE,
                    )
                    await sio.disconnect()
                    break
                except Exception as e:
                    display_message(f'Error in CLI input: {e}')

        input_task = asyncio.create_task(cli_input_loop())
        await sio.wait()
        await input_task

    except socketio.exceptions.ConnectionError as e:
        display_message(f'Connection failed: {e}')
        # Run shutdown to display metrics on connection failure
        update_metrics_with_lock()
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: shutdown(usage_metrics, sid)
        )
    except Exception as e:
        display_message(f'Error: {e}')
        update_metrics_with_lock()
        # Run shutdown to display metrics on general error
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: shutdown(usage_metrics, sid)
        )


def create_conversation(
    initial_user_msg: Optional[str] = None,
    image_urls: Optional[List[str]] = None,
    selected_repository: Optional[dict] = None,
    selected_branch: Optional[str] = None,
    replay_json: Optional[str] = None,
    public_address: Optional[str] = None,
    user_prompt: Optional[str] = None,
    research_mode: Optional[ResearchMode] = None,
) -> dict:
    payload = {
        'initial_user_msg': initial_user_msg,
        'image_urls': image_urls or [],
        'selected_repository': selected_repository,
        'selected_branch': selected_branch,
        'replay_json': replay_json,
        'user_prompt': user_prompt,
        'research_mode': research_mode,
    }
    headers = {
        'Authorization': f'Bearer {public_address}',
        'Content-Type': 'application/json',
    }
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/conversations', json=payload, headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f'HTTP Error: {e.response.json()}')
        raise e
    except requests.exceptions.RequestException as e:
        print(f'Request Error: {e}')
        raise e


if __name__ == '__main__':
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(
            description='Run the A2A Agent with a custom prompt'
        )
        parser.add_argument(
            '--prompt', type=str, help='Custom prompt to send to the agent'
        )
        args = parser.parse_args()
        # Use the provided prompt or the default one
        prompt = args.prompt if args.prompt else DEFAULT_PROMPT
        public_address = '0x11A87E9d573597d5A4271272df09C1177F34bEbC'
        conversation_id = os.getenv('CONVERSATION_ID')
        if not conversation_id:
            new_conversation_response = create_conversation(
                initial_user_msg=prompt,
                image_urls=[],
                selected_repository=None,
                selected_branch=None,
                replay_json=None,
                public_address=public_address,
                research_mode=ResearchMode.DEEP_RESEARCH,
            )
            conversation_id = new_conversation_response['conversation_id']
        display_message(f'Conversation created with ID: {conversation_id}')
        uvloop.run(
            join_conversation(
                conversation_id=conversation_id, public_address=public_address
            )
        )
    except Exception as e:
        display_message(f'Error: {e}')
