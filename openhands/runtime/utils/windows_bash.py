"""
Windows-specific implementation of command execution using Windows ConPTY.
"""

import os
import time
import threading
import queue
import subprocess
import sys
from typing import Optional, List
import uuid

try:
    import winpty
    HAS_WINPTY = True
except ImportError:
    try:
        import pwinpty
        HAS_WINPTY = True
    except ImportError:
        HAS_WINPTY = False

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
)
from openhands.events.observation.commands import CmdOutputMetadata
from openhands.utils.shutdown_listener import should_continue


class WindowsBashSession:
    """A Windows-compatible version of BashSession that uses Windows command processor."""

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
        
        # Check for ConPTY support
        if not HAS_WINPTY:
            logger.warning("Neither winpty nor pwinpty is installed. Falling back to subprocess implementation.")
            self._use_winpty = False
        else:
            self._use_winpty = True
            
        # Either winpty.PTY or subprocess.Popen
        self.pty = None
        self.process = None

    def _run_simple_command(self, command: str, cwd: Optional[str] = None) -> str:
        """Run a simple command directly using subprocess (no ConPTY)."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                cwd=cwd or self._cwd
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Error executing simple command: {str(e)}")
            return f"Error: {str(e)}"

    def initialize(self):
        """Initialize the Windows command session."""
        if self._initialized:
            return

        if self._use_winpty:
            try:
                # Use the ConPTY approach
                logger.info("Initializing Windows ConPTY session...")
                if 'winpty' in sys.modules:
                    # Using the winpty package
                    self.pty = winpty.PTY(cols=120, rows=30)
                    self.pty.spawn('cmd.exe')
                    logger.info("ConPTY object created successfully with winpty")
                else:
                    # Using the pwinpty package
                    self.pty = pwinpty.PtyProcess.spawn('cmd.exe')
                    logger.info("ConPTY object created successfully with pwinpty")
                
                # Start reader thread
                self._start_reader_thread()
                
                # Change to working directory - using a direct method that doesn't check initialization
                self._send_raw_command(f"cd /d \"{self.work_dir}\"")
                
                logger.info(f"Windows ConPTY session initialized with work dir: {self.work_dir}")
            except Exception as e:
                logger.error(f"Failed to initialize ConPTY: {str(e)}")
                self._use_winpty = False
                
        if not self._use_winpty:
            # Fallback to subprocess approach
            logger.info("Initializing Windows subprocess session...")
            try:
                self.process = subprocess.Popen(
                    ["cmd.exe"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=self.work_dir
                )
                
                # Start reader thread
                self._start_reader_thread()
                
                # No need to change directory as we start in the right directory
                
                logger.info(f"Windows subprocess session initialized with work dir: {self.work_dir}")
            except Exception as e:
                logger.error(f"Failed to initialize subprocess: {str(e)}")
                raise RuntimeError(f"Failed to initialize Windows command session: {str(e)}")
        
        # Now we can mark as initialized
        self._initialized = True
        
        # Clear screen to ensure we start with a clean environment
        if self._use_winpty:
            self._send_raw_command("cls")
        else:
            self.process.stdin.write("cls\r\n")
            self.process.stdin.flush()
            # Clear any output from the queue
            while not self._output_queue.empty():
                self._output_queue.get(block=False)

    def _start_reader_thread(self):
        """Start the thread to read output from the process."""
        self._stop_reader = threading.Event()
        if self._use_winpty:
            self._reader_thread = threading.Thread(target=self._winpty_reader_thread, daemon=True)
        else:
            self._reader_thread = threading.Thread(target=self._subprocess_reader_thread, daemon=True)
        self._reader_thread.start()
        logger.info("Reader thread started")

    def _winpty_reader_thread(self):
        """Thread function to read from the ConPTY process."""
        try:
            while not self._stop_reader.is_set() and self.pty:
                try:
                    # Read available data
                    data = self.pty.read()
                    if data:
                        # Queue the data
                        logger.debug(f"ConPTY read data: {repr(data[:100])}{'...' if len(data) > 100 else ''}")
                        self._output_queue.put(data)
                    else:
                        time.sleep(0.01)
                except Exception as e:
                    logger.warning(f"Error reading from ConPTY: {str(e)}")
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in ConPTY reader thread: {str(e)}")

    def _subprocess_reader_thread(self):
        """Thread function to read from the subprocess."""
        try:
            while not self._stop_reader.is_set() and self.process and self.process.poll() is None:
                char = self.process.stdout.read(1)
                if char:
                    # Queue the character
                    self._output_queue.put(char)
                else:
                    time.sleep(0.01)
        except Exception as e:
            logger.error(f"Error in subprocess reader thread: {str(e)}")

    def _send_raw_command(self, command: str, wait_time: float = 2.0) -> str:
        """Send a raw command without checking initialization - used during setup."""
        logger.info(f"Sending raw command: {command}")
        
        # Clear any previous output
        while not self._output_queue.empty():
            self._output_queue.get(block=False)
            
        # Send the command directly
        if self._use_winpty:
            try:
                self.pty.write(command + "\r\n")
                logger.info(f"Raw command sent to ConPTY: {command}")
            except Exception as e:
                logger.error(f"Error sending raw command to ConPTY: {str(e)}")
                return f"Error sending command: {str(e)}"
        else:
            try:
                self.process.stdin.write(command + "\r\n")
                self.process.stdin.flush()
                logger.info(f"Raw command sent to subprocess: {command}")
            except Exception as e:
                logger.error(f"Error sending raw command to subprocess: {str(e)}")
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
            raise RuntimeError("Windows session is not initialized")

        logger.info(f"Sending command: {command}")
        
        # Clear any previous output
        while not self._output_queue.empty():
            self._output_queue.get(block=False)
        
        # Generate truly unique markers (don't use the command hash)
        uid = str(uuid.uuid4()).replace('-', '')[:8]
        start_marker = f"OH_START_{uid}"
        end_marker = f"OH_END_{uid}"
        
        # We'll use a file to capture the output - more reliable than echo
        # We'll use a temporary batch file to execute the command and capture its output
        temp_script = f"""
