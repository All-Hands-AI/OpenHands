#!/usr/bin/env python3
"""
Simple main entry point for OpenHands CLI.
This is a simplified version that demonstrates the TUI functionality.
"""

import argparse
import logging
import os
import warnings

debug_env = os.getenv('DEBUG', 'false').lower()
if debug_env != '1' and debug_env != 'true':
    logging.disable(logging.WARNING)
    warnings.filterwarnings('ignore')

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML


def main() -> None:
    """Main entry point for the OpenHands CLI.

    Raises:
        ImportError: If agent chat dependencies are missing
        Exception: On other error conditions
    """
    parser = argparse.ArgumentParser(
        description='OpenHands CLI - Terminal User Interface for OpenHands AI Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        description='''
Available commands:
  cli    - Run OpenHands in CLI mode (terminal interface) [default]
  serve  - Launch the OpenHands GUI server (web interface)
        ''',
    )
    
    # Add 'cli' subcommand (default behavior)
    cli_parser = subparsers.add_parser(
        'cli', help='Run OpenHands in CLI mode (terminal interface)'
    )
    cli_parser.add_argument(
        '--resume',
        type=str,
        help='Conversation ID to use for the session. If not provided, a random UUID will be generated.',
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

    args = parser.parse_args()
    
    # If no subcommand is provided, default to 'cli'
    if args.command is None:
        args.command = 'cli'
        # Add resume attribute for backward compatibility
        args.resume = getattr(args, 'resume', None)

    try:
        if args.command == 'serve':
            # Import gui_launcher only when needed
            from openhands_cli.gui_launcher import launch_gui_server
            
            launch_gui_server(mount_cwd=args.mount_cwd, gpu=args.gpu)
        elif args.command == 'cli':
            # Import agent_chat only when needed
            from openhands_cli.agent_chat import run_cli_entry
            
            # Start agent chat
            run_cli_entry(resume_conversation_id=args.resume)
        else:
            parser.print_help()
            sys.exit(1)

    except ImportError as e:
        print_formatted_text(
            HTML(f'<red>Error: Required dependencies are missing: {e}</red>')
        )
        print_formatted_text(
            HTML('<yellow>Please ensure all dependencies are properly installed.</yellow>')
        )
        raise
    except KeyboardInterrupt:
        print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
    except EOFError:
        print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
    except Exception as e:
        print_formatted_text(HTML(f'<red>Error: {e}</red>'))
        import traceback

        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
