"""Centralized command line argument configuration for OpenHands CLI and headless modes."""

import argparse

from openhands.core.config.config_utils import OH_DEFAULT_AGENT, OH_MAX_ITERATIONS


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common arguments shared between CLI and headless modes."""
    parser.add_argument(
        '--config-file',
        type=str,
        default='config.toml',
        help='Path to the config file (default: config.toml in the current directory)',
    )
    parser.add_argument(
        '-d',
        '--directory',
        type=str,
        help='The working directory for the agent',
    )
    parser.add_argument(
        '-t',
        '--task',
        type=str,
        default='',
        help='The task for the agent to perform',
    )
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='Path to a file containing the task. Overrides -t if both are provided.',
    )
    parser.add_argument(
        '-c',
        '--agent-cls',
        default=OH_DEFAULT_AGENT,
        type=str,
        help='Name of the default agent to use',
    )
    parser.add_argument(
        '-i',
        '--max-iterations',
        default=OH_MAX_ITERATIONS,
        type=int,
        help='The maximum number of iterations to run the agent',
    )
    parser.add_argument(
        '-b',
        '--max-budget-per-task',
        type=float,
        help='The maximum budget allowed per task, beyond which the agent will stop.',
    )
    parser.add_argument(
        '-l',
        '--llm-config',
        default=None,
        type=str,
        help='Replace default LLM ([llm] section in config.toml) config with the specified LLM config, e.g. "llama3" for [llm.llama3] section in config.toml',
    )
    parser.add_argument(
        '--agent-config',
        default=None,
        type=str,
        help='Replace default Agent ([agent] section in config.toml) config with the specified Agent config, e.g. "CodeAct" for [agent.CodeAct] section in config.toml',
    )
    parser.add_argument(
        '-n',
        '--name',
        help='Session name',
        type=str,
        default='',
    )
    parser.add_argument(
        '--log-level',
        help='Set the log level',
        type=str,
        default=None,
    )


def add_cli_specific_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments specific to CLI mode (simplified subset)."""
    parser.add_argument(
        '--no-auto-continue',
        help='Disable auto-continue responses in CLI mode (i.e. CLI will read from stdin instead of auto-continuing)',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--selected-repo',
        help='GitHub repository to clone (format: owner/repo)',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--override-cli-mode',
        help='Override the default settings for CLI mode',
        type=bool,
        default=False,
    )


def add_headless_specific_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments specific to headless mode (full evaluation suite)."""
    # Version argument
    parser.add_argument(
        '-v', '--version', action='store_true', help='Show version information'
    )

    # Evaluation-specific arguments
    parser.add_argument(
        '--eval-output-dir',
        default='evaluation/evaluation_outputs/outputs',
        type=str,
        help='The directory to save evaluation output',
    )
    parser.add_argument(
        '--eval-n-limit',
        default=None,
        type=int,
        help='The number of instances to evaluate',
    )
    parser.add_argument(
        '--eval-num-workers',
        default=4,
        type=int,
        help='The number of workers to use for evaluation',
    )
    parser.add_argument(
        '--eval-note',
        default=None,
        type=str,
        help='The note to add to the evaluation directory',
    )
    parser.add_argument(
        '--eval-ids',
        default=None,
        type=str,
        help='The comma-separated list (in quotes) of IDs of the instances to evaluate',
    )

    # Additional headless-specific arguments
    parser.add_argument(
        '--no-auto-continue',
        help='Disable auto-continue responses in headless mode (i.e. headless will read from stdin instead of auto-continuing)',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--selected-repo',
        help='GitHub repository to clone (format: owner/repo)',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--override-cli-mode',
        help='Override the default settings for CLI mode',
        type=bool,
        default=False,
    )


def create_cli_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI mode with simplified argument set."""
    parser = argparse.ArgumentParser(description='Run OpenHands in CLI mode')
    add_common_arguments(parser)
    add_cli_specific_arguments(parser)
    return parser


def create_headless_parser() -> argparse.ArgumentParser:
    """Create argument parser for headless mode with full argument set."""
    parser = argparse.ArgumentParser(description='Run the agent via CLI')
    add_common_arguments(parser)
    add_headless_specific_arguments(parser)
    return parser
