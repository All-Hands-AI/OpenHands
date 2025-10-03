"""CLI entry point for OpenHands ACP server."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from openhands.agent_server.acp.server import run_acp_server


def main() -> None:
    """Main entry point for ACP server."""
    parser = argparse.ArgumentParser(
        description="OpenHands Agent Client Protocol Server"
    )
    parser.add_argument(
        "--persistence-dir",
        type=Path,
        default=Path("/tmp/openhands_acp"),
        help="Directory to store conversation data (default: /tmp/openhands_acp)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Set up logging to stderr (stdout is used for ACP communication)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )

    # Run the ACP server
    try:
        asyncio.run(run_acp_server(args.persistence_dir))
    except KeyboardInterrupt:
        logging.info("ACP server stopped by user")
    except Exception as e:
        logging.error(f"ACP server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
