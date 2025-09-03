"""Main entry point for OpenHands CLI with subcommand support."""

import sys

import openhands
import openhands.cli.suppress_warnings  # noqa: F401
from openhands.cli.gui_launcher import launch_gui_server
from openhands.cli.main import run_cli_command
from openhands.core.config import get_cli_parser
from openhands.core.config.arg_utils import get_subparser
from openhands.utils.laminar import maybe_init_laminar

maybe_init_laminar()


def main():
    """Main entry point with subcommand support and backward compatibility."""
    parser = get_cli_parser()

    # If user only asks for --help or -h without a subcommand
    if len(sys.argv) == 2 and sys.argv[1] in ('--help', '-h'):
        # Print top-level help
        print(parser.format_help())

        # Also print help for `cli` subcommand
        print('\n' + '=' * 80)
        print('CLI command help:\n')

        cli_parser = get_subparser(parser, 'cli')
        print(cli_parser.format_help())

        sys.exit(0)

    # Special case: no subcommand provided, simulate "openhands cli"
    if len(sys.argv) == 1 or (
        len(sys.argv) > 1 and sys.argv[1] not in ['cli', 'serve']
    ):
        # Inject 'cli' as default command
        sys.argv.insert(1, 'cli')

    args = parser.parse_args()

    if hasattr(args, 'version') and args.version:
        print(f'OpenHands CLI version: {openhands.get_version()}')
        sys.exit(0)

    if args.command == 'serve':
        launch_gui_server(mount_cwd=args.mount_cwd, gpu=args.gpu)
    elif args.command == 'cli' or args.command is None:
        run_cli_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
