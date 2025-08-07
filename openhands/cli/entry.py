"""Main entry point for OpenHands CLI with subcommand support."""

import sys

from openhands.cli.gui_launcher import launch_gui_server
from openhands.cli.main import run_cli_command
from openhands.core.config import get_cli_parser


def main():
    """Main entry point with subcommand support and backward compatibility."""
    parser = get_cli_parser()
    args = parser.parse_args()
    if args.command == 'serve':
        launch_gui_server(mount_cwd=args.mount_cwd, gpu=args.gpu)
    elif args.command == 'cli' or args.command is None:
        run_cli_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
