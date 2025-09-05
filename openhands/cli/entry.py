"""Main entry point for Snowcode CLI with subcommand support and authentication."""

import hashlib
import json
import sys
import time
from pathlib import Path

import requests

import openhands
import openhands.cli.suppress_warnings  # noqa: F401
from openhands.cli.gui_launcher import launch_gui_server
from openhands.cli.main import run_cli_command
from openhands.core.config import get_cli_parser

# SNOW Authentication Configuration
_SNOW_API_ENDPOINT = 'https://api-kratos.dev.snowcell.io/auth/validate'
_SNOW_AUTH_FILE_PATH = Path.home() / '.snowcode' / 'auth.json'


# SNOW Authentication functions
def validate_snow_token_with_api(token: str) -> bool:
    """Validate SNOW token with the API endpoint."""
    try:
        headers = {'x-api-token': token, 'Content-Type': 'application/json'}

        response = requests.get(
            _SNOW_API_ENDPOINT, headers=headers, timeout=10  # 10 second timeout
        )

        if response.status_code == 200:
            try:
                data = response.json()
                return data.get('status') == 'success'
            except ValueError:
                return False

        return False
    except requests.RequestException:
        return False
    except Exception:
        return False


def store_snow_token(token: str) -> bool:
    """Store SNOW authentication token after validating with API."""
    try:
        # First validate the token with the API
        if not validate_snow_token_with_api(token):
            return False

        # Ensure the directory exists
        _SNOW_AUTH_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Create auth data with timestamp and actual token
        auth_data = {
            'token': token,  # Store actual token for future API calls
            'token_hash': hashlib.sha256(token.encode()).hexdigest(),
            'timestamp': time.time(),
            'status': 'active',
        }

        with open(_SNOW_AUTH_FILE_PATH, 'w') as f:
            json.dump(auth_data, f)

        return True
    except Exception:
        return False


def load_snow_token() -> dict | None:
    """Load stored SNOW authentication token."""
    try:
        if not _SNOW_AUTH_FILE_PATH.exists():
            return None

        with open(_SNOW_AUTH_FILE_PATH, 'r') as f:
            auth_data = json.load(f)

        # Validate required fields
        if not all(key in auth_data for key in ['token', 'timestamp', 'status']):
            return None

        # Check if token is still active
        if auth_data.get('status') != 'active':
            return None

        return auth_data
    except Exception:
        return None


def is_snow_authenticated() -> bool:
    """Check if user is authenticated with SNOW."""
    auth_data = load_snow_token()
    if not auth_data:
        return False

    # Optionally re-validate with API
    return validate_snow_token_with_api(auth_data['token'])


def logout_snow() -> bool:
    """Logout from SNOW by removing stored token."""
    try:
        if _SNOW_AUTH_FILE_PATH.exists():
            _SNOW_AUTH_FILE_PATH.unlink()
        return True
    except Exception:
        return False


def handle_snow_login(token: str) -> None:
    """Handle SNOW login with token."""
    print('🔑 Authenticating with Snowcode...')

    if store_snow_token(token):
        print('✅ Authentication successful!')
        print('🚀 You can now use "snow --chat" to start a chat session.')
    else:
        print('❌ Authentication failed. Please check your token and try again.')
        sys.exit(1)


def handle_snow_status() -> None:
    """Handle SNOW authentication status check."""
    if is_snow_authenticated():
        auth_data = load_snow_token()
        timestamp = auth_data.get('timestamp', 0) if auth_data else 0
        login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        print('✅ Authenticated with Snowcode')
        print(f'🕒 Logged in at: {login_time}')
    else:
        print('❌ Not authenticated with Snowcode')
        print('💡 Use "snow --token YOUR_TOKEN" to login')


# def handle_snow_chat() -> None:
#     """Handle SNOW chat session start."""
#     if not is_snow_authenticated():
#         print('❌ Not authenticated with Snowcode')
#         print('💡 Use "snow --token YOUR_TOKEN" to login first')
#         sys.exit(1)

#     print('🚀 Starting Snowcode chat session...')
#     # Inject 'cli' command to start the chat
#     sys.argv = ['snow', 'cli'] + [arg for arg in sys.argv[2:] if arg != '--chat']


