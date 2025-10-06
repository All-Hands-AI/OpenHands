"""Argument parser for CLI subcommand."""

import argparse


def add_cli_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add CLI subcommand parser.
    
    Args:
        subparsers: The subparsers object to add the CLI parser to
        
    Returns:
        The CLI argument parser
    """
    cli_parser = subparsers.add_parser(
        'cli',
        help='Run OpenHands in CLI mode (terminal interface)'
    )
    cli_parser.add_argument(
        '--resume',
        type=str,
        help='Conversation ID to use for the session. If not provided, a random UUID will be generated.'
    )
    return cli_parser