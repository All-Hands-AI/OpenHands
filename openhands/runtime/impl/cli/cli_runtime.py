# openhands/runtime/impl/cli/cli_runtime.py

import sys
import os
import logging
from typing import List, Optional

from openhands.runtime.impl.cli.utils import parse_args, load_config
from openhands.runtime.impl.cli.executor import CLIExecutor
from openhands.runtime.utils.windows_exceptions import handle_windows_exception

logger = logging.getLogger(__name__)

class CLIRuntime:
    def __init__(self, args: Optional[List[str]] = None):
        self.args = args if args is not None else sys.argv[1:]
        self.config = None
        self.executor = None

    def initialize(self):
        try:
            logger.info("Loading configuration...")
            self.config = load_config()
            logger.info("Configuration loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

        self.executor = CLIExecutor(self.config)

    def run(self):
        try:
            parsed_args = parse_args(self.args)
            logger.info(f"Running command: {parsed_args.command}")
            result = self.executor.execute(parsed_args)
            logger.info(f"Command executed successfully: {result}")
        except handle_windows_exception() as e:
            logger.error(f"Windows exception caught: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unhandled exception: {e}")
            sys.exit(1)

def main():
    runtime = CLIRuntime()
    runtime.initialize()
    runtime.run()

if __name__ == "__main__":
    main()
