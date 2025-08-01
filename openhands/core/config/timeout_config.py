"""Timeout configuration for OpenHands operations."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TimeoutType(str, Enum):
    """Different types of timeout scenarios."""

    # Command execution timeouts
    COMMAND_DEFAULT = 'command_default'
    COMMAND_LONG_RUNNING = 'command_long_running'
    COMMAND_INTERACTIVE = 'command_interactive'
    COMMAND_NETWORK = 'command_network'

    # Runtime operation timeouts
    RUNTIME_INIT = 'runtime_init'
    RUNTIME_SHUTDOWN = 'runtime_shutdown'
    RUNTIME_HEALTH_CHECK = 'runtime_health_check'

    # LLM operation timeouts
    LLM_REQUEST = 'llm_request'
    LLM_STREAMING = 'llm_streaming'

    # File operation timeouts
    FILE_READ = 'file_read'
    FILE_WRITE = 'file_write'
    FILE_LARGE_OPERATION = 'file_large_operation'

    # Browser operation timeouts
    BROWSER_NAVIGATION = 'browser_navigation'
    BROWSER_INTERACTION = 'browser_interaction'
    BROWSER_WAIT = 'browser_wait'

    # General async operation timeouts
    ASYNC_GENERAL = 'async_general'
    ASYNC_BACKGROUND = 'async_background'


class TimeoutStrategy(str, Enum):
    """Different timeout strategies."""

    FIXED = 'fixed'  # Fixed timeout value
    PROGRESSIVE = 'progressive'  # Increasing timeout on retries
    ADAPTIVE = 'adaptive'  # Timeout based on operation complexity
    CONTEXT_AWARE = 'context_aware'  # Timeout based on execution context


class TimeoutConfig(BaseModel):
    """Configuration for timeout handling."""

    # Default timeout values (in seconds)
    default_timeouts: dict[TimeoutType, float] = Field(
        default_factory=lambda: {
            # Command execution timeouts
            TimeoutType.COMMAND_DEFAULT: 120.0,
            TimeoutType.COMMAND_LONG_RUNNING: 600.0,
            TimeoutType.COMMAND_INTERACTIVE: 30.0,
            TimeoutType.COMMAND_NETWORK: 180.0,
            # Runtime operation timeouts
            TimeoutType.RUNTIME_INIT: 300.0,
            TimeoutType.RUNTIME_SHUTDOWN: 60.0,
            TimeoutType.RUNTIME_HEALTH_CHECK: 30.0,
            # LLM operation timeouts
            TimeoutType.LLM_REQUEST: 120.0,
            TimeoutType.LLM_STREAMING: 300.0,
            # File operation timeouts
            TimeoutType.FILE_READ: 30.0,
            TimeoutType.FILE_WRITE: 60.0,
            TimeoutType.FILE_LARGE_OPERATION: 300.0,
            # Browser operation timeouts
            TimeoutType.BROWSER_NAVIGATION: 60.0,
            TimeoutType.BROWSER_INTERACTION: 30.0,
            TimeoutType.BROWSER_WAIT: 10.0,
            # General async operation timeouts
            TimeoutType.ASYNC_GENERAL: 15.0,
            TimeoutType.ASYNC_BACKGROUND: 300.0,
        }
    )

    # Progressive timeout multipliers for retries
    progressive_multipliers: dict[int, float] = Field(
        default_factory=lambda: {
            1: 1.0,  # First attempt
            2: 1.5,  # Second attempt (50% longer)
            3: 2.0,  # Third attempt (100% longer)
            4: 3.0,  # Fourth attempt (200% longer)
        }
    )

    # Maximum timeout values (safety limits)
    max_timeouts: dict[TimeoutType, float] = Field(
        default_factory=lambda: {
            TimeoutType.COMMAND_DEFAULT: 1800.0,  # 30 minutes max
            TimeoutType.COMMAND_LONG_RUNNING: 3600.0,  # 1 hour max
            TimeoutType.COMMAND_INTERACTIVE: 300.0,  # 5 minutes max
            TimeoutType.COMMAND_NETWORK: 600.0,  # 10 minutes max
            TimeoutType.RUNTIME_INIT: 900.0,  # 15 minutes max
            TimeoutType.RUNTIME_SHUTDOWN: 300.0,  # 5 minutes max
            TimeoutType.RUNTIME_HEALTH_CHECK: 120.0,  # 2 minutes max
            TimeoutType.LLM_REQUEST: 600.0,  # 10 minutes max
            TimeoutType.LLM_STREAMING: 1800.0,  # 30 minutes max
            TimeoutType.FILE_READ: 300.0,  # 5 minutes max
            TimeoutType.FILE_WRITE: 600.0,  # 10 minutes max
            TimeoutType.FILE_LARGE_OPERATION: 1800.0,  # 30 minutes max
            TimeoutType.BROWSER_NAVIGATION: 300.0,  # 5 minutes max
            TimeoutType.BROWSER_INTERACTION: 180.0,  # 3 minutes max
            TimeoutType.BROWSER_WAIT: 60.0,  # 1 minute max
            TimeoutType.ASYNC_GENERAL: 300.0,  # 5 minutes max
            TimeoutType.ASYNC_BACKGROUND: 3600.0,  # 1 hour max
        }
    )

    # No-change timeout for commands (when output stops changing)
    no_change_timeout: float = Field(default=30.0)

    # Enable progressive timeout strategy
    enable_progressive_timeout: bool = Field(default=True)

    # Enable adaptive timeout based on command complexity
    enable_adaptive_timeout: bool = Field(default=True)

    # Timeout warning threshold (warn when timeout is close)
    warning_threshold_ratio: float = Field(default=0.8)  # Warn at 80% of timeout

    def get_timeout(
        self,
        timeout_type: TimeoutType,
        attempt: int = 1,
        complexity_factor: float = 1.0,
        custom_timeout: Optional[float] = None,
    ) -> float:
        """Get the appropriate timeout value for a given operation.

        Args:
            timeout_type: The type of timeout needed
            attempt: The attempt number (for progressive timeout)
            complexity_factor: Factor to adjust timeout based on operation complexity
            custom_timeout: Custom timeout value to use instead of default

        Returns:
            The timeout value in seconds
        """
        if custom_timeout is not None:
            base_timeout = custom_timeout
        else:
            base_timeout = self.default_timeouts.get(timeout_type, 120.0)

        # Apply progressive timeout multiplier
        if self.enable_progressive_timeout and attempt > 1:
            multiplier = self.progressive_multipliers.get(attempt, 3.0)
            base_timeout *= multiplier

        # Apply complexity factor for adaptive timeout
        if self.enable_adaptive_timeout:
            base_timeout *= complexity_factor

        # Ensure we don't exceed maximum timeout
        max_timeout = self.max_timeouts.get(timeout_type, base_timeout * 10)
        return min(base_timeout, max_timeout)

    def get_warning_timeout(self, timeout_type: TimeoutType, attempt: int = 1) -> float:
        """Get the timeout value at which to show a warning."""
        full_timeout = self.get_timeout(timeout_type, attempt)
        return full_timeout * self.warning_threshold_ratio


class TimeoutContext:
    """Context manager for timeout operations with enhanced error handling."""

    def __init__(
        self,
        timeout_config: TimeoutConfig,
        timeout_type: TimeoutType,
        operation_name: str = '',
        attempt: int = 1,
        complexity_factor: float = 1.0,
        custom_timeout: Optional[float] = None,
        enable_warnings: bool = True,
    ):
        self.timeout_config = timeout_config
        self.timeout_type = timeout_type
        self.operation_name = operation_name
        self.attempt = attempt
        self.complexity_factor = complexity_factor
        self.custom_timeout = custom_timeout
        self.enable_warnings = enable_warnings
        self._cancelled = False

        self.timeout_value = self.timeout_config.get_timeout(
            timeout_type, attempt, complexity_factor, custom_timeout
        )
        self.warning_timeout = self.timeout_config.get_warning_timeout(
            timeout_type, attempt
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def cancel(self) -> None:
        """Mark this context as cancelled."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if this context has been cancelled."""
        return self._cancelled

    def get_timeout_message(self, elapsed_time: float) -> str:
        """Generate an informative timeout message."""
        message_parts = []

        if self.operation_name:
            message_parts.append(f"Operation '{self.operation_name}' timed out")
        else:
            message_parts.append(
                f'Operation of type {self.timeout_type.value} timed out'
            )

        message_parts.append(f'after {elapsed_time:.1f} seconds')

        if self.attempt > 1:
            message_parts.append(f'(attempt {self.attempt})')

        message_parts.append(f'(timeout was {self.timeout_value:.1f}s)')

        # Add recovery suggestions
        suggestions = self._get_recovery_suggestions()
        if suggestions:
            message_parts.append(f'\n\nSuggestions:\n{suggestions}')

        return ' '.join(message_parts)

    def _get_recovery_suggestions(self) -> str:
        """Get context-specific recovery suggestions."""
        suggestions = []

        if self.timeout_type in [
            TimeoutType.COMMAND_DEFAULT,
            TimeoutType.COMMAND_LONG_RUNNING,
        ]:
            suggestions.extend(
                [
                    "• Send an empty command '' to wait for more output",
                    "• Send 'C-c' to interrupt the current process",
                    '• Use a longer timeout for future similar commands',
                    '• Check if the command is waiting for input',
                ]
            )
        elif self.timeout_type == TimeoutType.RUNTIME_INIT:
            suggestions.extend(
                [
                    '• Check runtime logs for initialization errors',
                    '• Verify runtime dependencies are available',
                    '• Try restarting the runtime environment',
                ]
            )
        elif self.timeout_type in [TimeoutType.LLM_REQUEST, TimeoutType.LLM_STREAMING]:
            suggestions.extend(
                [
                    '• Check network connectivity to LLM provider',
                    '• Verify API credentials are valid',
                    '• Try reducing the request complexity',
                ]
            )
        elif self.timeout_type in [
            TimeoutType.BROWSER_NAVIGATION,
            TimeoutType.BROWSER_INTERACTION,
        ]:
            suggestions.extend(
                [
                    '• Check if the page is still loading',
                    '• Verify the target element exists',
                    '• Try refreshing the page',
                ]
            )

        return '\n'.join(suggestions) if suggestions else ''
