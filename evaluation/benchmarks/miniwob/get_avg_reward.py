import json
import os
import pandas as pd
from openhands.core.logger import openhands_logger as logger

# TODO: Update to work with Browser-Use evaluation environments
# import browsergym.miniwob  # noqa F401 register miniwob tasks as gym environments

def get_avg_reward(output_file: str) -> float:
    """Get average reward from output file."""
    if not os.path.exists(output_file):
        logger.warning(f'Output file {output_file} does not exist')
        return 0.0

    # TODO: Update environment ID filtering for Browser-Use
    # For now, return 0.0 as we need to implement Browser-Use evaluation
    return 0.0
