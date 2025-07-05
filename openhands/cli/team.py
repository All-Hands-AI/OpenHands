import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


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

    # Create a console for rich output
    console = Console()

    if not api_key:
        console.print(
            '[bold red]Error:[/] OPENHANDS_API_KEY environment variable is not set.'
        )
        console.print('[yellow]Please set it and try again.[/]')
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
        console.print(
            f"[bold]Creating conversation with message: '{args.message}'...[/]"
        )

        # Make the API call
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))

            if response_data.get('status') == 'ok' and response_data.get(
                'conversation_id'
            ):
                conversation_id = response_data['conversation_id']
                conversation_url = f'{host}/conversations/{conversation_id}'
                short_id = conversation_id[:6]

                # Create a panel with conversation details
                details_table = Table(show_header=False, box=None, padding=(0, 1))
                details_table.add_column('Field', style='dim')
                details_table.add_column('Value')

                details_table.add_row('Initial Message', args.message)
                if args.repository:
                    details_table.add_row('Repository', args.repository)
                    if args.branch:
                        details_table.add_row('Branch', args.branch)
                details_table.add_row(
                    'Conversation URL',
                    f'[link={conversation_url}]{conversation_url}[/link]',
                )
                details_table.add_row('Conversation ID', f'[cyan]{short_id}[/]')

                # Display success message and details
                console.print()
                console.print('[bold green]Conversation created successfully![/]')
                console.print()
                console.print(
                    Panel(
                        details_table,
                        title='[bold]Conversation Details[/]',
                        expand=False,
                    )
                )
            else:
                console.print(
                    f'[bold red]Error creating conversation:[/] {response_data.get("message", "Unknown error")}'
                )

    except urllib.error.HTTPError as e:
        console.print(f'[bold red]Error: HTTP {e.code} - {e.reason}[/]')
        if e.code == 401:
            console.print(
                '[yellow]Authentication failed. Please check your API key.[/]'
            )
        elif e.code == 403:
            console.print(
                "[yellow]You don't have permission to create conversations.[/]"
            )
        else:
            console.print(f'[dim]Server response: {e.read().decode("utf-8")}[/]')

    except urllib.error.URLError as e:
        console.print(
            f'[bold red]Error: Could not connect to the server.[/] {e.reason}'
        )

    except json.JSONDecodeError:
        console.print(
            '[bold red]Error: Could not parse the server response as JSON.[/]'
        )

    except Exception as e:
        console.print(f'[bold red]Unexpected error:[/] {str(e)}')


def list_conversations(args: argparse.Namespace) -> None:
    """List all conversations the user is a member of."""
    api_key = get_api_key()
    host = get_host()

    # Create a console for rich output
    console = Console()

    if not api_key:
        console.print(
            '[bold red]Error:[/] OPENHANDS_API_KEY environment variable is not set.'
        )
        console.print('[yellow]Please set it and try again.[/]')
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
                console.print('[yellow]No conversations found.[/]')
                return

            # Filter conversations based on status if --all is not specified
            filtered_results = data['results']
            if not args.all:
                filtered_results = [
                    conv for conv in data['results'] if conv['status'] == 'RUNNING'
                ]

                if not filtered_results:
                    console.print('[yellow]No running conversations found.[/]')
                    console.print(
                        '[dim]Use [cyan]--all[/dim] to show all conversations including stopped ones.[/]'
                    )
                    return

            # Create a table for the conversations
            status_text = 'All' if args.all else 'Running'
            table = Table(title=f'Your {status_text} Conversations', expand=True)

            # Add columns to the table
            table.add_column('ID', style='cyan', no_wrap=True)
            table.add_column('Title', style='bold')
            table.add_column('Status', justify='center')
            table.add_column('Repository', style='blue')
            table.add_column('Branch', style='yellow')
            table.add_column('Last Updated', style='dim')
            table.add_column('URL', style='link')

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

                # Create the conversation URL
                conversation_url = f'{host}/conversations/{full_id}'

                # Set status style
                status_style = 'green' if conv['status'] == 'RUNNING' else 'dim'

                # Add a row to the table
                table.add_row(
                    short_id,
                    conv['title'][:30],
                    f'[{status_style}]{conv["status"]}[/]',
                    repo[:40],
                    branch[:15],
                    time_ago,
                    conversation_url,
                )

            # Print the table
            console.print()
            console.print(table)
            console.print()

            # Print pagination info if available
            if data.get('next_page_id'):
                console.print(
                    f'[dim]More results available. Use [cyan]--page-id={data["next_page_id"]}[/cyan] to see the next page.[/]'
                )

    except urllib.error.HTTPError as e:
        console.print(f'[bold red]Error: HTTP {e.code} - {e.reason}[/]')
        if e.code == 401:
            console.print(
                '[yellow]Authentication failed. Please check your API key.[/]'
            )
        elif e.code == 403:
            console.print(
                "[yellow]You don't have permission to access this resource.[/]"
            )
        else:
            console.print(f'[dim]Server response: {e.read().decode("utf-8")}[/]')

    except urllib.error.URLError as e:
        console.print(
            f'[bold red]Error: Could not connect to the server.[/] {e.reason}'
        )

    except json.JSONDecodeError:
        console.print(
            '[bold red]Error: Could not parse the server response as JSON.[/]'
        )

    except Exception as e:
        console.print(f'[bold red]Unexpected error:[/] {str(e)}')


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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
