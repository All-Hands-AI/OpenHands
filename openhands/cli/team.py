"""Team CLI interface for OpenHands.

This module provides a CLI interface for interacting with the OpenHands HTTP and WebSocket APIs.
It allows creating conversations and showing the current list of conversations/statuses.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Optional

import aiohttp
import socketio
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import clear
from rich.console import Console
from rich.table import Table

from openhands.cli.tui import (
    display_banner,
    display_event,
    display_welcome_message,
    read_prompt_input,
)
from openhands.core.schema import AgentState
from openhands.events.action import MessageAction
from openhands.events.serialization import event_from_dict, event_to_dict


class TeamClient:
    """Client for interacting with the OpenHands HTTP and WebSocket APIs."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize the TeamClient.

        Args:
            base_url: The base URL for the OpenHands API.
            api_key: Optional API key for authentication.
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.sio = socketio.AsyncClient()
        self.console = Console()
        self.headers = {}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    async def list_conversations(self, limit: int = 20) -> list[dict[str, Any]]:
        """List conversations.

        Args:
            limit: Maximum number of conversations to return.

        Returns:
            List of conversation objects.
        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f'{self.base_url}/api/conversations?limit={limit}'
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f'Failed to list conversations: {error_text}')
                data = await response.json()
                return data.get('results', [])

    async def create_conversation(
        self,
        repository: Optional[str] = None,
        git_provider: Optional[str] = None,
        selected_branch: Optional[str] = None,
        initial_user_msg: Optional[str] = None,
        conversation_instructions: Optional[str] = None,
    ) -> str:
        """Create a new conversation.

        Args:
            repository: Optional repository name (owner/repo).
            git_provider: Optional git provider (github or gitlab).
            selected_branch: Optional branch name.
            initial_user_msg: Optional initial user message.
            conversation_instructions: Optional conversation instructions.

        Returns:
            The conversation ID.
        """
        payload = {
            'repository': repository,
            'git_provider': git_provider,
            'selected_branch': selected_branch,
            'initial_user_msg': initial_user_msg,
            'conversation_instructions': conversation_instructions,
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                f'{self.base_url}/api/conversations', json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f'Failed to create conversation: {error_text}')
                data = await response.json()
                return data.get('conversation_id')

    async def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        """Get conversation details.

        Args:
            conversation_id: The conversation ID.

        Returns:
            Conversation details.
        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f'{self.base_url}/api/conversations/{conversation_id}'
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f'Failed to get conversation: {error_text}')
                return await response.json()

    async def connect_to_conversation(
        self, conversation_id: str, latest_event_id: int = -1
    ) -> None:
        """Connect to a conversation via WebSocket.

        Args:
            conversation_id: The conversation ID.
            latest_event_id: The latest event ID to start from.
        """

        # Set up event handlers
        @self.sio.event
        async def connect():
            self.console.print('[green]Connected to conversation[/green]')

        @self.sio.event
        async def disconnect():
            self.console.print('[yellow]Disconnected from conversation[/yellow]')

        @self.sio.event
        async def oh_event(data):
            event = event_from_dict(data)
            # Create a dummy config object to satisfy the type checker
            from openhands.core.config import OpenHandsConfig

            dummy_config = OpenHandsConfig()
            display_event(event, dummy_config)

        # Connect to the WebSocket
        query = {
            'conversation_id': conversation_id,
            'latest_event_id': str(latest_event_id),
        }
        if self.api_key:
            query['session_api_key'] = self.api_key

        await self.sio.connect(
            f'{self.base_url}',
            headers=self.headers,
            transports=['websocket'],
            socketio_path='socket.io',
            wait_timeout=10,
            query=query,
        )

    async def send_message(self, message: str) -> None:
        """Send a message to the conversation.

        Args:
            message: The message to send.
        """
        event = MessageAction(content=message)
        event_dict = event_to_dict(event)
        await self.sio.emit('oh_user_action', event_dict)

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        await self.sio.disconnect()


async def list_conversations_cmd(client: TeamClient, args: argparse.Namespace) -> None:
    """List conversations command.

    Args:
        client: The TeamClient instance.
        args: Command line arguments.
    """
    conversations = await client.list_conversations(limit=args.limit)

    if not conversations:
        print('No conversations found.')
        return

    table = Table(title='Conversations')
    table.add_column('ID', style='cyan')
    table.add_column('Title', style='green')
    table.add_column('Status', style='magenta')
    table.add_column('Repository', style='blue')
    table.add_column('Last Updated', style='yellow')
    table.add_column('Created', style='yellow')

    for convo in conversations:
        # Format dates
        created_at = datetime.fromisoformat(convo['created_at'].replace('Z', '+00:00'))
        last_updated_at = datetime.fromisoformat(
            convo['last_updated_at'].replace('Z', '+00:00')
        )

        created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
        updated_str = last_updated_at.strftime('%Y-%m-%d %H:%M:%S')

        # Add row to table
        table.add_row(
            convo['conversation_id'],
            convo['title'],
            convo['status'],
            convo.get('selected_repository', ''),
            updated_str,
            created_str,
        )

    client.console.print(table)


