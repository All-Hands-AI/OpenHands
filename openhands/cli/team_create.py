"""Create conversation command for the OpenHands Team CLI."""

import argparse
import sys
from typing import Optional

from openhands.cli.team import TeamClient


def setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser for the create command.

    Returns:
        The argument parser.
    """
    parser = argparse.ArgumentParser(
        description='Create a new conversation with optional repository and message',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('-r', '--repository', help='Repository name (owner/repo)')
    parser.add_argument('-g', '--git-provider', help='Git provider (github or gitlab)')
    parser.add_argument('-b', '--branch', help='Branch name')
    parser.add_argument('-m', '--message', help='Initial user message')
    parser.add_argument('-i', '--instructions', help='Conversation instructions')
    parser.add_argument(
        '-j', '--join', action='store_true', help='Join the conversation after creation'
    )
    parser.add_argument(
        '--url',
        help='OpenHands API URL (default: $OPENHANDS_API_URL or http://localhost:3000)',
    )
    parser.add_argument(
        '--api-key', help='OpenHands API key (default: $OPENHANDS_API_KEY)'
    )
    return parser


async def create_conversation(args: argparse.Namespace) -> None:
    """Create a conversation command.

    Args:
        args: Command line arguments.
    """
    # Create client
    client = TeamClient(args.url, args.api_key)

    try:
        # Create conversation
        await client.create_conversation(
            repository=args.repository,
            git_provider=args.git_provider,
            selected_branch=args.branch,
            initial_user_msg=args.message,
            conversation_instructions=args.instructions,
        )
    except Exception as e:
        print(f'Error creating conversation: {e}')
        sys.exit(1)


def main(args: Optional[list[str]] = None) -> None:
    """Main function for the create command.

    Args:
        args: Command line arguments.
    """
    parser = setup_parser()
    parsed_args = parser.parse_args(args)

    import asyncio

    asyncio.run(create_conversation(parsed_args))


if __name__ == '__main__':
    main()
