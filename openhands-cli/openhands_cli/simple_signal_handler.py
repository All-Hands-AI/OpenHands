"""
Simple signal handling for Ctrl+C behavior in OpenHands CLI.

- First Ctrl+C: Attempt graceful pause of the agent
- Second Ctrl+C: Immediately kill the process
"""

import signal
import time
from typing import Optional

from prompt_toolkit import HTML, print_formatted_text


class SimpleSignalHandler:
    """Simple signal handler that tracks Ctrl+C presses and manages a subprocess."""
    
    def __init__(self):
        self.ctrl_c_count = 0
        self.last_ctrl_c_time = 0.0
        self.timeout = 3.0  # Reset counter after 3 seconds
        self.original_handler = None
        self.current_process: Optional[object] = None
        
    def install(self) -> None:
        """Install the signal handler."""
        self.original_handler = signal.signal(signal.SIGINT, self._handle_ctrl_c)
        
    def uninstall(self) -> None:
        """Restore the original signal handler."""
        if self.original_handler is not None:
            signal.signal(signal.SIGINT, self.original_handler)
            self.original_handler = None
            
    def reset_count(self) -> None:
        """Reset the Ctrl+C count (called when starting new message processing)."""
        self.ctrl_c_count = 0
        self.last_ctrl_c_time = 0.0
        
    def set_process(self, process) -> None:
        """Set the current process to manage."""
        self.current_process = process
        
    def _handle_ctrl_c(self, signum: int, frame) -> None:
        """Handle Ctrl+C signal."""
        current_time = time.time()
        
        # Reset counter if too much time has passed
        if current_time - self.last_ctrl_c_time > self.timeout:
            self.ctrl_c_count = 0
            
        self.ctrl_c_count += 1
        self.last_ctrl_c_time = current_time
        
        if self.ctrl_c_count == 1:
            print_formatted_text(HTML('<yellow>Received Ctrl+C. Attempting to pause agent...</yellow>'))
            if self.current_process and self.current_process.is_alive():
                self.current_process.terminate()
                print_formatted_text(HTML('<yellow>Press Ctrl+C again within 3 seconds to force kill.</yellow>'))
            else:
                print_formatted_text(HTML('<yellow>No active process to pause.</yellow>'))
        else:
            print_formatted_text(HTML('<red>Received second Ctrl+C. Force killing process...</red>'))
            if self.current_process and self.current_process.is_alive():
                self.current_process.kill()
            import os
            os._exit(1)