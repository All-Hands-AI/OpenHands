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
    # Set the args in a way that main_with_loop can access them
    # We need to monkey-patch the parse_arguments function temporarily
    import openhands.core.config.utils as config_utils

    original_parse_arguments = config_utils.parse_arguments

    def mock_parse_arguments():
        return args

    config_utils.parse_arguments = mock_parse_arguments

    try:
        loop = asyncio.get_event_loop()
        await main_with_loop(loop)
    finally:
        # Restore original function
        config_utils.parse_arguments = original_parse_arguments


def create_subcommand_parser() -> argparse.ArgumentParser:
    """Create the main parser with subcommands."""
    parser = argparse.ArgumentParser(
        description='OpenHands: Code Less, Make More',
        prog='openhands',
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
    """Add all CLI arguments to the parser."""
    parser.add_argument(
        '--config-file',
        type=str,
        default='config.toml',
        help='Path to the config file (default: config.toml in the current directory)',
    )
    parser.add_argument(
        '-d',
        '--directory',
        type=str,
        help='The working directory for the agent',
    )
    parser.add_argument(
        '-t',
        '--task',
        type=str,
        default='',
        help='The task for the agent to perform',
    )
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='Path to a file containing the task. Overrides -t if both are provided.',
    )
    parser.add_argument(
        '-c',
        '--agent-cls',
        default='CodeActAgent',
        type=str,
        help='Name of the default agent to use',
    )
    parser.add_argument(
        '-i',
        '--max-iterations',
        default=100,
        type=int,
        help='The maximum number of iterations to run the agent',
    )
    parser.add_argument(
        '-b',
        '--max-budget-per-task',
        type=float,
        help='The maximum budget allowed per task, beyond which the agent will stop.',
    )
    parser.add_argument(
        '-l',
        '--llm-config',
        default=None,
        type=str,
        help='Replace default LLM ([llm] section in config.toml) config with the specified LLM config, e.g. "llama3" for [llm.llama3] section in config.toml',
    )
    parser.add_argument(
        '--agent-config',
        default=None,
        type=str,
        help='Replace default Agent ([agent] section in config.toml) config with the specified Agent config, e.g. "CodeAct" for [agent.CodeAct] section in config.toml',
    )
    parser.add_argument(
        '-n',
        '--name',
        help='Session name',
        type=str,
        default='',
    )
    parser.add_argument(
        '--no-auto-continue',
        help='Disable auto-continue responses in headless mode (i.e. headless will read from stdin instead of auto-continuing)',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--selected-repo',
        help='GitHub repository to clone (format: owner/repo)',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--override-cli-mode',
        help='Override the default settings for CLI mode',
        type=bool,
        default=False,
    )
    parser.add_argument(
        '--log-level',
        help='Set the log level',
        type=str,
        default=None,
    )
