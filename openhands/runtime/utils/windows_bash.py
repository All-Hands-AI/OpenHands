"""
Windows-specific implementation of command execution using PowerShell.
"""

import os
import time
import threading
import queue
import subprocess
import sys
from typing import Optional, List
import uuid

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
)
from openhands.events.observation.commands import CmdOutputMetadata
from openhands.utils.shutdown_listener import should_continue


class WindowsBashSession:
    """A Windows-compatible version of BashSession that uses PowerShell."""

    POLL_INTERVAL = 0.5

    def __init__(
        self,
        work_dir: str,
        username: str | None = None,
        no_change_timeout_seconds: int = 30,
        max_memory_mb: int | None = None,
    ):
        self.work_dir = work_dir
        self.username = username
        self.NO_CHANGE_TIMEOUT_SECONDS = no_change_timeout_seconds
        self._initialized = False
        self._output_buffer = ""
        self._cwd = os.path.abspath(work_dir)
        
        # Thread control variables
        self._reader_thread = None
        self._output_queue = queue.Queue()
        self._stop_reader = threading.Event()
        
        # PowerShell process
        self.process = None

    def _run_simple_command(self, command: str, cwd: Optional[str] = None) -> str:
        """Run a simple command directly using subprocess."""
        try:
            result = subprocess.run(
                ["powershell.exe", "-Command", command],
                text=True,
                capture_output=True,
                cwd=cwd or self._cwd
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Error executing simple command: {str(e)}")
            return f"Error: {str(e)}"

    def initialize(self):
        """Initialize the PowerShell session."""
        if self._initialized:
            return

        logger.info("Initializing PowerShell session...")
        try:
            # Start PowerShell process with specific configuration
            self.process = subprocess.Popen(
                ["powershell.exe", "-NoLogo", "-NoExit", "-Command", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=self.work_dir
            )
            
            # Start reader thread
            self._start_reader_thread()
            
            # Configure PowerShell prompt and behavior
            self._send_raw_command("$OutputEncoding = [System.Text.Encoding]::UTF8")
            self._send_raw_command("$PSDefaultParameterValues['*:Encoding'] = 'utf8'")
            self._send_raw_command("$ProgressPreference = 'SilentlyContinue'")
            self._send_raw_command("$ErrorActionPreference = 'Continue'")
            
            # Set up custom prompt for better output parsing
            self._send_raw_command('function prompt { "OH_PS1_$pwd> " }')
            
            logger.info(f"PowerShell session initialized with work dir: {self.work_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize PowerShell: {str(e)}")
            raise RuntimeError(f"Failed to initialize PowerShell session: {str(e)}")
        
        # Now we can mark as initialized
        self._initialized = True
        
        # Clear screen to ensure we start with a clean environment
        self._send_raw_command("Clear-Host")
        # Clear any output from the queue
        while not self._output_queue.empty():
            self._output_queue.get(block=False)

    def _start_reader_thread(self):
        """Start the thread to read output from the process."""
        self._stop_reader = threading.Event()
        self._reader_thread = threading.Thread(target=self._reader_thread_func, daemon=True)
        self._reader_thread.start()
        logger.info("Reader thread started")

    def _reader_thread_func(self):
        """Thread function to read from the PowerShell process."""
        try:
            while not self._stop_reader.is_set() and self.process and self.process.poll() is None:
                char = self.process.stdout.read(1)
                if char:
                    # Queue the character
                    self._output_queue.put(char)
                else:
                    time.sleep(0.01)
        except Exception as e:
            logger.error(f"Error in PowerShell reader thread: {str(e)}")

    def _send_raw_command(self, command: str, wait_time: float = 2.0) -> str:
        """Send a raw command without checking initialization - used during setup."""
        logger.info(f"Sending raw command: {command}")
        
        # Clear any previous output
        while not self._output_queue.empty():
            self._output_queue.get(block=False)
            
        # Send the command directly
        try:
            self.process.stdin.write(command + "\r\n")
            self.process.stdin.flush()
            logger.info(f"Raw command sent to PowerShell: {command}")
        except Exception as e:
            logger.error(f"Error sending raw command to PowerShell: {str(e)}")
            return f"Error sending command: {str(e)}"
        
        # Wait a short time to allow command to complete        
        time.sleep(wait_time)
        
        # Collect any output that's available
        output = []
        while not self._output_queue.empty():
            try:
                data = self._output_queue.get(block=False)
                output.append(data)
            except queue.Empty:
                break
        
        return "".join(output)

    def _send_command(self, command: str, timeout: int = 30) -> str:
        """Send a command and return its output."""
        if not self._initialized:
            raise RuntimeError("PowerShell session is not initialized")

        logger.info(f"Sending command: {command}")
        
        # Clear any previous output
        while not self._output_queue.empty():
            self._output_queue.get(block=False)
        
        # Generate truly unique markers
        uid = str(uuid.uuid4()).replace('-', '')[:8]
        start_marker = f"OH_START_{uid}"
        end_marker = f"OH_END_{uid}"
        
        # Create a PowerShell script to execute the command and capture output
        ps_script = f"""
Write-Host "{start_marker}"
try {{
    $output = & {{ {command} }} 2>&1
    $LASTEXITCODE
    $output | ForEach-Object {{ Write-Host $_ }}
}} catch {{
    Write-Host "ERROR: $_"
    exit 1
}}
Write-Host "{end_marker}"
"""
        
        # Send the script
        try:
            self.process.stdin.write(ps_script + "\r\n")
            self.process.stdin.flush()
            logger.info(f"Command sent to PowerShell: {command}")
        except Exception as e:
            logger.error(f"Error sending command to PowerShell: {str(e)}")
            return f"Error sending command: {str(e)}"
                
        # Track directory changes
        command_lower = command.lower().strip()
        if command_lower.startswith("cd ") or command_lower.startswith("set-location "):
            # Extract the target directory from the command
            parts = command.split(None, 1)
            if len(parts) > 1:
                target_dir = parts[1].strip().strip('"')
                # Handle relative vs absolute paths
                if os.path.isabs(target_dir):
                    self._cwd = target_dir
                else:
                    self._cwd = os.path.normpath(os.path.join(self._cwd, target_dir))

        # Collect output with timeout
        output = []
        in_command_output = False
        command_complete = False
        start_time = time.time()
        last_change_time = start_time
        accumulated_output = ""

        while should_continue() and not command_complete and time.time() - start_time < timeout:
            try:
                # Get output with a short timeout
                try:
                    data = self._output_queue.get(timeout=0.1)
                    accumulated_output += data
                    last_change_time = time.time()
                except queue.Empty:
                    # Check timeouts
                    if time.time() - last_change_time >= self.NO_CHANGE_TIMEOUT_SECONDS:
                        logger.warning(f"Command '{command}' had no output for {self.NO_CHANGE_TIMEOUT_SECONDS} seconds")
                        output.append(f"[Command had no output for {self.NO_CHANGE_TIMEOUT_SECONDS} seconds]")
                        break
                    # Check for hard timeout
                    if time.time() - start_time >= timeout:
                        logger.warning(f"Command '{command}' timed out after {timeout} seconds")
                        output.append(f"[Command timed out after {timeout} seconds]")
                        break
                    time.sleep(0.1)
                    continue
                
                # Check for start marker
                if start_marker in accumulated_output and not in_command_output:
                    logger.info(f"Start marker found in output: {start_marker}")
                    in_command_output = True
                    # Split at the start marker and keep everything after
                    parts = accumulated_output.split(start_marker, 1)
                    accumulated_output = parts[1].lstrip()  # Remove leading whitespace
                    
                # Check for end marker (only if we're collecting command output)
                if end_marker in accumulated_output and in_command_output:
                    logger.info(f"End marker found in output: {end_marker}")
                    command_complete = True
                    # Split at the end marker and keep everything before
                    parts = accumulated_output.split(end_marker, 1)
                    final_output = parts[0].rstrip()  # Remove trailing whitespace
                    
                    # Process the final output
                    for line in final_output.splitlines():
                        output.append(line)
                    break
                
                # If we're collecting command output, save complete lines
                if in_command_output:
                    lines = accumulated_output.splitlines(True)  # Keep line endings
                    if len(lines) > 1:
                        for i in range(len(lines) - 1):
                            output.append(lines[i].rstrip('\r\n'))
                        # Keep the last possibly incomplete line
                        accumulated_output = lines[-1]
                    
            except Exception as e:
                logger.error(f"Error processing command output: {str(e)}")
                output.append(f"[Error processing output: {str(e)}]")
                break

        if not command_complete:
            logger.warning(f"Command '{command}' did not complete properly within timeout")
            # Add an explicit indicator that will be detected in execute()
            output.append(f"[Command did not complete properly within {timeout} seconds]")
            if accumulated_output and in_command_output:
                # Add any remaining output
                for line in accumulated_output.splitlines():
                    output.append(line)

        # Join the collected output lines
        result = "\n".join(output)
        logger.info(f"Command output: {result[:100]}{'...' if len(result) > 100 else ''}")
        return result

    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command in the PowerShell session."""
        if not self._initialized:
            raise RuntimeError("PowerShell session is not initialized")

        command = action.command.strip()
        if not command:
            return CmdOutputObservation(
                content="",
                command="",
                metadata=CmdOutputMetadata(),
            )

        try:
            # Handle special cases and command translations
            if "alias git=" in command:
                # PowerShell doesn't support Bash aliases, so we just ignore this
                command = "Write-Host 'PowerShell does not support Bash aliases. Git will be used as normal.'"
            elif "git --no-pager" in command:
                # This is typically part of a git configuration command
                # We need to adapt it for PowerShell
                command = command.replace(" && alias git=\"git --no-pager\"", "")
            
            # For Git config commands, run directly using subprocess which is more reliable
            if command.startswith("git config"):
                output = self._run_simple_command(command)
            else:
                # Execute the command with timeout from the action or default
                timeout = action.timeout if action.timeout else 30
                logger.info(f"Executing command: {command} with timeout: {timeout}")
                output = self._send_command(command, timeout=timeout)
            
            # Create metadata
            metadata = CmdOutputMetadata()
            metadata.working_dir = self._cwd
            
            # Determine exit code - not available in this implementation
            metadata.exit_code = 0
            
            # Add suffix if the command timed out
            if "[Command had no output for" in output:
                metadata.suffix = (
                    f"\n[The command has no new output after {self.NO_CHANGE_TIMEOUT_SECONDS} seconds. "
                    f"You may wait longer to see additional output by sending empty command '', "
                    f"send other commands to interact with the current process, "
                    f"or send keys to interrupt/kill the command.]"
                )
                metadata.exit_code = -1  # Indicate command is still running
            elif "[Command timed out after" in output:
                timeout_value = action.timeout if action.timeout else 30
                metadata.suffix = (
                    f"\n[The command timed out after {timeout_value} seconds. "
                    f"You may wait longer to see additional output by sending empty command '', "
                    f"send other commands to interact with the current process, "
                    f"or send keys to interrupt/kill the command.]"
                )
                metadata.exit_code = -1  # Indicate command is still running
            elif "[Command did not complete properly within" in output:
                timeout_value = action.timeout if action.timeout else 30
                metadata.suffix = (
                    f"\n[The command did not complete properly within {timeout_value} seconds. "
                    f"You may wait longer to see additional output by sending empty command '', "
                    f"send other commands to interact with the current process, "
                    f"or send keys to interrupt/kill the command.]"
                )
                metadata.exit_code = -1  # Indicate command is still running

            return CmdOutputObservation(
                content=output,
                command=command,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return ErrorObservation(
                content=f"Error executing command: {str(e)}"
            )

    def close(self):
        """Clean up the PowerShell session."""
        # Signal the reader thread to stop
        if self._reader_thread and self._reader_thread.is_alive():
            self._stop_reader.set()
            self._reader_thread.join(timeout=2)
        
        # Close the process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    @property
    def cwd(self):
        return self._cwd 