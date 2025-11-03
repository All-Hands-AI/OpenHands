"""
Signal handling for graceful shutdown and immediate termination.

This module provides a signal handler that tracks Ctrl+C presses:
- First Ctrl+C: Attempt graceful pause of the agent
- Second Ctrl+C: Immediately terminate the process
"""

import signal
import threading
import time
from typing import Callable, Optional

from prompt_toolkit import HTML, print_formatted_text


class SignalHandler:
    """Handles SIGINT (Ctrl+C) with graceful shutdown on first press and immediate termination on second."""
    
    def __init__(self, graceful_shutdown_callback: Optional[Callable] = None):
        self.graceful_shutdown_callback = graceful_shutdown_callback
        self.sigint_count = 0
        self.last_sigint_time = 0.0
        self.sigint_timeout = 3.0  # Reset counter after 3 seconds
        self.lock = threading.Lock()
        self.original_handler = None
        
    def install(self) -> None:
        """Install the signal handler."""
        self.original_handler = signal.signal(signal.SIGINT, self._handle_sigint)
        
    def uninstall(self) -> None:
        """Restore the original signal handler."""
        if self.original_handler is not None:
            signal.signal(signal.SIGINT, self.original_handler)
            self.original_handler = None
            
    def _handle_sigint(self, signum: int, frame) -> None:
        """Handle SIGINT (Ctrl+C) signal."""
        current_time = time.time()
        
        with self.lock:
            # Reset counter if too much time has passed since last Ctrl+C
            if current_time - self.last_sigint_time > self.sigint_timeout:
                self.sigint_count = 0
                
            self.sigint_count += 1
            self.last_sigint_time = current_time
            
            if self.sigint_count == 1:
                # First Ctrl+C: attempt graceful shutdown
                print_formatted_text(HTML('\n<yellow>Received Ctrl+C. Attempting to pause agent gracefully...</yellow>'))
                print_formatted_text(HTML('<grey>Press Ctrl+C again within 3 seconds to force immediate termination.</grey>'))
                
                if self.graceful_shutdown_callback:
                    try:
                        self.graceful_shutdown_callback()
                    except Exception as e:
                        print_formatted_text(HTML(f'<red>Error during graceful shutdown: {e}</red>'))
                        
            elif self.sigint_count >= 2:
                # Second Ctrl+C: immediate termination
                print_formatted_text(HTML('\n<red>Received second Ctrl+C. Terminating immediately...</red>'))
                self.uninstall()
                # Force immediate exit
                import os
                os._exit(1)


class ProcessSignalHandler:
    """Signal handler for managing conversation runner processes."""
    
    def __init__(self):
        self.conversation_process = None
        self.signal_handler = None
        
    def set_conversation_process(self, process) -> None:
        """Set the conversation process to manage."""
        self.conversation_process = process
        
    def graceful_shutdown(self) -> None:
        """Attempt graceful shutdown of the conversation process."""
        if hasattr(self, 'conversation_process') and self.conversation_process and self.conversation_process.is_alive():
            print_formatted_text(HTML('<yellow>Pausing agent once current step is completed...</yellow>'))
            # Send SIGTERM to the process for graceful shutdown
            self.conversation_process.terminate()
            
            # Give it a moment to shut down gracefully
            self.conversation_process.join(timeout=2.0)
            
            if self.conversation_process.is_alive():
                print_formatted_text(HTML('<yellow>Agent is taking time to pause. Press Ctrl+C again to force termination.</yellow>'))
            else:
                print_formatted_text(HTML('<green>Agent paused successfully.</green>'))
        else:
            print_formatted_text(HTML('<yellow>No active conversation process to pause.</yellow>'))
                
    def install_handler(self) -> None:
        """Install the signal handler."""
        self.signal_handler = SignalHandler(graceful_shutdown_callback=self.graceful_shutdown)
        self.signal_handler.install()
        
    def uninstall_handler(self) -> None:
        """Uninstall the signal handler."""
        if self.signal_handler:
            self.signal_handler.uninstall()
            self.signal_handler = None
            
    def force_terminate(self) -> None:
        """Force terminate the conversation process."""
        if self.conversation_process and self.conversation_process.is_alive():
            self.conversation_process.kill()
            self.conversation_process.join(timeout=1.0)