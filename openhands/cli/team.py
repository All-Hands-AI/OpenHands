import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
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

    # In a real implementation, this would use a dedicated teams API endpoint
    # For now, we'll use a placeholder implementation
    url = f'{host}/api/teams'  # Placeholder URL

    # Prepare the request data
    data = json.dumps({'name': args.name, 'description': args.description}).encode(
        'utf-8'
    )

    # Create the request with the API key in the header
    urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        print(f"Creating team '{args.name}'...")

        # This is a placeholder - in a real implementation, we would make the API call
        # with urllib.request.urlopen(req) as response:
        #     data = json.loads(response.read().decode('utf-8'))
        #     print(f"Team created successfully with ID: {data['team_id']}")

        # For now, just show a placeholder message
        print(f"Team '{args.name}' would be created using API at {host}")
        print('Note: This is a placeholder. The teams API is not yet implemented.')

    except urllib.error.HTTPError as e:
        print(f'Error: HTTP {e.code} - {e.reason}')
        if e.code == 401:
            print('Authentication failed. Please check your API key.')
        elif e.code == 403:
            print("You don't have permission to create teams.")
        else:
            print(f'Server response: {e.read().decode("utf-8")}')

    except urllib.error.URLError as e:
        print(f'Error: Could not connect to the server. {e.reason}')

    except json.JSONDecodeError:
        print('Error: Could not parse the server response as JSON.')

    except Exception as e:
        print(f'Unexpected error: {str(e)}')


def list_teams(args: argparse.Namespace) -> None:
    """List all teams the user is a member of."""
    api_key = get_api_key()
    host = get_host()

    if not api_key:
        print('Error: OPENHANDS_API_KEY environment variable is not set.')
        print('Please set it and try again.')
        sys.exit(1)

    # Set up the request to list conversations
    url = f'{host}/api/conversations'

    # Add query parameters if provided
    params = []
    if args.limit:
        params.append(f'limit={args.limit}')
    if args.page_id:
        params.append(f'page_id={args.page_id}')

    if params:
        url += '?' + '&'.join(params)

    # Create the request with the API key in the header
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
    )

    try:
        # Make the API call
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

            # Check if we have results
            if not data.get('results'):
                print('No conversations found.')
                return

            # Filter conversations based on status if --all is not specified
            filtered_results = data['results']
            if not args.all:
                filtered_results = [
                    conv for conv in data['results'] if conv['status'] == 'RUNNING'
                ]

                if not filtered_results:
                    print('No running conversations found.')
                    print('Use --all to show all conversations including stopped ones.')
                    return

            # Print the conversations in a formatted table
            status_text = 'All' if args.all else 'Running'
            print(f'\nYour {status_text} Conversations:')
            print('-' * 100)
            print(
                f'{"ID":<24} {"Title":<30} {"Status":<10} {"Repository":<20} {"Last Updated":<20}'
            )
            print('-' * 100)

            for conv in filtered_results:
                # Format the date
                last_updated = datetime.fromisoformat(
                    conv['last_updated_at'].replace('Z', '+00:00')
                )
                formatted_date = last_updated.strftime('%Y-%m-%d %H:%M:%S')

                # Format the repository name (if available)
                repo = conv.get('selected_repository', 'N/A')
                if repo is None:
                    repo = 'N/A'

                # Print the conversation details
                print(
                    f'{conv["conversation_id"]:<24} {conv["title"][:28]:<30} {conv["status"]:<10} {repo[:18]:<20} {formatted_date:<20}'
                )

            # Print pagination info if available
            if data.get('next_page_id'):
                print(
                    f'\nMore results available. Use --page-id={data["next_page_id"]} to see the next page.'
                )

    except urllib.error.HTTPError as e:
        print(f'Error: HTTP {e.code} - {e.reason}')
        if e.code == 401:
            print('Authentication failed. Please check your API key.')
        elif e.code == 403:
            print("You don't have permission to access this resource.")
        else:
            print(f'Server response: {e.read().decode("utf-8")}')

    except urllib.error.URLError as e:
        print(f'Error: Could not connect to the server. {e.reason}')

    except json.JSONDecodeError:
        print('Error: Could not parse the server response as JSON.')

    except Exception as e:
        print(f'Unexpected error: {str(e)}')


def join_team(args: argparse.Namespace) -> None:
    """Join an existing team."""
    api_key = get_api_key()
    host = get_host()

    if not api_key:
        print('Error: OPENHANDS_API_KEY environment variable is not set.')
        print('Please set it and try again.')
        sys.exit(1)

    # In a real implementation, this would use a dedicated teams API endpoint
    # For now, we'll use a placeholder implementation
    url = f'{host}/api/teams/join'  # Placeholder URL

    # Prepare the request data
    data = json.dumps({'invite_code': args.invite_code}).encode('utf-8')

    # Create the request with the API key in the header
    urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        print(f"Joining team with invite code '{args.invite_code}'...")

        # This is a placeholder - in a real implementation, we would make the API call
        # with urllib.request.urlopen(req) as response:
        #     data = json.loads(response.read().decode('utf-8'))
        #     print(f"Successfully joined team: {data['team_name']}")

        # For now, just show a placeholder message
        print(
            f"Would join team with invite code '{args.invite_code}' using API at {host}"
        )
        print('Note: This is a placeholder. The teams API is not yet implemented.')

    except urllib.error.HTTPError as e:
        print(f'Error: HTTP {e.code} - {e.reason}')
        if e.code == 401:
            print('Authentication failed. Please check your API key.')
        elif e.code == 403:
            print("You don't have permission to join this team.")
        elif e.code == 404:
            print('Invalid invite code. Please check and try again.')
        else:
            print(f'Server response: {e.read().decode("utf-8")}')

    except urllib.error.URLError as e:
        print(f'Error: Could not connect to the server. {e.reason}')

    except json.JSONDecodeError:
        print('Error: Could not parse the server response as JSON.')

    except Exception as e:
        print(f'Unexpected error: {str(e)}')


def main() -> None:
    """Main entry point for the team CLI."""
    parser = argparse.ArgumentParser(description='OpenHands Team Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Create team command
    create_parser = subparsers.add_parser('create', help='Create a new team')
    create_parser.add_argument('name', help='Name of the team to create')
    create_parser.add_argument(
        '--description', help='Description of the team (optional)'
    )
    create_parser.set_defaults(func=create_team)

    # List teams command
    list_parser = subparsers.add_parser(
        'list', help='List all teams you are a member of'
    )
    list_parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of conversations to display (default: 20)',
    )
    list_parser.add_argument(
        '--page-id', help='Page ID for pagination when there are more results'
    )
    list_parser.add_argument(
        '--all',
        action='store_true',
        help='Show all conversations including stopped ones (default: show only running)',
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
