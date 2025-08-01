"""Utility for configuring and managing timeout settings."""

import json
import os
from pathlib import Path
from typing import Any, Optional

from openhands.core.config.timeout_config import TimeoutConfig, TimeoutType
from openhands.core.logger import openhands_logger as logger


class TimeoutConfigurator:
    """Utility class for managing timeout configurations."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the timeout configurator.

        Args:
            config_path: Path to the timeout configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        home_dir = Path.home()
        config_dir = home_dir / '.openhands'
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / 'timeout_config.json')

    def _load_config(self) -> TimeoutConfig:
        """Load timeout configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)

                # Convert string keys back to TimeoutType enums
                if 'default_timeouts' in data:
                    default_timeouts = {}
                    for key, value in data['default_timeouts'].items():
                        try:
                            timeout_type = TimeoutType(key)
                            default_timeouts[timeout_type] = value
                        except ValueError:
                            logger.warning(f'Unknown timeout type in config: {key}')
                    data['default_timeouts'] = default_timeouts

                if 'max_timeouts' in data:
                    max_timeouts = {}
                    for key, value in data['max_timeouts'].items():
                        try:
                            timeout_type = TimeoutType(key)
                            max_timeouts[timeout_type] = value
                        except ValueError:
                            logger.warning(f'Unknown timeout type in config: {key}')
                    data['max_timeouts'] = max_timeouts

                return TimeoutConfig(**data)
            except Exception as e:
                logger.warning(
                    f'Failed to load timeout config from {self.config_path}: {e}'
                )
                return TimeoutConfig()
        else:
            return TimeoutConfig()

    def save_config(self) -> None:
        """Save the current configuration to file."""
        try:
            # Convert TimeoutType enums to strings for JSON serialization
            data = self.config.model_dump()

            if 'default_timeouts' in data:
                default_timeouts = {}
                for key, value in data['default_timeouts'].items():
                    if isinstance(key, TimeoutType):
                        default_timeouts[key.value] = value
                    else:
                        default_timeouts[str(key)] = value
                data['default_timeouts'] = default_timeouts

            if 'max_timeouts' in data:
                max_timeouts = {}
                for key, value in data['max_timeouts'].items():
                    if isinstance(key, TimeoutType):
                        max_timeouts[key.value] = value
                    else:
                        max_timeouts[str(key)] = value
                data['max_timeouts'] = max_timeouts

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f'Timeout configuration saved to {self.config_path}')
        except Exception as e:
            logger.error(f'Failed to save timeout config to {self.config_path}: {e}')

    def set_timeout(self, timeout_type: TimeoutType, value: float) -> None:
        """Set a specific timeout value.

        Args:
            timeout_type: The type of timeout to set
            value: The timeout value in seconds
        """
        self.config.default_timeouts[timeout_type] = value
        logger.info(f'Set {timeout_type.value} timeout to {value}s')

    def set_max_timeout(self, timeout_type: TimeoutType, value: float) -> None:
        """Set a maximum timeout value.

        Args:
            timeout_type: The type of timeout to set
            value: The maximum timeout value in seconds
        """
        self.config.max_timeouts[timeout_type] = value
        logger.info(f'Set {timeout_type.value} max timeout to {value}s')

    def get_timeout(self, timeout_type: TimeoutType) -> float:
        """Get the current timeout value for a type.

        Args:
            timeout_type: The type of timeout to get

        Returns:
            The timeout value in seconds
        """
        return self.config.default_timeouts.get(timeout_type, 120.0)

    def get_max_timeout(self, timeout_type: TimeoutType) -> float:
        """Get the maximum timeout value for a type.

        Args:
            timeout_type: The type of timeout to get

        Returns:
            The maximum timeout value in seconds
        """
        return self.config.max_timeouts.get(timeout_type, 1800.0)

    def enable_progressive_timeout(self, enabled: bool = True) -> None:
        """Enable or disable progressive timeout.

        Args:
            enabled: Whether to enable progressive timeout
        """
        self.config.enable_progressive_timeout = enabled
        logger.info(f'Progressive timeout {"enabled" if enabled else "disabled"}')

    def enable_adaptive_timeout(self, enabled: bool = True) -> None:
        """Enable or disable adaptive timeout.

        Args:
            enabled: Whether to enable adaptive timeout
        """
        self.config.enable_adaptive_timeout = enabled
        logger.info(f'Adaptive timeout {"enabled" if enabled else "disabled"}')

    def set_no_change_timeout(self, value: float) -> None:
        """Set the no-change timeout value.

        Args:
            value: The no-change timeout in seconds
        """
        self.config.no_change_timeout = value
        logger.info(f'No-change timeout set to {value}s')

    def set_warning_threshold(self, ratio: float) -> None:
        """Set the warning threshold ratio.

        Args:
            ratio: The ratio (0.0-1.0) at which to show warnings
        """
        if not 0.0 <= ratio <= 1.0:
            raise ValueError('Warning threshold ratio must be between 0.0 and 1.0')

        self.config.warning_threshold_ratio = ratio
        logger.info(f'Warning threshold set to {ratio * 100}%')

    def reset_to_defaults(self) -> None:
        """Reset all timeout values to defaults."""
        self.config = TimeoutConfig()
        logger.info('Timeout configuration reset to defaults')

    def print_current_config(self) -> None:
        """Print the current timeout configuration."""
        print('\n=== Current Timeout Configuration ===')
        print(
            f'Progressive timeout: {"Enabled" if self.config.enable_progressive_timeout else "Disabled"}'
        )
        print(
            f'Adaptive timeout: {"Enabled" if self.config.enable_adaptive_timeout else "Disabled"}'
        )
        print(f'No-change timeout: {self.config.no_change_timeout}s')
        print(f'Warning threshold: {self.config.warning_threshold_ratio * 100}%')

        print('\n--- Default Timeouts ---')
        for timeout_type, value in self.config.default_timeouts.items():
            print(f'{timeout_type.value}: {value}s')

        print('\n--- Maximum Timeouts ---')
        for timeout_type, value in self.config.max_timeouts.items():
            print(f'{timeout_type.value}: {value}s')
        print()

    def get_recommendations(self) -> dict[str, dict[str, Any]]:
        """Get timeout configuration recommendations based on common use cases."""
        recommendations = {
            'development': {
                'description': 'Optimized for development work with shorter timeouts',
                'changes': {
                    TimeoutType.COMMAND_DEFAULT: 60.0,
                    TimeoutType.COMMAND_LONG_RUNNING: 300.0,
                    TimeoutType.COMMAND_NETWORK: 120.0,
                    'no_change_timeout': 20.0,
                },
            },
            'production': {
                'description': 'Optimized for production with longer, more stable timeouts',
                'changes': {
                    TimeoutType.COMMAND_DEFAULT: 180.0,
                    TimeoutType.COMMAND_LONG_RUNNING: 900.0,
                    TimeoutType.COMMAND_NETWORK: 300.0,
                    'no_change_timeout': 60.0,
                },
            },
            'ci_cd': {
                'description': 'Optimized for CI/CD pipelines with build-focused timeouts',
                'changes': {
                    TimeoutType.COMMAND_DEFAULT: 120.0,
                    TimeoutType.COMMAND_LONG_RUNNING: 1800.0,
                    TimeoutType.COMMAND_NETWORK: 600.0,
                    'no_change_timeout': 45.0,
                },
            },
            'research': {
                'description': 'Optimized for research work with very long timeouts',
                'changes': {
                    TimeoutType.COMMAND_DEFAULT: 300.0,
                    TimeoutType.COMMAND_LONG_RUNNING: 3600.0,
                    TimeoutType.COMMAND_NETWORK: 900.0,
                    'no_change_timeout': 120.0,
                },
            },
        }
        return recommendations

    def apply_preset(self, preset_name: str) -> None:
        """Apply a preset timeout configuration.

        Args:
            preset_name: Name of the preset to apply
        """
        recommendations = self.get_recommendations()
        if preset_name not in recommendations:
            available = ', '.join(recommendations.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")

        preset = recommendations[preset_name]
        logger.info(f"Applying preset '{preset_name}': {preset['description']}")

        for key, value in preset['changes'].items():
            if isinstance(key, TimeoutType):
                self.set_timeout(key, value)
            elif key == 'no_change_timeout':
                self.set_no_change_timeout(value)

        logger.info(f"Preset '{preset_name}' applied successfully")

    def print_recommendations(self) -> None:
        """Print available timeout presets and recommendations."""
        recommendations = self.get_recommendations()

        print('\n=== Available Timeout Presets ===')
        for name, info in recommendations.items():
            print(f'\n{name.upper()}:')
            print(f'  Description: {info["description"]}')
            print('  Changes:')
            for key, value in info['changes'].items():
                if isinstance(key, TimeoutType):
                    print(f'    {key.value}: {value}s')
                else:
                    print(f'    {key}: {value}s')
        print()


def main():
    """Command-line interface for timeout configuration."""
    import argparse

    parser = argparse.ArgumentParser(description='Configure OpenHands timeout settings')
    parser.add_argument('--config', help='Path to timeout configuration file')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Show current configuration
    subparsers.add_parser('show', help='Show current timeout configuration')

    # Set timeout values
    set_parser = subparsers.add_parser('set', help='Set a timeout value')
    set_parser.add_argument(
        'type', choices=[t.value for t in TimeoutType], help='Timeout type'
    )
    set_parser.add_argument('value', type=float, help='Timeout value in seconds')

    # Apply presets
    preset_parser = subparsers.add_parser('preset', help='Apply a timeout preset')
    preset_parser.add_argument('name', help='Preset name')

    # Show recommendations
    subparsers.add_parser(
        'recommendations', help='Show available presets and recommendations'
    )

    # Reset to defaults
    subparsers.add_parser('reset', help='Reset to default timeout values')

    args = parser.parse_args()

    configurator = TimeoutConfigurator(args.config)

    if args.command == 'show':
        configurator.print_current_config()
    elif args.command == 'set':
        timeout_type = TimeoutType(args.type)
        configurator.set_timeout(timeout_type, args.value)
        configurator.save_config()
    elif args.command == 'preset':
        configurator.apply_preset(args.name)
        configurator.save_config()
    elif args.command == 'recommendations':
        configurator.print_recommendations()
    elif args.command == 'reset':
        configurator.reset_to_defaults()
        configurator.save_config()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
