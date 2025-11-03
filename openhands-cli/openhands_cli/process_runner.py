"""
Process-based conversation runner for handling agent execution in a separate process.

This allows for immediate termination of the agent when needed while maintaining
the ability to gracefully pause on the first Ctrl+C.
"""

import multiprocessing
import queue
import signal
import threading
import time
from enum import Enum
from typing import Any, Dict, Optional

from openhands.sdk import BaseConversation, Message
from openhands.sdk.conversation.state import AgentExecutionStatus
from prompt_toolkit import HTML, print_formatted_text

from openhands_cli.runner import ConversationRunner


class ProcessCommand(Enum):
    """Commands that can be sent to the conversation process."""
    PROCESS_MESSAGE = "process_message"
    PAUSE = "pause"
    RESUME = "resume"
    TOGGLE_CONFIRMATION = "toggle_confirmation"
    GET_STATUS = "get_status"
    SHUTDOWN = "shutdown"


class ProcessResponse(Enum):
    """Response types from the conversation process."""
    SUCCESS = "success"
    ERROR = "error"
    STATUS = "status"


def conversation_worker(
    conversation_id: str,
    command_queue: multiprocessing.Queue,
    response_queue: multiprocessing.Queue,
    setup_conversation_func: Any,  # Function to setup conversation
) -> None:
    """Worker function that runs in a separate process to handle conversation."""
    
    # Set up signal handling in the worker process
    def signal_handler(signum, frame):
        print_formatted_text(HTML('<yellow>Conversation process received termination signal.</yellow>'))
        return
        
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignore SIGINT in worker process
    
    try:
        # Setup conversation in the worker process
        conversation = setup_conversation_func(conversation_id)
        runner = ConversationRunner(conversation)
        
        response_queue.put({
            "type": ProcessResponse.SUCCESS,
            "message": "Conversation process initialized"
        })
        
        while True:
            try:
                # Check for commands with timeout
                try:
                    command_data = command_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                    
                command = command_data.get("command")
                args = command_data.get("args", {})
                
                if command == ProcessCommand.SHUTDOWN:
                    break
                    
                elif command == ProcessCommand.PROCESS_MESSAGE:
                    message = args.get("message")
                    try:
                        runner.process_message(message)
                        response_queue.put({
                            "type": ProcessResponse.SUCCESS,
                            "message": "Message processed"
                        })
                    except Exception as e:
                        response_queue.put({
                            "type": ProcessResponse.ERROR,
                            "message": f"Error processing message: {e}"
                        })
                        
                elif command == ProcessCommand.PAUSE:
                    try:
                        runner.conversation.pause()
                        response_queue.put({
                            "type": ProcessResponse.SUCCESS,
                            "message": "Conversation paused"
                        })
                    except Exception as e:
                        response_queue.put({
                            "type": ProcessResponse.ERROR,
                            "message": f"Error pausing conversation: {e}"
                        })
                        
                elif command == ProcessCommand.RESUME:
                    try:
                        runner.process_message(None)  # Resume without new message
                        response_queue.put({
                            "type": ProcessResponse.SUCCESS,
                            "message": "Conversation resumed"
                        })
                    except Exception as e:
                        response_queue.put({
                            "type": ProcessResponse.ERROR,
                            "message": f"Error resuming conversation: {e}"
                        })
                        
                elif command == ProcessCommand.TOGGLE_CONFIRMATION:
                    try:
                        runner.toggle_confirmation_mode()
                        new_status = 'enabled' if runner.is_confirmation_mode_active else 'disabled'
                        response_queue.put({
                            "type": ProcessResponse.SUCCESS,
                            "message": f"Confirmation mode {new_status}"
                        })
                    except Exception as e:
                        response_queue.put({
                            "type": ProcessResponse.ERROR,
                            "message": f"Error toggling confirmation mode: {e}"
                        })
                        
                elif command == ProcessCommand.GET_STATUS:
                    try:
                        status = {
                            "agent_status": runner.conversation.state.agent_status,
                            "confirmation_mode": runner.is_confirmation_mode_active
                        }
                        response_queue.put({
                            "type": ProcessResponse.STATUS,
                            "data": status
                        })
                    except Exception as e:
                        response_queue.put({
                            "type": ProcessResponse.ERROR,
                            "message": f"Error getting status: {e}"
                        })
                        
            except Exception as e:
                response_queue.put({
                    "type": ProcessResponse.ERROR,
                    "message": f"Unexpected error in conversation worker: {e}"
                })
                
    except Exception as e:
        response_queue.put({
            "type": ProcessResponse.ERROR,
            "message": f"Failed to initialize conversation process: {e}"
        })


