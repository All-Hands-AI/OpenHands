import argparse
import os
import sys
from typing import Optional


def get_api_key() -> Optional[str]:
    """Get the OpenHands API key from environment variable."""
    return os.environ.get('OPENHANDS_API_KEY')


def get_host() -> str:
    """Get the OpenHands host from environment variable or use default."""
    return os.environ.get('OPENHANDS_HOST', 'https://app.all-hands.dev')


def create_team(args: argparse.Namespace) -> None:
    """Create a new team."""
    api_key = get_api_key()
    host = get_host()

    if not api_key:
        print('Error: OPENHANDS_API_KEY environment variable is not set.')
        print('Please set it and try again.')
        sys.exit(1)

    print(f"Creating team '{args.name}' using API at {host}")
    print('This would create a new team with the provided name.')
    # In a real implementation, this would make an API call to create the team


def list_teams(args: argparse.Namespace) -> None:
    """List all teams the user is a member of."""
    api_key = get_api_key()
    host = get_host()

    if not api_key:
        print('Error: OPENHANDS_API_KEY environment variable is not set.')
        print('Please set it and try again.')
        sys.exit(1)

    print(f'Listing teams using API at {host}')
    print('This would list all teams you are a member of.')
    # In a real implementation, this would make an API call to list teams


def join_team(args: argparse.Namespace) -> None:
    """Join an existing team."""
    api_key = get_api_key()
    host = get_host()

    if not api_key:
        print('Error: OPENHANDS_API_KEY environment variable is not set.')
        print('Please set it and try again.')
        sys.exit(1)

    print(f"Joining team with invite code '{args.invite_code}' using API at {host}")
    print('This would join the team associated with the provided invite code.')
    # In a real implementation, this would make an API call to join the team


def main() -> None:
    """Main entry point for the team CLI."""
    parser = argparse.ArgumentParser(description='OpenHands Team Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Create team command
    create_parser = subparsers.add_parser('create', help='Create a new team')
    create_parser.add_argument('name', help='Name of the team to create')
    create_parser.set_defaults(func=create_team)

    # List teams command
    list_parser = subparsers.add_parser(
        'list', help='List all teams you are a member of'
    )
    list_parser.set_defaults(func=list_teams)

    # Join team command
    join_parser = subparsers.add_parser('join', help='Join an existing team')
    join_parser.add_argument('invite_code', help='Invite code for the team')
    join_parser.set_defaults(func=join_team)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