def handle_snow_logout() -> None:
    """Handle SNOW logout."""
    if logout_snow():
        print('✅ Successfully logged out from Snowcode')
    else:
        print('❌ Logout failed or already logged out')


def get_snow_cli_parser():
    """Create a custom parser for SNOW CLI commands."""
    # Get the original parser but modify the description
    parser = get_cli_parser()

    # Update program name and description for Snowcode
    parser.prog = 'snow'
    parser.description = (
        'Snowcode - Your AI-powered coding assistant\n\n'
        'Snowcode supports authentication and chat commands:\n'
        '  --token TOKEN  - Login with authentication token\n'
        '  --status       - Check authentication status\n'
        # '  --chat         - Start chat session (requires authentication)\n'
        '  --logout       - Logout from Snowcode\n\n'
        'Original OpenHands commands are also supported:\n'
        '  serve - Launch the Snowcode GUI server (web interface)\n'
        '  cli   - Run Snowcode in CLI mode (terminal interface)\n\n'
        'Running "snow" without a command is the same as "snow cli" (if authenticated)'
    )

    # Add SNOW-specific arguments
    parser.add_argument(
        '--token',
        type=str,
        help='Snowcode authentication token for login',
        metavar='TOKEN',
    )
    parser.add_argument(
        '--status', action='store_true', help='Check Snowcode authentication status'
    )
    # parser.add_argument(
    #     '--chat',
    #     action='store_true',
    #     help='Start Snowcode chat session (requires authentication)',
    # )
    # parser.add_argument('--logout', action='store_true', help='Logout from Snowcode')

    return parser


def main():
    """Main entry point with SNOW authentication and subcommand support."""
    parser = get_snow_cli_parser()

    # Handle SNOW-specific commands first (before parsing)
    if len(sys.argv) >= 2:
        # Handle SNOW authentication commands
        if '--token' in sys.argv:
            # Find the token value
            try:
                token_index = sys.argv.index('--token')
                if token_index + 1 < len(sys.argv):
                    token = sys.argv[token_index + 1]
                    handle_snow_login(token)
                    return
                else:
                    print('❌ Error: --token requires a value')
                    sys.exit(1)
            except ValueError:
                print('❌ Error: Invalid token format')
                sys.exit(1)

        elif '--status' in sys.argv:
            handle_snow_status()
            return

        # elif '--chat' in sys.argv:
        #     handle_snow_chat()
        #     # Continue to CLI execution after authentication check

        elif '--logout' in sys.argv:
            handle_snow_logout()
            return

    # If user only asks for --help or -h without a subcommand
    if len(sys.argv) == 2 and sys.argv[1] in ('--help', '-h'):
        # Print top-level help
        print(parser.format_help())

        # Also print help for `cli` subcommand if available
        try:
            from openhands.core.config.arg_utils import get_subparser

            print('\n' + '=' * 80)
            print('CLI command help:\n')
            cli_parser = get_subparser(parser, 'cli')
            print(cli_parser.format_help())
        except Exception:
            # Gracefully handle if subparser is not available
            pass

        sys.exit(0)

    # Special case: no subcommand provided, simulate "snow cli" (with auth check)
    if len(sys.argv) == 1 or (
        len(sys.argv) > 1
        and sys.argv[1] not in ['cli', 'serve']
        and not sys.argv[1].startswith('--')
    ):
        # Check authentication for default chat mode
        if not is_snow_authenticated():
            print('❌ Not authenticated with Snowcode')
            print('💡 Use "snow --token YOUR_TOKEN" to login first')
            print('📖 Use "snow --help" for more options')
            sys.exit(1)

        # Inject 'cli' as default command
        sys.argv.insert(1, 'cli')

    args = parser.parse_args()

    if hasattr(args, 'version') and args.version:
        print(f'Snowcode CLI version: {openhands.get_version()}')
        sys.exit(0)

    # Handle standard OpenHands commands (preserved functionality)
    if args.command == 'serve':
        launch_gui_server(mount_cwd=args.mount_cwd, gpu=args.gpu)
    elif args.command == 'cli' or args.command is None:
        # For CLI mode, ensure authentication
        if not is_snow_authenticated():
            print('❌ Not authenticated with Snowcode')
            print('💡 Use "snow --token YOUR_TOKEN" to login first')
            sys.exit(1)

        print('🚀 Welcome to Snowcode! Starting chat session...')
        run_cli_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