class ProcessBasedConversationRunner:
    """Manages a conversation runner in a separate process."""
    
    def __init__(self, conversation_id: str, setup_conversation_func: Any):
        self.conversation_id = conversation_id
        self.setup_conversation_func = setup_conversation_func
        self.process: Optional[multiprocessing.Process] = None
        self.command_queue: Optional[multiprocessing.Queue] = None
        self.response_queue: Optional[multiprocessing.Queue] = None
        self.is_running = False
        
    def start(self) -> bool:
        """Start the conversation process."""
        if self.is_running:
            return True
            
        try:
            # Create queues for communication
            self.command_queue = multiprocessing.Queue()
            self.response_queue = multiprocessing.Queue()
            
            # Start the worker process
            self.process = multiprocessing.Process(
                target=conversation_worker,
                args=(
                    self.conversation_id,
                    self.command_queue,
                    self.response_queue,
                    self.setup_conversation_func
                )
            )
            self.process.start()
            
            # Wait for initialization confirmation
            try:
                response = self.response_queue.get(timeout=10.0)
                if response["type"] == ProcessResponse.SUCCESS:
                    self.is_running = True
                    return True
                else:
                    print_formatted_text(HTML(f'<red>Failed to initialize conversation process: {response.get("message", "Unknown error")}</red>'))
                    self.stop()
                    return False
            except queue.Empty:
                print_formatted_text(HTML('<red>Timeout waiting for conversation process to initialize</red>'))
                self.stop()
                return False
                
        except Exception as e:
            print_formatted_text(HTML(f'<red>Error starting conversation process: {e}</red>'))
            return False
            
    def stop(self) -> None:
        """Stop the conversation process."""
        if not self.is_running:
            return
            
        try:
            if self.command_queue:
                self.command_queue.put({"command": ProcessCommand.SHUTDOWN})
                
            if self.process:
                self.process.join(timeout=2.0)
                if self.process.is_alive():
                    self.process.terminate()
                    self.process.join(timeout=1.0)
                    if self.process.is_alive():
                        self.process.kill()
                        
        except Exception as e:
            print_formatted_text(HTML(f'<yellow>Warning: Error stopping conversation process: {e}</yellow>'))
            
        finally:
            self.is_running = False
            self.process = None
            self.command_queue = None
            self.response_queue = None
            
    def send_command(self, command: ProcessCommand, args: Optional[Dict] = None, timeout: float = 5.0) -> Optional[Dict]:
        """Send a command to the conversation process and wait for response."""
        if not self.is_running or not self.command_queue or not self.response_queue:
            return None
            
        try:
            command_data = {"command": command, "args": args or {}}
            self.command_queue.put(command_data)
            
            response = self.response_queue.get(timeout=timeout)
            return response
            
        except queue.Empty:
            print_formatted_text(HTML(f'<yellow>Timeout waiting for response to {command.value}</yellow>'))
            return None
        except Exception as e:
            print_formatted_text(HTML(f'<red>Error sending command {command.value}: {e}</red>'))
            return None
            
    def process_message(self, message: Optional[Message]) -> bool:
        """Process a message through the conversation."""
        response = self.send_command(ProcessCommand.PROCESS_MESSAGE, {"message": message})
        if response and response["type"] == ProcessResponse.SUCCESS:
            return True
        elif response:
            print_formatted_text(HTML(f'<red>{response.get("message", "Unknown error")}</red>'))
        return False
        
    def pause(self) -> bool:
        """Pause the conversation."""
        response = self.send_command(ProcessCommand.PAUSE)
        if response and response["type"] == ProcessResponse.SUCCESS:
            return True
        elif response:
            print_formatted_text(HTML(f'<red>{response.get("message", "Unknown error")}</red>'))
        return False
        
    def resume(self) -> bool:
        """Resume the conversation."""
        response = self.send_command(ProcessCommand.RESUME)
        if response and response["type"] == ProcessResponse.SUCCESS:
            return True
        elif response:
            print_formatted_text(HTML(f'<red>{response.get("message", "Unknown error")}</red>'))
        return False
        
    def toggle_confirmation_mode(self) -> Optional[str]:
        """Toggle confirmation mode and return the new status."""
        response = self.send_command(ProcessCommand.TOGGLE_CONFIRMATION)
        if response and response["type"] == ProcessResponse.SUCCESS:
            return response.get("message")
        elif response:
            print_formatted_text(HTML(f'<red>{response.get("message", "Unknown error")}</red>'))
        return None
        
    def get_status(self) -> Optional[Dict]:
        """Get the current status of the conversation."""
        response = self.send_command(ProcessCommand.GET_STATUS)
        if response and response["type"] == ProcessResponse.STATUS:
            return response.get("data")
        elif response:
            print_formatted_text(HTML(f'<red>{response.get("message", "Unknown error")}</red>'))
        return None
        
    def is_alive(self) -> bool:
        """Check if the conversation process is alive."""
        return self.is_running and self.process and self.process.is_alive()
        
    def force_terminate(self) -> None:
        """Force terminate the conversation process immediately."""
        if self.process and self.process.is_alive():
            self.process.kill()
            self.process.join(timeout=1.0)
        self.is_running = False