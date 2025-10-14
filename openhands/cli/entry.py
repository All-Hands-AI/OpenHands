"""Main entry point for OpenHands CLI with subcommand support."""

import sys

# Import only essential modules for CLI help
# Other imports are deferred until they're actually needed
import openhands
import openhands.cli.suppress_warnings  # noqa: F401
from openhands.cli.fast_help import handle_fast_commands


def main():
    """Main entry point with subcommand support and backward compatibility."""
    # Fast path for help and version commands
    if handle_fast_commands():
        sys.exit(0)

    # Import parser only when needed - only if we're not just showing help
    from openhands.core.config import get_cli_parser

    parser = get_cli_parser()

    # Special case: no subcommand provided, simulate "openhands cli"
    if len(sys.argv) == 1 or (
        len(sys.argv) > 1 and sys.argv[1] not in ['cli', 'serve']
    ):
        # Inject 'cli' as default command
        sys.argv.insert(1, 'cli')

    args = parser.parse_args()

    if hasattr(args, 'version') and args.version:
        from openhands import get_version

        print(f'OpenHands CLI version: {get_version()}')
        sys.exit(0)

    if args.command == 'serve':
        # Import gui_launcher only when needed
        from openhands.cli.gui_launcher import launch_gui_server

        launch_gui_server(mount_cwd=args.mount_cwd, gpu=args.gpu)
    elif args.command == 'cli' or args.command is None:
        # Import main only when needed
        from openhands.cli.main import run_cli_command

        run_cli_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
