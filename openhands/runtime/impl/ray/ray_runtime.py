"""Ray Runtime implementation for distributed OpenHands execution."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

import ray

from openhands.core.config import OpenHandsConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.llm.llm_registry import LLMRegistry
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.runtime.utils.command import (
    DEFAULT_MAIN_MODULE,
    get_action_execution_server_startup_command,
)
from openhands.utils.tenacity_stop import stop_if_should_exit

from .worker_pool import RayWorkerPool, WorkerSelectionStrategy
from .session_manager import SessionManager, SessionType
from .ray_actor import RayExecutionActor
from .event_broadcaster import RayEventStream
from .auto_scaler import AutoScalingManager, ScalingConfig, ScalingStrategy


class RayRuntime(ActionExecutionClient):
    """Ray-based runtime for distributed OpenHands execution.
    
    This runtime uses Ray actors to execute commands in a distributed manner,
    allowing for horizontal scaling across a Ray cluster.
    """
    
    def __init__(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        llm_registry: LLMRegistry,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
        main_module: str = DEFAULT_MAIN_MODULE,
    ):
        """Initialize the Ray runtime.
        
        Args:
            config: OpenHands configuration
            event_stream: Event stream for communication
            llm_registry: LLM registry
            sid: Session ID
            plugins: List of plugin requirements
            env_vars: Environment variables
            status_callback: Status callback function
            attach_to_existing: Whether to attach to existing runtime
            headless_mode: Whether to run in headless mode
            user_id: User ID
            git_provider_tokens: Git provider tokens
            main_module: Main module to run
        """
        self.config = config
        self.status_callback = status_callback
        self.main_module = main_module
        
        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            try:
                ray.init(
                    address=config.sandbox.ray_cluster_address if hasattr(config.sandbox, 'ray_cluster_address') else None,
                    ignore_reinit_error=True
                )
                logger.info("Ray initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Ray: {e}")
                raise AgentRuntimeError(f"Ray initialization failed: {e}")
        
        # Create workspace directory
        self.workspace_path = os.path.join(
            tempfile.gettempdir(), 
            f"openhands-ray-workspace-{sid}-{uuid4().hex[:8]}"
        )
        os.makedirs(self.workspace_path, exist_ok=True)
        
        # Prepare environment variables
        self._env_vars = env_vars or {}
        self._env_vars.update({
            'OPENHANDS_SESSION_ID': sid,
            'OPENHANDS_WORKSPACE_PATH': self.workspace_path,
        })
        
        # Create worker pool and session manager
        pool_size = getattr(config.sandbox, 'ray_worker_pool_size', 3)
        max_pool_size = getattr(config.sandbox, 'ray_max_pool_size', 10)
        selection_strategy = getattr(config.sandbox, 'ray_selection_strategy', 'least_busy')
        
        strategy_map = {
            'round_robin': WorkerSelectionStrategy.ROUND_ROBIN,
            'least_busy': WorkerSelectionStrategy.LEAST_BUSY,
            'random': WorkerSelectionStrategy.RANDOM,
            'session_affinity': WorkerSelectionStrategy.SESSION_AFFINITY,
        }
        
        self.worker_pool = RayWorkerPool(
            pool_size=pool_size,
            max_pool_size=max_pool_size,
            selection_strategy=strategy_map.get(selection_strategy, WorkerSelectionStrategy.LEAST_BUSY),
            workspace_path=self.workspace_path,
            env_vars=self._env_vars
        )
        
        self.session_manager = SessionManager()
        self.session_id = sid
        
        # Create session for this runtime instance
        self.session_manager.create_session(
            session_type=SessionType.COMBINED,
            session_id=self.session_id
        )
        
        # Initialize distributed event streaming
        self.distributed_event_stream = RayEventStream(
            session_id=sid,
            worker_pool=self.worker_pool
        )
        self._event_stream_initialized = False
        
        # Initialize auto-scaling
        scaling_config = ScalingConfig(
            min_workers=getattr(config.sandbox, 'ray_min_workers', 2),
            max_workers=getattr(config.sandbox, 'ray_max_workers', 20),
            scale_up_queue_threshold=getattr(config.sandbox, 'ray_scale_up_queue_threshold', 10),
            scale_down_queue_threshold=getattr(config.sandbox, 'ray_scale_down_queue_threshold', 2),
            scale_up_response_time_threshold=getattr(config.sandbox, 'ray_scale_up_response_time_threshold', 5.0),
            cpu_scale_up_threshold=getattr(config.sandbox, 'ray_cpu_scale_up_threshold', 0.8),
            cpu_scale_down_threshold=getattr(config.sandbox, 'ray_cpu_scale_down_threshold', 0.3),
            cooldown_period=getattr(config.sandbox, 'ray_scaling_cooldown_period', 60.0),
            strategy=ScalingStrategy(getattr(config.sandbox, 'ray_scaling_strategy', 'hybrid'))
        )
        
        self.auto_scaler = AutoScalingManager(scaling_config, self.worker_pool)
        self._auto_scaling_enabled = getattr(config.sandbox, 'ray_auto_scaling_enabled', True)
        self._auto_scaling_initialized = False
        
        # Legacy compatibility: maintain reference for backward compatibility
        # This will be deprecated once all methods use worker pool
        self.actor = None
        
        logger.info(f"RayRuntime initialized for session {sid}")
        logger.info(f"Workspace path: {self.workspace_path}")
        
        # Call parent constructor
        super().__init__(
            config,
            event_stream,
            llm_registry,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
            user_id,
            git_provider_tokens,
        )
    
    async def connect(self) -> None:
        """Connect to the Ray runtime."""
        try:
            # Initialize worker pool and session manager
            await self.worker_pool.initialize()
            await self.session_manager.initialize()
            
            # Initialize distributed event streaming
            await self.distributed_event_stream.initialize()
            self._event_stream_initialized = True
            logger.info("Distributed event streaming initialized")
            
            # Initialize auto-scaling if enabled
            if self._auto_scaling_enabled:
                await self.auto_scaler.initialize()
                self._auto_scaling_initialized = True
                logger.info("Auto-scaling system initialized")
            else:
                logger.info("Auto-scaling disabled by configuration")
            
            # Test that the worker pool is responsive with a simple action
            test_action_data = {
                'type': 'CmdRunAction',
                'command': "echo 'Ray runtime connected'",
                'timeout': 30
            }
            result = await self.worker_pool.execute_action(test_action_data, self.session_id)
            
            if result.get('exit_code') == 0:
                logger.info("Ray runtime connected successfully")
                self._runtime_initialized = True
                if self.status_callback:
                    self.status_callback('info', RuntimeStatus.RUNNING, 'Ray runtime connected')
            else:
                raise AgentRuntimeError(f"Ray worker pool connection test failed: {result}")
                
        except Exception as e:
            logger.error(f"Failed to connect to Ray runtime: {e}")
            if self.status_callback:
                self.status_callback('error', RuntimeStatus.ERROR, f'Ray connection failed: {e}')
            raise AgentRuntimeDisconnectedError(f"Ray runtime connection failed: {e}")
    
    def close(self) -> None:
        """Close the Ray runtime and cleanup resources."""
        try:
            # Shutdown worker pool and session manager using same pattern as actions
            def shutdown_async_components():
                async def shutdown():
                    if hasattr(self, 'worker_pool'):
                        await self.worker_pool.shutdown()
                        logger.info("Ray worker pool terminated")
                    
                    if hasattr(self, 'session_manager'):
                        await self.session_manager.shutdown()
                        logger.info("Session manager terminated")
                    
                    if hasattr(self, 'distributed_event_stream'):
                        self.distributed_event_stream.close()
                        logger.info("Distributed event stream closed")
                    
                    if hasattr(self, 'auto_scaler') and self._auto_scaling_initialized:
                        await self.auto_scaler.shutdown()
                        logger.info("Auto-scaling system shutdown")
                
                return shutdown()
            
            # Handle async shutdown the same way as actions
            try:
                loop = asyncio.get_running_loop()
                # In async context - run in thread
                import concurrent.futures
                
                def run_in_new_loop():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(shutdown_async_components())
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_new_loop)
                    future.result()
                    
            except RuntimeError:
                # No event loop running
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(shutdown_async_components())
                finally:
                    loop.close()
            
            # Legacy cleanup for backward compatibility
            if hasattr(self, 'actor') and self.actor:
                ray.kill(self.actor)
                logger.info("Ray actor terminated")
            
            # Cleanup workspace directory
            if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
                import shutil
                shutil.rmtree(self.workspace_path, ignore_errors=True)
                logger.info(f"Workspace directory cleaned up: {self.workspace_path}")
                
        except Exception as e:
            logger.error(f"Error closing Ray runtime: {e}")
        
        super().close()
    
    @property
    def api_url(self) -> str:
        """Return the API URL for the runtime."""
        # Ray runtime doesn't use HTTP API, return a placeholder
        return f"ray://workspace/{self.workspace_path}"
    
    @property
    def workspace_root(self) -> Path:
        """Return the workspace root path."""
        return Path(self.workspace_path)
    
    def get_working_directory(self) -> str:
        """Get the current working directory."""
        return self.workspace_path
    
    def _run_async_action(self, action_data: dict, session_id: Optional[str] = None, timeout: Optional[float] = None) -> dict:
        """Helper to run async worker pool actions synchronously."""
        try:
            # Check if we're already in an async context
            loop = asyncio.get_running_loop()
            # If we get here, we're in an async context - need to run in thread
            import concurrent.futures
            import threading
            
            def run_in_new_loop():
                # Create a new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        self.worker_pool.execute_action(action_data, session_id or self.session_id, timeout)
                    )
                finally:
                    new_loop.close()
            
            # Run in a separate thread to avoid event loop conflicts
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result()
                
        except RuntimeError:
            # No event loop running, we can create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.worker_pool.execute_action(action_data, session_id or self.session_id, timeout)
                )
            finally:
                loop.close()
    
    # Override ActionExecutionClient methods to use Ray worker pool instead of HTTP
    
    def run(self, action) -> 'Observation':
        """Execute a CmdRunAction using Ray worker pool."""
        from openhands.events.observation import CmdOutputObservation, ErrorObservation
        
        try:
            # Execute command via Ray worker pool
            action_data = {
                'type': 'CmdRunAction',
                'command': action.command,
                'timeout': action.timeout or 60
            }
            
            result = self._run_async_action(action_data, timeout=action.timeout or 60)
            
            # Convert Ray result to CmdOutputObservation
            return CmdOutputObservation(
                content=result.get('stdout', ''),
                exit_code=result.get('exit_code', 1),
                command=action.command,
                command_id=action.id,
            )
        except Exception as e:
            logger.error(f"Error executing command action via Ray: {e}")
            return ErrorObservation(
                f"Ray execution failed: {str(e)}",
                error_id='RAY_EXECUTION_ERROR'
            )
    
    def read(self, action) -> 'Observation':
        """Execute a FileReadAction using Ray worker pool."""
        from openhands.events.observation import FileReadObservation, ErrorObservation
        
        try:
            # Read file via Ray worker pool
            action_data = {
                'type': 'FileReadAction',
                'path': action.path
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return FileReadObservation(
                    content=result.get('content', ''),
                    path=action.path,
                )
            else:
                return ErrorObservation(
                    f"Failed to read file: {result.get('error', 'Unknown error')}",
                    error_id='FILE_READ_ERROR'
                )
        except Exception as e:
            logger.error(f"Error reading file via Ray: {e}")
            return ErrorObservation(
                f"Ray file read failed: {str(e)}",
                error_id='RAY_FILE_READ_ERROR'
            )
    
    def write(self, action) -> 'Observation':
        """Execute a FileWriteAction using Ray worker pool."""
        from openhands.events.observation import FileWriteObservation, ErrorObservation
        
        try:
            # Write file via Ray worker pool
            action_data = {
                'type': 'FileWriteAction',
                'path': action.path,
                'content': action.content
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return FileWriteObservation(
                    content=action.content,
                    path=action.path,
                )
            else:
                return ErrorObservation(
                    f"Failed to write file: {result.get('error', 'Unknown error')}",
                    error_id='FILE_WRITE_ERROR'
                )
        except Exception as e:
            logger.error(f"Error writing file via Ray: {e}")
            return ErrorObservation(
                f"Ray file write failed: {str(e)}",
                error_id='RAY_FILE_WRITE_ERROR'
            )
    
    def edit(self, action) -> 'Observation':
        """Execute a FileEditAction using Ray worker pool."""
        from openhands.events.observation import FileEditObservation, ErrorObservation
        
        try:
            # Use Ray worker pool to perform file edit
            action_data = {
                'type': 'FileEditAction',
                'path': action.path,
                'new_str': action.new_str,
                'old_str': getattr(action, 'old_str', None),
                'start_line': getattr(action, 'start_line', None),
                'end_line': getattr(action, 'end_line', None)
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return FileEditObservation(
                    content=result.get('content', ''),
                    path=action.path,
                )
            else:
                return ErrorObservation(
                    f"Failed to edit file: {result.get('error', 'Unknown error')}",
                    error_id='FILE_EDIT_ERROR'
                )
        except Exception as e:
            logger.error(f"Error editing file via Ray: {e}")
            return ErrorObservation(
                f"Ray file edit failed: {str(e)}",
                error_id='RAY_FILE_EDIT_ERROR'
            )
    
    def run_ipython(self, action) -> 'Observation':
        """Execute an IPythonRunCellAction using Ray worker pool."""
        from openhands.events.observation import IPythonRunCellObservation, ErrorObservation
        
        try:
            # Execute IPython code via Ray worker pool (using session affinity for kernel state)
            action_data = {
                'type': 'IPythonRunCellAction',
                'code': action.code,
                'kernel_init_code': getattr(action, 'kernel_init_code', None)
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return IPythonRunCellObservation(
                    content=result.get('content', ''),
                    code=action.code,
                )
            else:
                return ErrorObservation(
                    f"Failed to run IPython code: {result.get('error', 'Unknown error')}",
                    error_id='IPYTHON_EXECUTION_ERROR'
                )
        except Exception as e:
            logger.error(f"Error executing IPython code via Ray: {e}")
            return ErrorObservation(
                f"Ray IPython execution failed: {str(e)}",
                error_id='RAY_IPYTHON_ERROR'
            )
    
    def browse(self, action) -> 'Observation':
        """Execute a BrowseURLAction using Ray worker pool."""
        from openhands.events.observation import BrowserOutputObservation, ErrorObservation
        
        try:
            # Browse URL via Ray worker pool
            action_data = {
                'type': 'BrowseURLAction',
                'url': action.url
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return BrowserOutputObservation(
                    content=result.get('content', ''),
                    url=action.url,
                    screenshot=result.get('screenshot'),
                )
            else:
                return ErrorObservation(
                    f"Failed to browse URL: {result.get('error', 'Unknown error')}",
                    error_id='BROWSER_ERROR'
                )
        except Exception as e:
            logger.error(f"Error browsing URL via Ray: {e}")
            return ErrorObservation(
                f"Ray browser failed: {str(e)}",
                error_id='RAY_BROWSER_ERROR'
            )
    
    def browse_interactive(self, action) -> 'Observation':
        """Execute a BrowseInteractiveAction using Ray worker pool."""
        from openhands.events.observation import BrowserOutputObservation, ErrorObservation
        
        try:
            # Interactive browse via Ray worker pool
            action_data = {
                'type': 'BrowseInteractiveAction',
                'browser_actions': getattr(action, 'browser_actions', [])
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return BrowserOutputObservation(
                    content=result.get('content', ''),
                    url=result.get('url', ''),
                    screenshot=result.get('screenshot'),
                )
            else:
                return ErrorObservation(
                    f"Failed to perform interactive browsing: {result.get('error', 'Unknown error')}",
                    error_id='INTERACTIVE_BROWSER_ERROR'
                )
        except Exception as e:
            logger.error(f"Error with interactive browsing via Ray: {e}")
            return ErrorObservation(
                f"Ray interactive browser failed: {str(e)}",
                error_id='RAY_INTERACTIVE_BROWSER_ERROR'
            )
    
    # Distributed Event Streaming Methods
    
    def subscribe_to_distributed_events(
        self, 
        subscriber_id: str, 
        callback: Callable, 
        callback_id: str,
        worker_id: Optional[str] = None
    ) -> None:
        """Subscribe to distributed events across the Ray cluster.
        
        Args:
            subscriber_id: Type of subscriber
            callback: Callback function to handle events
            callback_id: Unique identifier for this callback
            worker_id: Optional worker ID for distributed callbacks
        """
        if self._event_stream_initialized:
            self.distributed_event_stream.subscribe(
                subscriber_id, callback, callback_id, worker_id
            )
        else:
            logger.warning("Distributed event stream not initialized, skipping subscription")
    
    def unsubscribe_from_distributed_events(
        self, 
        subscriber_id: str, 
        callback_id: str
    ) -> None:
        """Unsubscribe from distributed events.
        
        Args:
            subscriber_id: Type of subscriber
            callback_id: Unique identifier for this callback
        """
        if self._event_stream_initialized:
            self.distributed_event_stream.unsubscribe(subscriber_id, callback_id)
    
    def broadcast_event(self, event: 'Event', source: 'EventSource') -> None:
        """Broadcast an event across the distributed Ray cluster.
        
        Args:
            event: Event to broadcast
            source: Source of the event
        """
        if self._event_stream_initialized:
            self.distributed_event_stream.add_event(event, source)
        else:
            logger.warning("Distributed event stream not initialized, event not broadcasted")
    
    async def get_distributed_event_stats(self) -> dict:
        """Get statistics about the distributed event streaming system."""
        if self._event_stream_initialized:
            return await self.distributed_event_stream.get_stats()
        else:
            return {'error': 'Distributed event stream not initialized'}
    
    async def get_recent_distributed_events(self, limit: int = 10) -> list:
        """Get recent events from the distributed event stream."""
        if self._event_stream_initialized:
            return await self.distributed_event_stream.get_recent_events(limit)
        else:
            return []
    
    # Auto-Scaling Methods
    
    async def get_auto_scaling_stats(self) -> dict:
        """Get auto-scaling statistics and configuration."""
        if self._auto_scaling_initialized:
            return await self.auto_scaler.get_stats()
        else:
            return {'error': 'Auto-scaling not initialized'}
    
    async def force_scaling_check(self) -> dict:
        """Force an immediate scaling check and return the decision."""
        if self._auto_scaling_initialized:
            return await self.auto_scaler.force_scaling_check()
        else:
            return {'error': 'Auto-scaling not initialized'}
    
    def add_scaling_callback(self, callback: Callable) -> None:
        """Add a callback to be notified of scaling events.
        
        Args:
            callback: Callback function taking (direction, amount, success)
        """
        if self._auto_scaling_initialized:
            self.auto_scaler.add_scaling_callback(callback)
        else:
            logger.warning("Cannot add scaling callback: auto-scaling not initialized")
    
    def remove_scaling_callback(self, callback: Callable) -> None:
        """Remove a scaling callback.
        
        Args:
            callback: Callback function to remove
        """
        if self._auto_scaling_initialized:
            self.auto_scaler.remove_scaling_callback(callback)
        else:
            logger.warning("Cannot remove scaling callback: auto-scaling not initialized")
    
    def is_auto_scaling_enabled(self) -> bool:
        """Check if auto-scaling is enabled and initialized."""
        return self._auto_scaling_enabled and self._auto_scaling_initialized