async def create_conversation_cmd(client: TeamClient, args: argparse.Namespace) -> None:
    """Create a conversation command.

    Args:
        client: The TeamClient instance.
        args: Command line arguments.
    """
    initial_message = args.message

    # If no message provided, prompt for one
    if not initial_message:
        print_formatted_text(HTML('<green>Enter your initial message:</green>'))
        initial_message = input('> ')

    try:
        conversation_id = await client.create_conversation(
            repository=args.repository,
            git_provider=args.git_provider,
            selected_branch=args.branch,
            initial_user_msg=initial_message,
            conversation_instructions=args.instructions,
        )

        print_formatted_text(
            HTML(f'<green>Conversation created with ID: {conversation_id}</green>')
        )

        if args.join:
            await join_conversation_cmd(
                client, argparse.Namespace(conversation_id=conversation_id)
            )

    except Exception as e:
        print_formatted_text(HTML(f'<red>Error creating conversation: {str(e)}</red>'))


async def join_conversation_cmd(client: TeamClient, args: argparse.Namespace) -> None:
    """Join a conversation command.

    Args:
        client: The TeamClient instance.
        args: Command line arguments.
    """
    conversation_id = args.conversation_id

    try:
        # Get conversation details
        conversation = await client.get_conversation(conversation_id)

        # Clear screen and show banner
        clear()
        display_banner(session_id=conversation_id)

        # Show conversation title
        title = conversation.get('title', 'Untitled Conversation')
        display_welcome_message(f'Joined conversation: {title}')

        # Connect to the WebSocket
        await client.connect_to_conversation(conversation_id)

        # Main conversation loop
        try:
            while True:
                next_message = await read_prompt_input(
                    AgentState.AWAITING_USER_INPUT.value
                )

                if not next_message.strip():
                    continue

                if next_message.lower() in ['exit', 'quit', '/exit', '/quit']:
                    break

                await client.send_message(next_message)

        except KeyboardInterrupt:
            print('\nDisconnecting...')
        finally:
            await client.disconnect()

    except Exception as e:
        print_formatted_text(HTML(f'<red>Error joining conversation: {str(e)}</red>'))


def get_base_url() -> str:
    """Get the base URL for the OpenHands API.

    Returns:
        The base URL.
    """
    # Check environment variables first
    base_url = os.environ.get('OPENHANDS_API_URL')
    if base_url:
        return base_url

    # Default to localhost
    return 'http://localhost:3000'


def get_api_key() -> Optional[str]:
    """Get the API key for authentication.

    Returns:
        The API key, or None if not found.
    """
    return os.environ.get('OPENHANDS_API_KEY')


def setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser for the team CLI.

    Returns:
        The argument parser.
    """
    parser = argparse.ArgumentParser(description='OpenHands Team CLI')
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

    # Server configuration
    parser.add_argument(
        '--url',
        help='OpenHands API URL (default: $OPENHANDS_API_URL or http://localhost:3000)',
    )
    parser.add_argument(
        '--api-key', help='OpenHands API key (default: $OPENHANDS_API_KEY)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # List conversations command
    list_parser = subparsers.add_parser(
        'list',
        help='List conversations',
        description='List all available conversations',
    )
    list_parser.add_argument(
        '-l',
        '--limit',
        type=int,
        default=20,
        help='Maximum number of conversations to list',
    )
    # Add help formatter
    list_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

    # Create conversation command
    create_parser = subparsers.add_parser(
        'create',
        help='Create a new conversation',
        description='Create a new conversation with optional repository and message',
    )
    create_parser.add_argument(
        '-r', '--repository', help='Repository name (owner/repo)'
    )
    create_parser.add_argument(
        '-g', '--git-provider', help='Git provider (github or gitlab)'
    )
    create_parser.add_argument('-b', '--branch', help='Branch name')
    create_parser.add_argument('-m', '--message', help='Initial user message')
    create_parser.add_argument('-i', '--instructions', help='Conversation instructions')
    create_parser.add_argument(
        '-j', '--join', action='store_true', help='Join the conversation after creation'
    )
    # Add help formatter
    create_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

    # Join conversation command
    join_parser = subparsers.add_parser(
        'join',
        help='Join an existing conversation',
        description='Join an existing conversation by ID',
    )
    join_parser.add_argument('conversation_id', help='Conversation ID')
    # Add help formatter
    join_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

    return parser


async def main_async(args: argparse.Namespace) -> None:
    """Main async function for the team CLI.

    Args:
        args: Command line arguments.
    """
    # Get base URL and API key
    base_url = args.url or get_base_url()
    api_key = args.api_key or get_api_key()

    # Create client
    client = TeamClient(base_url, api_key)

    # Run command
    if args.command == 'list':
        await list_conversations_cmd(client, args)
    elif args.command == 'create':
        await create_conversation_cmd(client, args)
    elif args.command == 'join':
        await join_conversation_cmd(client, args)
    else:
        print('No command specified. Use --help for usage information.')


def main(args: Optional[list[str]] = None) -> None:
    """Main function for the team CLI.

    Args:
        args: Command line arguments.
    """
    parser = setup_parser()

    # If no arguments provided, show help
    if not args or len(args) == 0:
        parser.print_help()
        return

    # Handle special case for help with subcommands
    if (
        len(args) >= 2
        and args[0] in ['list', 'create', 'join']
        and args[1] in ['-h', '--help']
    ):
        # Get the subparser for the command
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                if choice == args[0]:
                    subparser.print_help()
                    return

    try:
        parsed_args = parser.parse_args(args)

        # If no command specified, show help
        if not parsed_args.command:
            parser.print_help()
            return

        # Run the command
        asyncio.run(main_async(parsed_args))
    except KeyboardInterrupt:
        print('\nOperation cancelled by user.')
    except Exception as e:
        print(f'Error: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
