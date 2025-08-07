"""Subcommand handlers for OpenHands CLI."""

import argparse
import asyncio

from openhands.cli.gui_launcher import launch_gui_server
from openhands.cli.main import main_with_loop


def handle_serve_command(args: argparse.Namespace) -> None:
    """Handle the 'serve' subcommand to launch GUI server."""
    launch_gui_server(mount_cwd=args.mount_cwd, gpu=args.gpu)


async def handle_cli_command(args: argparse.Namespace) -> None:
    """Handle the 'cli' subcommand to run CLI mode."""
    loop = asyncio.get_event_loop()
    await main_with_loop(loop, args)


def create_subcommand_parser() -> argparse.ArgumentParser:
    """Create the main parser with subcommands."""
    # Create a description with welcome message explaining available commands
    description = (
        'Welcome to OpenHands: Code Less, Make More\n\n'
        'OpenHands supports two main commands:\n'
        '  serve - Launch the OpenHands GUI server (web interface)\n'
        '  cli   - Run OpenHands in CLI mode (terminal interface)\n\n'
        'Running "openhands" without a command is the same as "openhands cli"'
    )

    parser = argparse.ArgumentParser(
        description=description,
        prog='openhands',
        formatter_class=argparse.RawDescriptionHelpFormatter,  # Preserve formatting in description
        epilog='For more information about a command, run: openhands COMMAND --help',
    )

    # Add version argument at top level
    parser.add_argument(
        '-v', '--version', action='store_true', help='Show version information'
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description='OpenHands supports two main commands:',
        metavar='COMMAND',
    )

    # Add 'serve' subcommand
    serve_parser = subparsers.add_parser(
        'serve', help='Launch the OpenHands GUI server using Docker (web interface)'
    )
    serve_parser.add_argument(
        '--mount-cwd',
        help='Mount the current working directory into the GUI server container',
        action='store_true',
        default=False,
    )
    serve_parser.add_argument(
        '--gpu',
        help='Enable GPU support by mounting all GPUs into the Docker container via nvidia-docker',
        action='store_true',
        default=False,
    )

    # Add 'cli' subcommand - import all the existing CLI arguments
    cli_parser = subparsers.add_parser(
        'cli', help='Run OpenHands in CLI mode (terminal interface)'
    )

    # Add all the existing CLI arguments to the cli subcommand
    _add_cli_arguments(cli_parser)

    return parser


def _add_cli_arguments(parser: argparse.ArgumentParser) -> None:
    """Add CLI arguments to the parser using centralized configuration."""
    from openhands.cli.args_config import add_common_arguments, add_cli_specific_arguments
    
    add_common_arguments(parser)
    add_cli_specific_arguments(parser)
