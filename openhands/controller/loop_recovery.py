"""Loop recovery manager for handling agent stuck in loop scenarios."""

import asyncio
from typing import Optional, TYPE_CHECKING

from openhands.controller.stuck import StuckDetector
from openhands.core.exceptions import AgentStuckInLoopError
from openhands.core.schema import AgentState
from openhands.events import Event, EventSource
from openhands.events.action import MessageAction
from openhands.events.action.message import SystemMessageAction

try:
    import aioconsole
    HAS_AIOCONSOLE = True
except ImportError:
    HAS_AIOCONSOLE = False

if TYPE_CHECKING:
    from openhands.controller.agent_controller import AgentController
    from openhands.controller.state.state import State
    from openhands.memory.memory import Memory


class LoopRecoveryManager:
    """Manages recovery from agent loops by preserving context and providing recovery options."""
    
    def __init__(self, controller: 'AgentController'):
        self.controller = controller
        self.state = controller.state
        self.event_stream = controller.event_stream
        self.stuck_detector = StuckDetector(self.state)
    
    async def handle_loop_detection(self, filtered_history: list[Event]) -> bool:
        """Handle loop detection and attempt recovery.
        
        Args:
            filtered_history: The filtered event history to analyze
            
        Returns:
            bool: True if recovery was successful and agent should continue, False otherwise
        """
        loop_info = self.stuck_detector.analyze_loop_pattern(filtered_history)
        
        if not loop_info['loop_detected']:
            return False
        
        # Check if we're in CLI mode
        is_cli_mode = self._is_cli_mode()
        print(f"DEBUG: Loop detected! is_cli_mode = {is_cli_mode}")
        
        if is_cli_mode:
            print("DEBUG: Entering CLI recovery mode...")
            return await self._handle_cli_recovery(loop_info, filtered_history)
        else:
            print("DEBUG: Entering automatic recovery mode...")
            return await self._handle_automatic_recovery(loop_info, filtered_history)
    
    def _is_cli_mode(self) -> bool:
        """Check if we're running in CLI mode."""
        # CLI mode has status_callback AND is in headless mode
        # GUI mode has status_callback but headless_mode=False
        return (
            self.controller.status_callback is not None 
            and self.controller.headless_mode
        )
    
    async def _handle_cli_recovery(self, loop_info: dict, filtered_history: list[Event]) -> bool:
        """Handle loop recovery in CLI mode with user interaction."""
        loop_start = loop_info['loop_start_index']
        recovery_point = loop_info['suggested_recovery_point']
        
        # Calculate what would be preserved vs discarded
        preserved_events = filtered_history[:recovery_point] if recovery_point > 0 else []
        discarded_events = filtered_history[recovery_point:] if recovery_point > 0 else filtered_history
        
        # Present recovery options to user
        print("\n" + "="*60)
        print("⚠️  Agent detected in a loop!")
        print("="*60)
        print(f"Loop type: {loop_info['loop_type']}")
        print(f"Loop detected at iteration {self.state.iteration_flag.current_value}")
        print(f"\nRecovery options:")
        print(f"1. Restart from before loop (preserves {len(preserved_events)} events)")
        print(f"2. Stop agent completely")
        
        # Use prompt_toolkit for input in CLI mode
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.patch_stdout import patch_stdout
            from prompt_toolkit.formatted_text import HTML
            
            # Try to get config from agent to create proper prompt session
            config = None
            if hasattr(self.controller.agent, 'config'):
                config = self.controller.agent.config
            
            # Create a prompt session with config if available
            if config and hasattr(config, 'cli') and hasattr(config.cli, 'vi_mode'):
                session = PromptSession(vi_mode=config.cli.vi_mode)
            else:
                session = PromptSession()
            
            # Get user input (no timeout - wait indefinitely for user response)
            with patch_stdout():
                choice = await session.prompt_async(
                    HTML('<gold>Choose option (1-2): </gold>')
                )
            
            choice = choice.strip()
            if choice == '1':
                return await self._perform_recovery(loop_info, filtered_history)
            elif choice == '2':
                print("Stopping agent...")
                return False
            else:
                print(f"Invalid choice: '{choice}'. Defaulting to option 1 (recovery).")
                return await self._perform_recovery(loop_info, filtered_history)
                
        except asyncio.TimeoutError:
            print("\nInput timeout. Defaulting to option 1 (recovery).")
            return await self._perform_recovery(loop_info, filtered_history)
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled. Defaulting to option 2 (stop).")
            return False
        except Exception as e:
            print(f"\nInput error: {e}. Defaulting to option 1 (recovery).")
            return await self._perform_recovery(loop_info, filtered_history)
    
    async def _async_input(self, prompt: str) -> str:
        """Get user input asynchronously without blocking the event loop.
        
        This method uses a combination of approaches:
        1. First tries aioconsole.ainput() if available
        2. Falls back to a simple synchronous input with timeout
        """
        try:
            # Try aioconsole first if available
            if HAS_AIOCONSOLE:
                return await aioconsole.ainput(prompt)
        except Exception:
            # aioconsole failed, fall through
            pass
        
        # Use simple synchronous input with timeout
        print(prompt, end='', flush=True)
        
        try:
            # Use asyncio.to_thread with a shorter timeout
            return await asyncio.wait_for(
                asyncio.to_thread(input, ""),
                timeout=10.0  # 10 second timeout
            )
        except asyncio.TimeoutError:
            print("\nInput timeout. Defaulting to option 1 (recovery).")
            return "1"
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled. Defaulting to option 3 (stop).")
            return "3"
        except Exception:
            print("\nInput error. Defaulting to option 1 (recovery).")
            return "1"

    async def _handle_automatic_recovery(self, loop_info: dict, filtered_history: list[Event]) -> bool:
        """Handle loop detection in GUI/automated mode - return False to maintain original behavior."""
        # For GUI mode, maintain original behavior by returning False
        # This will cause the agent to exit naturally as before
        print(f"Agent detected in loop (type: {loop_info['loop_type']}) in GUI mode. Exiting as per original behavior.")
        return False
    
    async def _perform_recovery(self, loop_info: dict, filtered_history: list[Event]) -> bool:
        """Perform the actual recovery by truncating history and adding recovery message."""
        recovery_point = loop_info['suggested_recovery_point']
        
        if recovery_point <= 0:
            # If we can't find a good recovery point, fall back to original behavior
            return False
        
        try:
            # Truncate the memory to before the loop started
            await self._truncate_memory_to_point(recovery_point)
            
            # Add a system message explaining the recovery
            recovery_message = (
                f"System: Agent was detected in a loop (type: {loop_info['loop_type']}). "
                f"Conversation has been reset to before the loop started. "
                f"Please continue from this point with a different approach."
            )
            
            recovery_action = SystemMessageAction(
                content=recovery_message
            )
            
            self.event_stream.add_event(recovery_action, EventSource.AGENT)
            
            # Reset the agent state to allow continuation
            # Set to AWAITING_USER_INPUT so TUI will prompt for next input
            if hasattr(self.controller, 'set_agent_state_to'):
                await self.controller.set_agent_state_to(AgentState.AWAITING_USER_INPUT)
            
            print(f"✓ Recovery successful! Reset to before loop (preserved {recovery_point} events)")
            return True
            
        except Exception as e:
            print(f"✗ Recovery failed: {e}")
            return False
    
    async def _truncate_memory_to_point(self, recovery_point: int) -> None:
        """Truncate memory to a specific point in the event history."""
        # Get all events from state history
        all_events = self.state.history
        
        if recovery_point >= len(all_events):
            # Nothing to truncate
            return
        
        # Keep only events up to the recovery point
        events_to_keep = all_events[:recovery_point]
        
        # Update state history
        self.state.history = events_to_keep
        
        # Update end_id to reflect the truncation
        if events_to_keep:
            self.state.end_id = events_to_keep[-1].id
        else:
            self.state.end_id = -1
    
    def should_attempt_recovery(self) -> bool:
        """Determine if recovery should be attempted based on configuration and context."""
        # Check if recovery is enabled in configuration
        # For now, always attempt recovery in CLI mode
        return self._is_cli_mode()