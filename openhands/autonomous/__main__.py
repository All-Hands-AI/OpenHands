"""
Main entry point for autonomous system

Usage:
    python -m openhands.autonomous [command]

Commands:
    start    - Start the autonomous system
    status   - Check system status
    stop     - Stop the system
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from openhands.autonomous.lifecycle.manager import LifecycleManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('autonomous_system.log'),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


async def start_system(repo_path: str):
    """Start the autonomous system"""
    logger.info("=" * 60)
    logger.info("🧬 OpenHands Autonomous Digital Life System")
    logger.info("=" * 60)

    # Create lifecycle manager
    manager = LifecycleManager(repo_path=repo_path)

    # Initialize
    await manager.initialize()

    # Start
    await manager.start()

    # Run forever
    try:
        while True:
            await asyncio.sleep(60)

            # Periodically log status
            status = await manager.get_status()
            logger.info(
                f"Status: {status['health']['status']} | "
                f"Events: {status['health']['metrics']['events_processed']} | "
                f"Decisions: {status['health']['metrics']['decisions_made']} | "
                f"Tasks: {status['components']['executor']['stats'].get('total_completed', 0)}"
            )

    except KeyboardInterrupt:
        logger.info("\nReceived shutdown signal...")
        await manager.stop()


async def show_status(repo_path: str):
    """Show system status"""
    # For now, just show if system is running
    # In production, would connect to running instance

    logger.info("System status check not yet implemented")
    logger.info("To start the system, use: python -m openhands.autonomous start")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='OpenHands Autonomous Digital Life System'
    )

    parser.add_argument(
        'command',
        choices=['start', 'status', 'stop'],
        help='Command to execute',
    )

    parser.add_argument(
        '--repo-path',
        default='.',
        help='Path to repository (default: current directory)',
    )

    args = parser.parse_args()

    # Resolve repo path
    repo_path = str(Path(args.repo_path).resolve())

    # Execute command
    if args.command == 'start':
        asyncio.run(start_system(repo_path))
    elif args.command == 'status':
        asyncio.run(show_status(repo_path))
    elif args.command == 'stop':
        logger.info("Stop command not yet implemented")
        logger.info("For now, use Ctrl+C to stop a running system")


if __name__ == '__main__':
    main()
