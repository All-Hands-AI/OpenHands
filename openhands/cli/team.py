import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional


def format_time_ago(dt: datetime) -> str:
    """Format a datetime as a human-readable 'time ago' string."""
    now = datetime.now(timezone.utc)
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:  # 7 days
        days = int(seconds // 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif seconds < 2592000:  # 30 days
        weeks = int(seconds // 604800)
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'
    elif seconds < 31536000:  # 365 days
        months = int(seconds // 2592000)
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = int(seconds // 31536000)
        return f'{years} year{"s" if years != 1 else ""} ago'


def get_api_key() -> Optional[str]:
    """Get the OpenHands API key from environment variable."""
    return os.environ.get('OPENHANDS_API_KEY')


def get_host() -> str:
    """Get the OpenHands host from environment variable or use default."""
    return os.environ.get('OPENHANDS_HOST', 'https://app.all-hands.dev')


def create_conversation(args: argparse.Namespace) -> None:
    """Create a new conversation."""
    api_key = get_api_key()
    host = get_host()

    # Define colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    GRAY = '\033[90m'
    RED = '\033[31m'

    if not api_key:
        print(f'{RED}Error: OPENHANDS_API_KEY environment variable is not set.{RESET}')
        print(f'{YELLOW}Please set it and try again.{RESET}')
        sys.exit(1)

    # Use the conversations API endpoint
    url = f'{host}/api/conversations'

    # Use the message directly as the initial user message
    # Prepare the request data
    request_data = {
        'initial_user_msg': args.message,
    }

    # Add repository if specified
    if args.repository:
        request_data['repository'] = args.repository

        # Add git provider if specified
        if args.git_provider:
            request_data['git_provider'] = args.git_provider

        # Add branch if specified
        if args.branch:
            request_data['selected_branch'] = args.branch

    # Encode the data
    data = json.dumps(request_data).encode('utf-8')

    # Create the request with the API key in the header
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        print(f"{BOLD}Creating conversation with message: '{args.message}'...{RESET}")

        # Make the API call
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))

            if response_data.get('status') == 'ok' and response_data.get(
                'conversation_id'
            ):
                conversation_id = response_data['conversation_id']
                conversation_url = f'{host}/conversations/{conversation_id}'

                print(f'\n{GREEN}Conversation created successfully!{RESET}')
                print(f'\n{BOLD}Conversation Details:{RESET}')
                print(f'  {GRAY}Initial Message:{RESET} {args.message}')
                if args.repository:
                    print(f'  {GRAY}Repository:{RESET} {args.repository}')
                    if args.branch:
                        print(f'  {GRAY}Branch:{RESET} {args.branch}')

                print(f'\n{BOLD}Access your conversation at:{RESET}')
                print(f'  {BLUE}{conversation_url}{RESET}')

                # Print the short ID for reference
                short_id = conversation_id[:6]
                print(f'\n{GRAY}Conversation ID: {CYAN}{short_id}{RESET}')
            else:
                print(
                    f'{RED}Error creating conversation: {response_data.get("message", "Unknown error")}{RESET}'
                )

    except urllib.error.HTTPError as e:
        print(f'{RED}Error: HTTP {e.code} - {e.reason}{RESET}')
        if e.code == 401:
            print(f'{YELLOW}Authentication failed. Please check your API key.{RESET}')
        elif e.code == 403:
            print(f"{YELLOW}You don't have permission to create conversations.{RESET}")
        else:
            print(f'{GRAY}Server response: {e.read().decode("utf-8")}{RESET}')

    except urllib.error.URLError as e:
        print(f'{RED}Error: Could not connect to the server. {e.reason}{RESET}')

    except json.JSONDecodeError:
        print(f'{RED}Error: Could not parse the server response as JSON.{RESET}')

    except Exception as e:
        print(f'{RED}Unexpected error: {str(e)}{RESET}')


def list_conversations(args: argparse.Namespace) -> None:
    """List all conversations the user is a member of."""
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

    # Define colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    GRAY = '\033[90m'
    RED = '\033[31m'

    try:
        # Make the API call
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

            # Check if we have results
            if not data.get('results'):
                print(f'{YELLOW}No conversations found.{RESET}')
                return

            # Filter conversations based on status if --all is not specified
            filtered_results = data['results']
            if not args.all:
                filtered_results = [
                    conv for conv in data['results'] if conv['status'] == 'RUNNING'
                ]

                if not filtered_results:
                    print(f'{YELLOW}No running conversations found.{RESET}')
                    print(
                        f'{GRAY}Use {CYAN}--all{GRAY} to show all conversations including stopped ones.{RESET}'
                    )
                    return

            # Print the conversations in a formatted table
            status_text = 'All' if args.all else 'Running'
            print(f'\n{BOLD}Your {status_text} Conversations:{RESET}')
            print('-' * 150)
            print(
                f'{BOLD}{"ID":<10} {"Title":<25} {"Status":<10} {"Repository":<50} {"Branch":<15} {"Last Updated":<20}{RESET}'
            )
            print('-' * 150)

            for conv in filtered_results:
                # Format the date
                last_updated = datetime.fromisoformat(
                    conv['last_updated_at'].replace('Z', '+00:00')
                )
                time_ago = format_time_ago(last_updated)

                # Format the repository name (if available)
                repo = conv.get('selected_repository', 'N/A')
                if repo is None:
                    repo = 'N/A'

                # Format the branch name (if available)
                branch = conv.get('selected_branch', 'N/A')
                if branch is None:
                    branch = 'N/A'

                # Get the short ID (first 6 characters)
                full_id = conv['conversation_id']
                short_id = full_id[:6]

                # Set status color
                status_color = GREEN if conv['status'] == 'RUNNING' else GRAY

                # Print the conversation details
                print(
                    f'{CYAN}{short_id:<10}{RESET} '
                    f'{BOLD}{conv["title"][:23]:<25}{RESET} '
                    f'{status_color}{conv["status"]:<10}{RESET} '
                    f'{BLUE}{repo[:48]:<50}{RESET} '
                    f'{YELLOW}{branch[:13]:<15}{RESET} '
                    f'{GRAY}{time_ago:<20}{RESET}'
                )

                # Print the URL underneath
                conversation_url = f'{host}/conversations/{full_id}'
                print(f'  {GRAY}URL: {BLUE}{conversation_url}{RESET}')
                print('')  # Empty line for better readability

            # Print pagination info if available
            if data.get('next_page_id'):
                print(
                    f'\n{GRAY}More results available. Use {CYAN}--page-id={data["next_page_id"]}{GRAY} to see the next page.{RESET}'
                )

    except urllib.error.HTTPError as e:
        print(f'{RED}Error: HTTP {e.code} - {e.reason}{RESET}')
        if e.code == 401:
            print(f'{YELLOW}Authentication failed. Please check your API key.{RESET}')
        elif e.code == 403:
            print(f"{YELLOW}You don't have permission to access this resource.{RESET}")
        else:
            print(f'{GRAY}Server response: {e.read().decode("utf-8")}{RESET}')

    except urllib.error.URLError as e:
        print(f'{RED}Error: Could not connect to the server. {e.reason}{RESET}')

    except json.JSONDecodeError:
        print(f'{RED}Error: Could not parse the server response as JSON.{RESET}')

    except Exception as e:
        print(f'{RED}Unexpected error: {str(e)}{RESET}')


def join_conversation(args: argparse.Namespace) -> None:
    """Join an existing conversation using an invite code."""
    api_key = get_api_key()
    host = get_host()

    # Define colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    GRAY = '\033[90m'
    RED = '\033[31m'

    if not api_key:
        print(f'{RED}Error: OPENHANDS_API_KEY environment variable is not set.{RESET}')
        print(f'{YELLOW}Please set it and try again.{RESET}')
        sys.exit(1)

    # For now, we'll treat the invite code as the conversation ID
    # In a real implementation, there would be a dedicated endpoint for invite codes
    conversation_id = args.invite_code

    # First, check if the conversation exists
    url = f'{host}/api/conversations/{conversation_id}'

    # Create the request with the API key in the header
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
    )

    try:
        print(
            f"{BOLD}Joining conversation with invite code '{args.invite_code}'...{RESET}"
        )

        # Make the API call to get conversation details
        with urllib.request.urlopen(req) as response:
            conversation_data = json.loads(response.read().decode('utf-8'))

            # If we get here, the conversation exists
            conversation_url = f'{host}/conversations/{conversation_id}'

            # Now create a message to join the conversation
            join_url = f'{host}/api/conversations/{conversation_id}/messages'
            join_data = json.dumps(
                {'content': 'I would like to join this conversation.', 'role': 'user'}
            ).encode('utf-8')

            join_req = urllib.request.Request(
                join_url,
                data=join_data,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                method='POST',
            )

            # Send the join message
            with urllib.request.urlopen(join_req) as join_response:
                json.loads(join_response.read().decode('utf-8'))

                # Display success message
                print(f'\n{GREEN}Successfully joined the conversation!{RESET}')

                # Display conversation details
                print(f'\n{BOLD}Conversation Details:{RESET}')
                print(
                    f'  {GRAY}Name:{RESET} {conversation_data.get("title", "Unnamed Conversation")}'
                )

                if conversation_data.get('selected_repository'):
                    print(
                        f'  {GRAY}Repository:{RESET} {conversation_data.get("selected_repository")}'
                    )
                    if conversation_data.get('selected_branch'):
                        print(
                            f'  {GRAY}Branch:{RESET} {conversation_data.get("selected_branch")}'
                        )

                # Display access URL
                print(f'\n{BOLD}Access your conversation at:{RESET}')
                print(f'  {BLUE}{conversation_url}{RESET}')

                # Print the short ID for reference
                short_id = conversation_id[:6]
                print(f'\n{GRAY}Conversation ID: {CYAN}{short_id}{RESET}')

    except urllib.error.HTTPError as e:
        print(f'{RED}Error: HTTP {e.code} - {e.reason}{RESET}')
        if e.code == 401:
            print(f'{YELLOW}Authentication failed. Please check your API key.{RESET}')
        elif e.code == 403:
            print(
                f"{YELLOW}You don't have permission to join this conversation.{RESET}"
            )
        elif e.code == 404:
            print(f'{YELLOW}Invalid invite code. Please check and try again.{RESET}')
        else:
            print(f'{GRAY}Server response: {e.read().decode("utf-8")}{RESET}')

    except urllib.error.URLError as e:
        print(f'{RED}Error: Could not connect to the server. {e.reason}{RESET}')

    except json.JSONDecodeError:
        print(f'{RED}Error: Could not parse the server response as JSON.{RESET}')

    except Exception as e:
        print(f'{RED}Unexpected error: {str(e)}{RESET}')


def info_conversation(args: argparse.Namespace) -> None:
    """Show detailed information about a conversation."""
    api_key = get_api_key()
    host = get_host()

    # Define colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    GRAY = '\033[90m'
    RED = '\033[31m'

    if not api_key:
        print(f'{RED}Error: OPENHANDS_API_KEY environment variable is not set.{RESET}')
        print(f'{YELLOW}Please set it and try again.{RESET}')
        sys.exit(1)

    # Get the conversation ID
    conversation_id = args.conversation_id

    # Get the conversation details
    url = f'{host}/api/conversations/{conversation_id}'

    # Create the request with the API key in the header
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
    )

    try:
        print(
            f"{BOLD}Fetching information for conversation '{conversation_id}'...{RESET}"
        )

        # Make the API call to get conversation details
        with urllib.request.urlopen(req) as response:
            conversation_data = json.loads(response.read().decode('utf-8'))

            # Display conversation details
            print(f'\n{BOLD}Conversation Details:{RESET}')
            print(f'  {GRAY}ID:{RESET} {conversation_id}')
            print(
                f'  {GRAY}Name:{RESET} {conversation_data.get("title", "Unnamed Conversation")}'
            )
            print(
                f'  {GRAY}Status:{RESET} {conversation_data.get("status", "Unknown")}'
            )

            # Display creation and update times
            if conversation_data.get('created_at'):
                created_at = datetime.fromisoformat(
                    conversation_data['created_at'].replace('Z', '+00:00')
                )
                print(
                    f'  {GRAY}Created:{RESET} {created_at.strftime("%Y-%m-%d %H:%M:%S")}'
                )

            if conversation_data.get('last_updated_at'):
                updated_at = datetime.fromisoformat(
                    conversation_data['last_updated_at'].replace('Z', '+00:00')
                )
                print(
                    f'  {GRAY}Last Updated:{RESET} {updated_at.strftime("%Y-%m-%d %H:%M:%S")}'
                )

            # Display repository information if available
            if conversation_data.get('selected_repository'):
                print(f'\n{BOLD}Repository Information:{RESET}')
                print(
                    f'  {GRAY}Repository:{RESET} {conversation_data.get("selected_repository")}'
                )
                if conversation_data.get('selected_branch'):
                    print(
                        f'  {GRAY}Branch:{RESET} {conversation_data.get("selected_branch")}'
                    )
                if conversation_data.get('git_provider'):
                    print(
                        f'  {GRAY}Git Provider:{RESET} {conversation_data.get("git_provider")}'
                    )

            # Display access URL
            conversation_url = f'{host}/conversations/{conversation_id}'
            print(f'\n{BOLD}Access URL:{RESET}')
            print(f'  {BLUE}{conversation_url}{RESET}')

    except urllib.error.HTTPError as e:
        print(f'{RED}Error: HTTP {e.code} - {e.reason}{RESET}')
        if e.code == 401:
            print(f'{YELLOW}Authentication failed. Please check your API key.{RESET}')
        elif e.code == 403:
            print(
                f"{YELLOW}You don't have permission to access this conversation.{RESET}"
            )
        elif e.code == 404:
            print(
                f'{YELLOW}Conversation not found. Please check the conversation ID and try again.{RESET}'
            )
        else:
            print(f'{GRAY}Server response: {e.read().decode("utf-8")}{RESET}')

    except urllib.error.URLError as e:
        print(f'{RED}Error: Could not connect to the server. {e.reason}{RESET}')

    except json.JSONDecodeError:
        print(f'{RED}Error: Could not parse the server response as JSON.{RESET}')

    except Exception as e:
        print(f'{RED}Unexpected error: {str(e)}{RESET}')


