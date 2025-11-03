"""
Simple process-based conversation runner for OpenHands CLI.

Only the actual conversation running (process_message) is wrapped in a separate process.
All other methods run in the main process.
"""

import multiprocessing
from typing import Any, Optional

from openhands.sdk import BaseConversation, Message
from openhands_cli.runner import ConversationRunner


def _run_conversation_in_process(conversation: BaseConversation, message: Optional[Message], result_queue: multiprocessing.Queue):
    """Run the conversation in a separate process."""
    try:
        # Create conversation runner
        runner = ConversationRunner(conversation)
        
        # Process the message
        runner.process_message(message)
        
        # Put success result in the queue
        result_queue.put(('success', None))
        
    except KeyboardInterrupt:
        result_queue.put(('interrupted', None))
    except Exception as e:
        result_queue.put(('error', str(e)))


class SimpleProcessRunner:
    """Simple conversation runner that only uses multiprocessing for the actual conversation."""
    
    def __init__(self, conversation: BaseConversation):
        """Initialize the process runner.
        
        Args:
            conversation: The conversation instance
        """
        self.conversation = conversation
        self.current_process: Optional[multiprocessing.Process] = None
        self.result_queue: Optional[multiprocessing.Queue] = None
        
        # Create a runner for main process operations
        self.runner = ConversationRunner(conversation)
        
    def process_message(self, message: Optional[Message]) -> bool:
        """Process a message in a separate process.
        
        Args:
            message: The user message to process
            
        Returns:
            True if successful, False otherwise
        """
        # Create queue for result
        self.result_queue = multiprocessing.Queue()
        
        # Create and start process
        self.current_process = multiprocessing.Process(
            target=_run_conversation_in_process,
            args=(self.conversation, message, self.result_queue)
        )
        self.current_process.start()
        
        # Wait for result
        try:
            result_type, result_data = self.result_queue.get()
            self.current_process.join()
            
            if result_type == 'success':
                return True
            elif result_type == 'interrupted':
                print("Agent was interrupted by user")
                return False
            else:
                print(f"Process error: {result_data}")
                return False
                
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
            'conversation_id': self.conversation.id,
            'agent_status': self.conversation.state.agent_status.value if self.conversation.state else 'unknown',
            'is_running': self.current_process is not None and self.current_process.is_alive()
        }
    
    def toggle_confirmation_mode(self) -> bool:
        """Toggle confirmation mode (runs in main process)."""
        self.runner.toggle_confirmation_mode()
        # Update our conversation reference
        self.conversation = self.runner.conversation
        return self.conversation.is_confirmation_mode_active
    
    def resume(self) -> None:
        """Resume the agent (runs in main process)."""
        # This would be handled by the conversation state
        pass
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.current_process and self.current_process.is_alive():
            self.current_process.terminate()
            self.current_process.join(timeout=2)
            if self.current_process.is_alive():
                self.current_process.kill()
                self.current_process.join()
        
        # Clean up conversation resources if needed
        if hasattr(self.conversation, 'close'):
            self.conversation.close()