@echo off
echo {start_marker}
{command}
echo {end_marker}
"""
        # Temp file path
        temp_file = os.path.join(self._cwd, f"oh_cmd_{uid}.bat")
        
        # Write the temporary batch file
        try:
            with open(temp_file, 'w') as f:
                f.write(temp_script)
        except Exception as e:
            logger.error(f"Error creating temp batch file: {str(e)}")
            return f"Error creating temp batch file: {str(e)}"
        
        # Prepare the command to run the batch file
        batch_command = f"\"{temp_file}\""
        
        # Send the command
        if self._use_winpty:
            try:
                self.pty.write(batch_command + "\r\n")
                logger.info(f"Batch command sent to ConPTY: {batch_command}")
            except Exception as e:
                logger.error(f"Error sending batch command to ConPTY: {str(e)}")
                # Try to clean up
                try:
                    os.remove(temp_file)
                except:
                    pass
                return f"Error sending command: {str(e)}"
        else:
            try:
                self.process.stdin.write(batch_command + "\r\n")
                self.process.stdin.flush()
                logger.info(f"Batch command sent to subprocess: {batch_command}")
            except Exception as e:
                logger.error(f"Error sending batch command to subprocess: {str(e)}")
                # Try to clean up
                try:
                    os.remove(temp_file)
                except:
                    pass
                return f"Error sending command: {str(e)}"
                
        # Track directory changes
        command_lower = command.lower().strip()
        if command_lower.startswith("cd ") or command_lower.startswith("chdir "):
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

        # Clean up the temp file
        try:
            os.remove(temp_file)
        except Exception as e:
            logger.warning(f"Failed to remove temp batch file: {str(e)}")
            
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
        """Execute a command in the Windows session."""
        if not self._initialized:
            raise RuntimeError("Windows session is not initialized")

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
                # Windows doesn't support Bash aliases, so we just ignore this
                command = "echo 'Windows does not support Bash aliases. Git will be used as normal.'"
            elif "git --no-pager" in command:
                # This is typically part of a git configuration command
                # We need to adapt it for Windows
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
        """Clean up the Windows session."""
        # Signal the reader thread to stop
        if self._reader_thread and self._reader_thread.is_alive():
            self._stop_reader.set()
            self._reader_thread.join(timeout=2)
        
        # Close the process
        if self._use_winpty and self.pty:
            try:
                self.pty.close()
            except Exception as e:
                logger.error(f"Error closing ConPTY: {str(e)}")
        elif self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    @property
    def cwd(self):
        return self._cwd 