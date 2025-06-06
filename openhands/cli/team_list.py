"""List conversations command for the OpenHands Team CLI."""

import argparse
import sys
from typing import Optional

from openhands.cli.team import TeamClient


def setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser for the list command.

    Returns:
        The argument parser.
    """
    parser = argparse.ArgumentParser(
        description='List all available conversations',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-l',
        '--limit',
        type=int,
        default=20,
        help='Maximum number of conversations to list',
    )
    parser.add_argument(
        '--url',
        help='OpenHands API URL (default: $OPENHANDS_API_URL or http://localhost:3000)',
    )
    parser.add_argument(
        '--api-key', help='OpenHands API key (default: $OPENHANDS_API_KEY)'
    )
    return parser


async def list_conversations(args: argparse.Namespace) -> None:
    """List conversations command.

    Args:
        args: Command line arguments.
    """
    # Create client
    client = TeamClient(args.url, args.api_key)

    try:
        # List conversations
        await client.list_conversations(limit=args.limit)
    except Exception as e:
        print(f'Error listing conversations: {e}')
        sys.exit(1)


def main(args: Optional[list[str]] = None) -> None:
    """Main function for the list command.

    Args:
        args: Command line arguments.
    """
    parser = setup_parser()
    parsed_args = parser.parse_args(args)

    import asyncio

    asyncio.run(list_conversations(parsed_args))


if __name__ == '__main__':
    main()
