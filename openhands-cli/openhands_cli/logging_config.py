#!/usr/bin/env python3
"""
Logging configuration for OpenHands CLI.
Suppresses verbose logs during agent initialization unless DEBUG is enabled.
"""

import logging
import os
import sys
from typing import Optional

DEBUG = os.environ.get('DEBUG', '0').lower() in ('1', 'true', 'yes', 'on')

def setup_logging(debug: Optional[bool] = None) -> None:
    """
    Setup logging configuration for OpenHands CLI.

    Args:
        debug: If True, enable debug logging. If None, use global DEBUG flag.
    """
    if debug is None:
        debug = DEBUG

    if debug:
        # Enable verbose logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stderr
        )
        print(f"Debug logging enabled", file=sys.stderr)
    else:
        # Suppress most logs, only show warnings and errors
        logging.basicConfig(
            level=logging.WARNING,
            format='%(levelname)s: %(message)s',
            stream=sys.stderr
        )

        # Specifically suppress common noisy loggers
        noisy_loggers = [
            'openhands',
            'openhands.sdk',
            'httpx',
            'httpcore',
            'urllib3',
            'requests',
            'openai',
            'anthropic',
            'litellm',
        ]

        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.ERROR)

def suppress_initialization_logs():
    """Context manager to temporarily suppress logs during initialization."""

    class LogSuppressor:
        def __init__(self):
            self.original_levels = {}
            self.loggers_to_suppress = [
                'openhands',
                'openhands.sdk',
                'httpx',
                'httpcore',
                'urllib3',
                'requests',
                'openai',
                'anthropic',
                'litellm',
                'root',
            ]

        def __enter__(self):
            if not DEBUG:
                for logger_name in self.loggers_to_suppress:
                    logger = logging.getLogger(logger_name)
                    self.original_levels[logger_name] = logger.level
                    logger.setLevel(logging.CRITICAL)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if not DEBUG:
                for logger_name, original_level in self.original_levels.items():
                    logging.getLogger(logger_name).setLevel(original_level)

    return LogSuppressor()

# Initialize logging when module is imported
setup_logging()
