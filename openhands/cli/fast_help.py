"""Fast help module for OpenHands CLI.

This module provides a lightweight implementation of the CLI help and version commands
without loading all the dependencies, which significantly improves the
performance of `openhands --help` and `openhands --version`.

The approach is to create a simplified version of the CLI parser that only includes
the necessary options for displaying help and version information. This avoids loading
the full OpenHands codebase, which can take several seconds.

This implementation addresses GitHub issue #10698, which reported that
`openhands --help` was taking around 20 seconds to run.
"""

import argparse
import sys

from openhands.cli.deprecation_warning import display_deprecation_warning


def get_fast_cli_parser() -> argparse.ArgumentParser:
    """Create a lightweight argument parser for CLI help command."""
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='For more information about a command, run: openhands COMMAND --help',
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

    # Add 'cli' subcommand with common arguments
    cli_parser = subparsers.add_parser(
        'cli', help='Run OpenHands in CLI mode (terminal interface)'
    )

    # Add common arguments
    cli_parser.add_argument(
        '--config-file',
        type=str,
        default='config.toml',
        help='Path to the config file (default: config.toml in the current directory)',
    )
    cli_parser.add_argument(
        '-t',
        '--task',
        type=str,
        default='',
        help='The task for the agent to perform',
    )
    cli_parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='Path to a file containing the task. Overrides -t if both are provided.',
    )
    cli_parser.add_argument(
        '-n',
        '--name',
        help='Session name',
        type=str,
        default='',
    )
    cli_parser.add_argument(
        '--log-level',
        help='Set the log level',
        type=str,
        default=None,
    )
    cli_parser.add_argument(
        '-l',
        '--llm-config',
        default=None,
        type=str,
        help='Replace default LLM ([llm] section in config.toml) config with the specified LLM config, e.g. "llama3" for [llm.llama3] section in config.toml',
    )
    cli_parser.add_argument(
        '--agent-config',
        default=None,
        type=str,
        help='Replace default Agent ([agent] section in config.toml) config with the specified Agent config, e.g. "CodeAct" for [agent.CodeAct] section in config.toml',
    )
    cli_parser.add_argument(
        '-v', '--version', action='store_true', help='Show version information'
    )
    cli_parser.add_argument(
        '--override-cli-mode',
        help='Override the default settings for CLI mode',
        type=bool,
        default=False,
    )
    parser.add_argument(
        '--conversation',
        help='The conversation id to continue',
        type=str,
        default=None,
    )

    return parser


def get_fast_subparser(
    parser: argparse.ArgumentParser, name: str
) -> argparse.ArgumentParser:
    """Get a subparser by name."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            if name in action.choices:
                return action.choices[name]
    raise ValueError(f"Subparser '{name}' not found")


def handle_fast_commands() -> bool:
    """Handle fast path commands like help and version.

    Returns:
        bool: True if a command was handled, False otherwise.
    """
    # Handle --help or -h
    if len(sys.argv) == 2 and sys.argv[1] in ('--help', '-h'):
        display_deprecation_warning()
        parser = get_fast_cli_parser()

        # Print top-level help
        print(parser.format_help())

        # Also print help for `cli` subcommand
        print('\n' + '=' * 80)
        print('CLI command help:\n')

        cli_parser = get_fast_subparser(parser, 'cli')
        print(cli_parser.format_help())

        return True

    # Handle --version or -v
    if len(sys.argv) == 2 and sys.argv[1] in ('--version', '-v'):
        from openhands import get_version

        print(f'OpenHands CLI version: {get_version()}')

        display_deprecation_warning()

        return True

    return False
