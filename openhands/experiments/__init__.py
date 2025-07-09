"""
Experiment management for OpenHands.

This module provides functionality for running experiments and A/B tests
in OpenHands, allowing for customization of various components including
system prompts, agent configurations, and more.
"""

from openhands.experiments.experiment_manager import (
    ExperimentManager,
    ExperimentManagerImpl,
)

__all__ = ['ExperimentManager', 'ExperimentManagerImpl']
