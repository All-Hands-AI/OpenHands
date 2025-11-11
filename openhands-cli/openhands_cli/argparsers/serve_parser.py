"""Argument parser for serve subcommand."""

import argparse


def add_serve_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add serve subcommand parser.
    
    Args:
        subparsers: The subparsers object to add the serve parser to
        
    Returns:
        The serve argument parser
    """
    serve_parser = subparsers.add_parser(
        'serve',
        help='Launch the OpenHands GUI server using Docker (web interface)'
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
    return serve_parser