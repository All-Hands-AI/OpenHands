"""Main argument parser for OpenHands CLI."""

import argparse

from openhands_cli.argparsers.cli_parser import add_cli_parser
from openhands_cli.argparsers.serve_parser import add_serve_parser


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands.
    
    Returns:
        The configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='OpenHands CLI - Terminal User Interface for OpenHands AI Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
subcommands:

  Available commands:
    cli    - Run OpenHands in CLI mode (terminal interface) [default]
    serve  - Launch the OpenHands GUI server (web interface)

"""
    )
    
    # Add top-level --resume argument for convenience (defaults to cli subcommand)
    parser.add_argument(
        '--resume',
        type=str,
        help='Conversation ID to resume (implies cli subcommand)'
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='{cli,serve}'
    )
    
    # Add individual parsers
    add_cli_parser(subparsers)
    add_serve_parser(subparsers)
    
    return parser