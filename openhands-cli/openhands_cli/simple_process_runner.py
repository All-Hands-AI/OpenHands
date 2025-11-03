"""
Simple process-based conversation runner for OpenHands CLI.

Only the actual conversation running (process_message) is wrapped in a separate process.
All other methods run in the main process.
"""

import multiprocessing
from typing import Any, Callable, Optional

from openhands.core.main import run_controller
from openhands.events.action import MessageAction
from openhands.events.observation import AgentFinishObservation


def _run_conversation_in_process(conversation_id: str, setup_func: Callable, message: str, result_queue: multiprocessing.Queue):
    """Run the conversation in a separate process."""
    try:
        # Set up the conversation components
        controller, agent, runtime = setup_func()
        
        # Create and process the message action
        action = MessageAction(content=message)
        
        # Run the controller with the action
        result = run_controller(
            controller=controller,
            agent=agent,
            runtime=runtime,
            initial_user_action=action,
            max_iterations=100,
            max_budget_per_task=None,
            agent_to_llm_config=None,
            agent_configs=None,
        )
        
        # Put the result in the queue
        result_queue.put(('success', result))
        
    except KeyboardInterrupt:
        result_queue.put(('interrupted', None))
    except Exception as e:
        result_queue.put(('error', str(e)))


class SimpleProcessRunner:
    """Simple conversation runner that only uses multiprocessing for the actual conversation."""
    
    def __init__(self, conversation_id: str, setup_func: Callable):
        self.conversation_id = conversation_id
        self.setup_func = setup_func
        self.current_process: Optional[multiprocessing.Process] = None
        self.result_queue: Optional[multiprocessing.Queue] = None
        
        # Set up conversation components in main process for non-process methods
        self.controller, self.agent, self.runtime = setup_func()
        
    def process_message(self, message: str) -> Any:
        """Process a message in a separate process."""
        # Create queue for result
        self.result_queue = multiprocessing.Queue()
        
        # Create and start process
        self.current_process = multiprocessing.Process(
            target=_run_conversation_in_process,
            args=(self.conversation_id, self.setup_func, message, self.result_queue)
        )
        self.current_process.start()
        
        # Wait for result
        try:
            result_type, result_data = self.result_queue.get()
            self.current_process.join()
            
            if result_type == 'success':
                return result_data
            elif result_type == 'interrupted':
                return AgentFinishObservation(content="Agent was interrupted by user")
            else:
                raise Exception(f"Process error: {result_data}")
                
        except Exception as e:
            if self.current_process.is_alive():
                self.current_process.terminate()
                self.current_process.join(timeout=2)
                if self.current_process.is_alive():
                    self.current_process.kill()
                    self.current_process.join()
            raise e
        finally:
            self.current_process = None
            self.result_queue = None
    
    def get_status(self) -> dict:
        """Get conversation status (runs in main process)."""
        return {
            'conversation_id': self.conversation_id,
            'agent_state': getattr(self.agent, 'state', None),
            'is_running': self.current_process is not None and self.current_process.is_alive()
        }
    
    def toggle_confirmation_mode(self) -> bool:
        """Toggle confirmation mode (runs in main process)."""
        if hasattr(self.agent, 'confirmation_mode'):
            self.agent.confirmation_mode = not getattr(self.agent, 'confirmation_mode', False)
            return self.agent.confirmation_mode
        return False
    
    def resume(self) -> None:
        """Resume the agent (runs in main process)."""
        if hasattr(self.agent, 'state'):
            self.agent.state.resume()
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.current_process and self.current_process.is_alive():
            self.current_process.terminate()
            self.current_process.join(timeout=2)
            if self.current_process.is_alive():
                self.current_process.kill()
                self.current_process.join()
        
        if hasattr(self.runtime, 'close'):
            self.runtime.close()