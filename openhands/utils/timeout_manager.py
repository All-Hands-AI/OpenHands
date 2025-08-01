"""Enhanced timeout management for OpenHands operations."""

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Callable, Optional

from openhands.core.config.timeout_config import (
    TimeoutConfig,
    TimeoutContext,
    TimeoutType,
)
from openhands.core.logger import openhands_logger as logger


class TimeoutManager:
    """Enhanced timeout manager with progressive, adaptive, and context-aware timeout handling."""

    def __init__(self, timeout_config: Optional[TimeoutConfig] = None):
        self.timeout_config = timeout_config or TimeoutConfig()
        self._active_operations: dict[str, dict] = {}

    def get_timeout_context(
        self,
        timeout_type: TimeoutType,
        operation_name: str = '',
        attempt: int = 1,
        complexity_factor: float = 1.0,
        custom_timeout: Optional[float] = None,
        enable_warnings: bool = True,
    ) -> TimeoutContext:
        """Create a timeout context for an operation."""
        return TimeoutContext(
            self.timeout_config,
            timeout_type,
            operation_name,
            attempt,
            complexity_factor,
            custom_timeout,
            enable_warnings,
        )

    @contextmanager
    def timeout_operation(
        self,
        timeout_type: TimeoutType,
        operation_name: str = '',
        attempt: int = 1,
        complexity_factor: float = 1.0,
        custom_timeout: Optional[float] = None,
        enable_warnings: bool = True,
    ):
        """Context manager for timeout operations with enhanced error handling."""
        context = self.get_timeout_context(
            timeout_type,
            operation_name,
            attempt,
            complexity_factor,
            custom_timeout,
            enable_warnings,
        )

        operation_id = f'{operation_name}_{id(context)}'
        start_time = time.time()

        # Track the operation
        self._active_operations[operation_id] = {
            'context': context,
            'start_time': start_time,
            'operation_name': operation_name,
            'timeout_type': timeout_type,
        }

        try:
            yield context
        except Exception as e:
            elapsed_time = time.time() - start_time
            if isinstance(e, (asyncio.TimeoutError, TimeoutError)):
                timeout_message = context.get_timeout_message(elapsed_time)
                logger.warning(f'Timeout occurred: {timeout_message}')
                # Re-raise with enhanced message
                raise TimeoutError(timeout_message) from e
            raise
        finally:
            # Clean up tracking
            self._active_operations.pop(operation_id, None)

    @asynccontextmanager
    async def async_timeout_operation(
        self,
        timeout_type: TimeoutType,
        operation_name: str = '',
        attempt: int = 1,
        complexity_factor: float = 1.0,
        custom_timeout: Optional[float] = None,
        enable_warnings: bool = True,
    ):
        """Async context manager for timeout operations with enhanced error handling."""
        context = self.get_timeout_context(
            timeout_type,
            operation_name,
            attempt,
            complexity_factor,
            custom_timeout,
            enable_warnings,
        )

        operation_id = f'{operation_name}_{id(context)}'
        start_time = time.time()

        # Track the operation
        self._active_operations[operation_id] = {
            'context': context,
            'start_time': start_time,
            'operation_name': operation_name,
            'timeout_type': timeout_type,
        }

        # Set up warning task if enabled
        warning_task = None
        if enable_warnings and context.warning_timeout > 0:
            warning_task = asyncio.create_task(
                self._warning_task(operation_id, context.warning_timeout)
            )

        try:
            yield context
        except Exception as e:
            elapsed_time = time.time() - start_time
            if isinstance(e, (asyncio.TimeoutError, TimeoutError)):
                timeout_message = context.get_timeout_message(elapsed_time)
                logger.warning(f'Timeout occurred: {timeout_message}')
                # Re-raise with enhanced message
                raise asyncio.TimeoutError(timeout_message) from e
            raise
        finally:
            # Cancel warning task
            if warning_task and not warning_task.done():
                warning_task.cancel()
                try:
                    await warning_task
                except asyncio.CancelledError:
                    pass

            # Clean up tracking
            self._active_operations.pop(operation_id, None)

    async def _warning_task(self, operation_id: str, warning_timeout: float):
        """Task to show warning when operation is taking too long."""
        try:
            await asyncio.sleep(warning_timeout)

            # Check if operation is still active
            if operation_id in self._active_operations:
                op_info = self._active_operations[operation_id]
                elapsed = time.time() - op_info['start_time']
                context = op_info['context']

                logger.warning(
                    f"Operation '{op_info['operation_name']}' has been running for "
                    f'{elapsed:.1f}s (timeout in {context.timeout_value - elapsed:.1f}s). '
                    f'Type: {op_info["timeout_type"].value}'
                )
        except asyncio.CancelledError:
            pass

    async def wait_with_timeout(
        self,
        awaitable: Any,
        timeout_type: TimeoutType,
        operation_name: str = '',
        attempt: int = 1,
        complexity_factor: float = 1.0,
        custom_timeout: Optional[float] = None,
    ) -> Any:
        """Wait for an awaitable with enhanced timeout handling."""
        async with self.async_timeout_operation(
            timeout_type, operation_name, attempt, complexity_factor, custom_timeout
        ) as context:
            try:
                return await asyncio.wait_for(awaitable, timeout=context.timeout_value)
            except asyncio.TimeoutError as e:
                elapsed_time = (
                    time.time() - time.time()
                )  # This will be updated by context manager
                raise asyncio.TimeoutError(
                    context.get_timeout_message(elapsed_time)
                ) from e

    def run_with_timeout(
        self,
        func: Callable,
        timeout_type: TimeoutType,
        operation_name: str = '',
        attempt: int = 1,
        complexity_factor: float = 1.0,
        custom_timeout: Optional[float] = None,
        *args,
        **kwargs,
    ) -> Any:
        """Run a function with timeout handling."""
        with self.timeout_operation(
            timeout_type, operation_name, attempt, complexity_factor, custom_timeout
        ) as context:
            # For synchronous operations, we can't easily implement timeout
            # This would need to be implemented using threading or multiprocessing
            # For now, just run the function and let it complete
            logger.debug(
                f'Running {operation_name} with timeout {context.timeout_value}s'
            )
            return func(*args, **kwargs)

    def estimate_complexity_factor(
        self,
        operation_type: str,
        data_size: Optional[int] = None,
        network_involved: bool = False,
        cpu_intensive: bool = False,
        io_intensive: bool = False,
    ) -> float:
        """Estimate complexity factor for adaptive timeout."""
        factor = 1.0

        # Adjust based on data size
        if data_size is not None:
            if data_size > 10 * 1024 * 1024:  # > 10MB
                factor *= 3.0
            elif data_size > 1024 * 1024:  # > 1MB
                factor *= 2.0
            elif data_size > 100 * 1024:  # > 100KB
                factor *= 1.5

        # Adjust based on operation characteristics
        if network_involved:
            factor *= 1.5
        if cpu_intensive:
            factor *= 2.0
        if io_intensive:
            factor *= 1.5

        return factor

    def get_active_operations(self) -> dict[str, dict]:
        """Get information about currently active operations."""
        current_time = time.time()
        active_ops = {}

        for op_id, op_info in self._active_operations.items():
            elapsed = current_time - op_info['start_time']
            context = op_info['context']
            remaining = max(0, context.timeout_value - elapsed)

            active_ops[op_id] = {
                'operation_name': op_info['operation_name'],
                'timeout_type': op_info['timeout_type'].value,
                'elapsed_time': elapsed,
                'remaining_time': remaining,
                'timeout_value': context.timeout_value,
                'progress_ratio': elapsed / context.timeout_value
                if context.timeout_value > 0
                else 0,
            }

        return active_ops

    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an active operation (if possible)."""
        if operation_id in self._active_operations:
            logger.info(f'Cancelling operation: {operation_id}')
            # For now, just remove from tracking
            # In a full implementation, this would need to actually cancel the operation
            self._active_operations.pop(operation_id, None)
            return True
        return False


# Global timeout manager instance
_global_timeout_manager: Optional[TimeoutManager] = None


def get_timeout_manager() -> TimeoutManager:
    """Get the global timeout manager instance."""
    global _global_timeout_manager
    if _global_timeout_manager is None:
        _global_timeout_manager = TimeoutManager()
    return _global_timeout_manager


def set_timeout_manager(manager: TimeoutManager) -> None:
    """Set the global timeout manager instance."""
    global _global_timeout_manager
    _global_timeout_manager = manager


# Convenience functions for common timeout operations
async def wait_with_timeout(
    awaitable: Any,
    timeout_type: TimeoutType,
    operation_name: str = '',
    attempt: int = 1,
    complexity_factor: float = 1.0,
    custom_timeout: Optional[float] = None,
) -> Any:
    """Convenience function to wait for an awaitable with timeout."""
    manager = get_timeout_manager()
    return await manager.wait_with_timeout(
        awaitable,
        timeout_type,
        operation_name,
        attempt,
        complexity_factor,
        custom_timeout,
    )


def run_with_timeout(
    func: Callable,
    timeout_type: TimeoutType,
    operation_name: str = '',
    attempt: int = 1,
    complexity_factor: float = 1.0,
    custom_timeout: Optional[float] = None,
    *args,
    **kwargs,
) -> Any:
    """Convenience function to run a function with timeout."""
    manager = get_timeout_manager()
    return manager.run_with_timeout(
        func,
        timeout_type,
        operation_name,
        attempt,
        complexity_factor,
        custom_timeout,
        *args,
        **kwargs,
    )
