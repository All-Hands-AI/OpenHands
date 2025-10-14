"""Main argument parser for OpenHands CLI."""

import argparse


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with CLI as default and serve as subcommand.
    
    Returns:
        The configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='OpenHands CLI - Terminal User Interface for OpenHands AI Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
By default, OpenHands runs in CLI mode (terminal interface).
Use 'serve' subcommand to launch the GUI server instead.

Examples:
  openhands                           # Start CLI mode
  openhands --resume conversation-id  # Resume a conversation in CLI mode
  openhands --task "Fix the bug"      # Start CLI mode with an initial task message
  openhands --file path/to/file.py    # Start CLI mode with file content as initial context
  openhands serve                     # Launch GUI server
  openhands serve --gpu               # Launch GUI server with GPU support
"""
    )
    
    # CLI arguments at top level (default mode)
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Conversation ID to resume'
    )
    parser.add_argument(
        '--task',
        type=str,
        default=None,
        help='Initial user task/message to send when the session starts'
    )
    parser.add_argument(
        '--file',
        type=str,
        default=None,
        help='Path to a file whose contents will be sent as the initial user message (takes precedence over --task)'
    )
    
    # Only serve as subcommand
    subparsers = parser.add_subparsers(
        dest='command',
        help='Additional commands'
    )
    
    # Add serve subcommand
    serve_parser = subparsers.add_parser(
        'serve',
        help='Launch the OpenHands GUI server using Docker (web interface)'
    )
    serve_parser.add_argument(
        '--mount-cwd',
        action='store_true',
        help='Mount the current working directory in the Docker container'
    )
    serve_parser.add_argument(
        '--gpu',
        action='store_true',
        help='Enable GPU support in the Docker container'
    )
    
    return parser