"""Main entry point for OpenHands CLI with subcommand support."""

import os
import sys

import openhands
import openhands.cli.suppress_warnings  # noqa: F401
from openhands.cli.gui_launcher import launch_gui_server
from openhands.cli.main import run_cli_command
from openhands.core.config import get_cli_parser
from openhands.core.config.arg_utils import get_subparser


def _maybe_preflight_mcp() -> None:
    """Fail fast if MCP stdio binaries are missing."""
    if sys.platform == 'win32':
        return

    mcp_config_path = os.environ.get('OPENHANDS_MCP_CONFIG') or os.environ.get(
        'MCP_CONFIG'
    )
    if not mcp_config_path or not os.path.isfile(mcp_config_path):
        return

    try:
        from openhands.cli.mcp_preflight import check_mcp_commands_exist
    except ImportError:
        return

    check_mcp_commands_exist(mcp_config_path)


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
        len(sys.argv) > 1 and sys.argv[1] not in ('cli', 'serve')
    ):
        sys.argv.insert(1, 'cli')

    args = parser.parse_args()

    if getattr(args, 'version', False):
        print(f'OpenHands CLI version: {openhands.get_version()}')
        sys.exit(0)

    if args.command == 'serve':
        launch_gui_server(mount_cwd=args.mount_cwd, gpu=args.gpu)
    else:
        # args.command == 'cli' or None
        _maybe_preflight_mcp()
        run_cli_command(args)


if __name__ == '__main__':
    main()