def main() -> None:
    """Main entry point for the conversation CLI."""
    parser = argparse.ArgumentParser(
        description='OpenHands Conversation Management CLI'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Create conversation command
    create_parser = subparsers.add_parser('create', help='Create a new conversation')
    create_parser.add_argument('message', help='Initial message to send to the agent')
    create_parser.add_argument(
        '--repository',
        help='Repository to associate with the conversation (e.g., owner/repo)',
    )
    create_parser.add_argument(
        '--git-provider',
        choices=['github', 'gitlab'],
        help='Git provider (github or gitlab)',
    )
    create_parser.add_argument('--branch', help='Branch to use for the repository')
    create_parser.set_defaults(func=create_conversation)

    # List conversations command
    list_parser = subparsers.add_parser(
        'list', help='List all conversations you are a member of'
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
    list_parser.set_defaults(func=list_conversations)

    # Join conversation command
    join_parser = subparsers.add_parser('join', help='Join an existing conversation')
    join_parser.add_argument('invite_code', help='Invite code for the conversation')
    join_parser.set_defaults(func=join_conversation)

    # Info conversation command
    info_parser = subparsers.add_parser(
        'info', help='Show detailed information about a conversation'
    )
    info_parser.add_argument(
        'conversation_id', help='ID of the conversation to show information for'
    )
    info_parser.set_defaults(func=info_conversation)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
