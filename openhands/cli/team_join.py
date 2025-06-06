"""Join conversation command for the OpenHands Team CLI."""

import argparse
import sys
from typing import Optional

from openhands.cli.team import TeamClient, join_conversation_cmd


def setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser for the join command.

    Returns:
        The argument parser.
    """
    parser = argparse.ArgumentParser(
        description='Join an existing conversation by ID',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('conversation_id', help='Conversation ID')
    parser.add_argument(
        '--url',
        help='OpenHands API URL (default: $OPENHANDS_API_URL or http://localhost:3000)',
    )
    parser.add_argument(
        '--api-key', help='OpenHands API key (default: $OPENHANDS_API_KEY)'
    )
    return parser


async def join_conversation(args: argparse.Namespace) -> None:
    """Join a conversation command.

    Args:
        args: Command line arguments.
    """
    # Create client
    client = TeamClient(args.url, args.api_key)

    try:
        # Join conversation
        await join_conversation_cmd(client, args)
    except Exception as e:
        print(f'Error joining conversation: {e}')
        sys.exit(1)


def main(args: Optional[list[str]] = None) -> None:
    """Main function for the join command.

    Args:
        args: Command line arguments.
    """
    parser = setup_parser()
    parsed_args = parser.parse_args(args)

    import asyncio

    asyncio.run(join_conversation(parsed_args))


if __name__ == '__main__':
    main()
