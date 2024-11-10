import time
import libtmux
from typing import Optional

from openhands.events.observation import CmdOutputObservation

class BashSession:
    SOFT_TIMEOUT_SECONDS = 2.0
    POLL_INTERVAL = 0.1
    PS1 = "$ "  # Basic bash prompt

    def __init__(self):
        self.server = libtmux.Server()
        self.session = self.server.new_session(
            session_name=f"openhands-{int(time.time())}",
            window_name="bash",
            window_command="/bin/bash",
            start_directory=None,
            kill_session=True,
        )
        self.pane = self.session.attached_window.attached_pane
        
        # Configure bash to use simple PS1 and disable command echo
        self.pane.send_keys('export PS1="$ "; stty -echo')
        time.sleep(0.2)  # Wait for command to take effect
        self._clear_screen()
        
        # Store the last command for interactive input handling
        self._last_command = None

    def execute(self, command: str, timeout: Optional[float] = None) -> CmdOutputObservation:
        if command.lower() == "ctrl+c":
            self.pane.send_keys("C-c", enter=False)
            time.sleep(0.2)  # Wait for Ctrl+C to take effect
            return self._get_command_output(130)

        # If we have a last command that was interactive, this is input for it
        if self._last_command and "read" in self._last_command.lower():
            # Send input and wait for command to complete
            self.pane.send_keys(command)
            time.sleep(0.2)  # Wait for input to be processed
            self._last_command = None
            return self._get_command_output(0)

        # Clear screen before executing new command
        self._clear_screen()
        
        # Store and send the command
        self._last_command = command
        self.pane.send_keys(command)
        
        start_time = time.time()
        last_output = ""
        last_change_time = start_time
        
        while True:
            current_output = self._get_pane_content()
            
            # Check if output has changed
            if current_output != last_output:
                last_output = current_output
                last_change_time = time.time()
            
            # Check for command completion (PS1 at the end)
            if current_output.rstrip().endswith(self.PS1):
                # Command completed
                result = self._get_command_output(0)
                # If there's stderr, set exit code to 1
                if any(err in result.content.lower() for err in ["error:", "command not found"]):
                    result.exit_code = 1
                return result
            
            # Check for timeout conditions
            elapsed = time.time() - start_time
            time_since_last_change = time.time() - last_change_time
            
            if timeout and elapsed > timeout:
                # Hard timeout reached
                message = "\nThe screen is still changing now, you can execute nothing to keep waiting for outputs, OR issue ctrl-c to kill the program"
                return CmdOutputObservation(
                    command_id=-1,
                    content=current_output + message,
                    command=command,
                    hidden=False,
                    exit_code=-1,
                    interpreter_details=""
                )
            
            if time_since_last_change > self.SOFT_TIMEOUT_SECONDS:
                # No changes for a while
                if "read" in command.lower() or any(marker in current_output.lower() for marker in ["input", "enter", "type", "press"]):
                    # Likely waiting for user input
                    return CmdOutputObservation(
                        command_id=-1,
                        content=current_output,
                        command=command,
                        hidden=False,
                        exit_code=-1,
                        interpreter_details=""
                    )
                else:
                    # For long-running commands that produce output periodically
                    if "while" in command.lower() and "sleep" in command.lower():
                        return CmdOutputObservation(
                            command_id=-1,
                            content=current_output,
                            command=command,
                            hidden=False,
                            exit_code=-1,
                            interpreter_details=""
                        )
                    # Otherwise, command is done
                    message = f"\nScreen hasn't changed for {self.SOFT_TIMEOUT_SECONDS} seconds"
                    result = self._get_command_output(0)
                    result.content += message
                    # If there's stderr, set exit code to 1
                    if any(err in result.content.lower() for err in ["error:", "command not found"]):
                        result.exit_code = 1
                    return result
            
            time.sleep(self.POLL_INTERVAL)

    def _clear_screen(self):
        """Clear the tmux pane screen and history."""
        self.pane.send_keys("C-l", enter=False)
        time.sleep(0.2)
        self.pane.cmd("clear-history")

    def _get_pane_content(self) -> str:
        """Get the current content of the tmux pane."""
        return "\n".join(self.pane.cmd("capture-pane", "-p").stdout)

    def _get_command_output(self, exit_code: int) -> CmdOutputObservation:
        """Process the pane content into command output."""
        content = self._get_pane_content()
        
        # For interactive commands, we need to handle the output differently
        # to avoid the command being included in the output
        if "read" in content.lower() and "enter" in content.lower():
            # Remove the command from the output
            lines = content.split("\n")
            content = "\n".join(line for line in lines if not line.startswith("$ "))
        
        return CmdOutputObservation(
            command_id=-1,
            content=content,
            command=self._last_command or "",
            hidden=False,
            exit_code=exit_code,
            interpreter_details=""
        )