"""Main entry point for OpenHands CLI with subcommand support."""

import argparse
import asyncio
import sys

from openhands import __version__
from openhands.cli.subcommands import (
    create_subcommand_parser,
    handle_cli_command,
    handle_serve_command,
)


def run_cli_command(args):
    """Run the CLI command with proper error handling and cleanup."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(handle_cli_command(args))
    except KeyboardInterrupt:
        print('⚠️ Session was interrupted: interrupted\n')
    except ConnectionRefusedError as e:
        print(f'Connection refused: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'An error occurred: {e}')
        sys.exit(1)
    finally:
        try:
            # Cancel all running tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            # Wait for all tasks to complete with a timeout
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        except Exception as e:
            print(f'Error during cleanup: {e}')
            sys.exit(1)


def main():
    """Main entry point with subcommand support and backward compatibility."""
    # Check if we're being called with subcommands or legacy arguments
    if len(sys.argv) > 1 and sys.argv[1] in ['serve', 'cli']:
        # New subcommand interface
        parser = create_subcommand_parser()
        args = parser.parse_args()

        if args.version:
            print(f'OpenHands version: {__version__}')
            sys.exit(0)

        if args.command == 'serve':
            handle_serve_command(args)
        elif args.command == 'cli':
            run_cli_command(args)
        else:
            parser.print_help()
    else:
        # Legacy interface - default to CLI mode for backward compatibility
        # Create a CLI-only parser for backward compatibility
        from openhands.cli.subcommands import _add_cli_arguments

        parser = argparse.ArgumentParser(
            description='OpenHands: Code Less, Make More', prog='openhands'
        )
        parser.add_argument(
            '-v', '--version', action='store_true', help='Show version information'
        )

        # Add a note about available commands
        parser.add_argument(
            '--commands',
            action='store_true',
            help=argparse.SUPPRESS,
        )

        _add_cli_arguments(parser)

        args = parser.parse_args()

        if args.version:
            print(f'OpenHands version: {__version__}')
            sys.exit(0)

        if hasattr(args, 'commands') and args.commands:
            print('OpenHands supports two main commands:')
            print('  serve - Launch the OpenHands GUI server (web interface)')
            print('  cli   - Run OpenHands in CLI mode (terminal interface)')
            print(
                '\nFor more information, run: openhands serve --help or openhands cli --help'
            )
            sys.exit(0)

        # Run CLI mode using the same function as the explicit CLI subcommand
        run_cli_command(args)


if __name__ == '__main__':
    main()
