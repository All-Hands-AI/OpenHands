"""Main entry point for Snowcode CLI with subcommand support and authentication."""

import asyncio
import sys

import openhands
import openhands.cli.suppress_warnings  # noqa: F401
from openhands.cli.gui_launcher import launch_gui_server
from openhands.cli.main import run_cli_command
from openhands.cli.snowcode_auth import (
    handle_snow_login,
    handle_snow_logout,
    handle_snow_status,
    snowcode_auth,
)
from openhands.core.config import get_cli_parser


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
                    asyncio.run(handle_snow_login(token))
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
        if not snowcode_auth.is_authenticated():
            print('❌ Not authenticated with Snowcode')
            print('💡 Use "snow --token YOUR_TOKEN" to login first')
            print('📖 Use "snow --help" for more options')
            sys.exit(1)

        # Ensure default configuration exists automatically
        try:
            asyncio.run(snowcode_auth.ensure_default_config_exists())
        except Exception:
            pass  # Silently continue if config setup fails

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
        if not snowcode_auth.is_authenticated():
            print('❌ Not authenticated with Snowcode')
            print('💡 Use "snow --token YOUR_TOKEN" to login first')
            sys.exit(1)

        # Ensure default configuration exists automatically
        try:
            asyncio.run(snowcode_auth.ensure_default_config_exists())
        except Exception:
            pass  # Silently continue if config setup fails

        print('🚀 Welcome to Snowcode! Starting chat session...')
        run_cli_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
