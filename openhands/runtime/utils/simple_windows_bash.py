import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
import signal
import re # Keep re for later use if needed
from typing import Optional, Dict, Any

from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import (
    CmdOutputMetadata,
    CmdOutputObservation,
)
from openhands.core.logger import openhands_logger as logger # Use actual logger

class SimpleWindowsBashSession:
    """A simplified PowerShell session manager for Windows using a persistent process and temp files for I/O."""
    
    def __init__(self, work_dir: str, username: str | None = None):
        self.work_dir = os.path.abspath(work_dir)
        self.username = username
        self._initialized = False
        self._process = None
        try:
            self._temp_dir = Path(tempfile.mkdtemp())
            # print(f"[DEBUG][INIT] Created temp directory: {self._temp_dir}")
        except Exception as e:
            logger.error(f"[INIT] Failed to create temp directory: {e}", exc_info=True)
            # print(f"[ERROR][INIT] Failed to create temp directory: {e}")
            raise
        self._cwd = self.work_dir
    
    def initialize(self):
        """Initialize the PowerShell session using a simplified approach."""
        logger.info(f"[INIT] Initializing PowerShell session in {self.work_dir}")
        # print(f"[DEBUG][INIT] Initializing PowerShell session in {self.work_dir}")
        
        # Start PowerShell process
        try:
            logger.debug("[INIT] Starting PowerShell process...")
            # print("[DEBUG][INIT] Starting PowerShell process...")
            self._process = subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8', # Specify encoding
                errors='replace',
                cwd=self.work_dir,
                creationflags=subprocess.CREATE_NO_WINDOW # Hide the window
            )
            logger.debug(f"[INIT] PowerShell process started with PID: {self._process.pid}")
            # print(f"[DEBUG][INIT] PowerShell process started with PID: {self._process.pid}")
        except Exception as e:
            logger.error(f"[INIT] Failed to start PowerShell process: {e}", exc_info=True)
            # print(f"[ERROR][INIT] Failed to start PowerShell process: {e}")
            raise RuntimeError(f"Failed to start PowerShell: {e}")
        
        # Change to the working directory
        logger.debug(f"[INIT] Sending Set-Location command: Set-Location '{self.work_dir}'")
        # print(f"[DEBUG][INIT] Sending Set-Location command: Set-Location '{self.work_dir}'")
        try:
            self._send_command(f"Set-Location '{self.work_dir}'")
            time.sleep(0.2) # Allow time for command to process
        except Exception as e:
             logger.error(f"[INIT] Failed during initial Set-Location: {e}", exc_info=True)
             # print(f"[ERROR][INIT] Failed during initial Set-Location: {e}")
             # Still try to continue, but log the error

        # Verify process is running
        if self._process.poll() is not None:
            logger.error(f"[INIT] PowerShell process terminated prematurely with code {self._process.poll()}")
            # print(f"[ERROR][INIT] PowerShell process terminated prematurely with code {self._process.poll()}")
            raise RuntimeError(f"PowerShell process terminated with code {self._process.poll()}")
        
        # Mark as initialized
        self._initialized = True
        logger.info("[INIT] PowerShell session initialized successfully")
        # print("[DEBUG][INIT] PowerShell session initialized successfully")
        
        return True
    
    def _send_command(self, command: str) -> None:
        """Send a command to the PowerShell process."""
        if not self._process or self._process.poll() is not None:
            logger.error("[_send_command] PowerShell process is not running")
            # print("[ERROR][_send_command] PowerShell process is not running")
            raise RuntimeError("PowerShell process is not running")
            
        if not self._process.stdin:
            logger.error("[_send_command] PowerShell stdin is not available")
            # print("[ERROR][_send_command] PowerShell stdin is not available")
            raise RuntimeError("PowerShell stdin is not available")
            
        try:
            command_to_send = f"{command}\n"
            logger.debug(f"[_send_command] Sending command ({len(command_to_send)} bytes): {command[:100]}...")
            # print(f"[DEBUG][_send_command] Sending command ({len(command_to_send)} bytes): {command[:100]}...")
            # Ensure command is encoded correctly
            encoded_command = command_to_send.encode('utf-8')
            # Use underlying buffer write for binary data
            self._process.stdin.buffer.write(encoded_command)
            self._process.stdin.buffer.flush() # Flush the binary buffer
            # Also flush the text wrapper if it exists (belt and suspenders)
            if hasattr(self._process.stdin, 'flush'):
                self._process.stdin.flush()
            logger.debug("[_send_command] Command sent and flushed.")
            # print("[DEBUG][_send_command] Command sent and flushed.")
        except Exception as e:
            logger.error(f"[_send_command] Failed to send command: {e}", exc_info=True)
            # print(f"[ERROR][_send_command] Failed to send command: {e}")
            raise RuntimeError(f"Failed to send command to PowerShell: {e}")
    
    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command in PowerShell using files for reliable I/O."""
        if not self._initialized:
            logger.error("[execute] Session not initialized.")
            # print("[ERROR][execute] Session not initialized.")
            raise RuntimeError("PowerShell session is not initialized")
            
        command = action.command.strip()
        is_input = action.is_input
        timeout = action.timeout or 60.0 # Increased default timeout
        
        logger.info(f"[execute] Command: {command[:100]}{'...' if len(command)>100 else ''}, is_input: {is_input}, timeout: {timeout}s")
        # print(f"[DEBUG][execute] Command: {command}, is_input: {is_input}, timeout: {timeout}s")
        
        # For special keys like Ctrl+C, handle directly
        if command.startswith("C-"):
            logger.debug(f"[execute] Handling special key: {command}")
            # print(f"[DEBUG][execute] Handling special key: {command}")
            if command == "C-c":
                try:
                    logger.debug(f"[execute] Sending CTRL_C_EVENT to PID {self._process.pid}")
                    # print(f"[DEBUG][execute] Sending CTRL_C_EVENT to PID {self._process.pid}")
                    os.kill(self._process.pid, signal.CTRL_C_EVENT)
                    time.sleep(0.1) # Small delay
                    return CmdOutputObservation(
                        content="[Interrupt signal (Ctrl+C) sent to process]",
                        command=command,
                        metadata=CmdOutputMetadata(exit_code=130)
                    )
                except Exception as e:
                    logger.error(f"[execute] Failed to send interrupt: {e}", exc_info=True)
                    # print(f"[ERROR][execute] Failed to send interrupt: {e}")
                    return ErrorObservation(
                        content=f"ERROR: Failed to send interrupt: {str(e)}"
                    )
            logger.warning(f"[execute] Special key {command} not supported.")
            # print(f"[WARN][execute] Special key {command} not supported.")
            return ErrorObservation(
                content=f"ERROR: Special key {command} not supported"
            )
        
        # For empty command or input mode, handle differently
        if command == "" or is_input:
            logger.debug(f"[execute] Handling empty/input command.")
            # print(f"[DEBUG][execute] Handling empty/input command.")
            if is_input:
                try:
                    logger.debug(f"[execute] Sending as input: {command[:100]}...")
                    # print(f"[DEBUG][execute] Sending as input: {command}")
                    self._send_command(command)
                    # Get output right after sending input
                    time.sleep(0.5)  # Brief pause to allow processing
                    stdout_data = self._read_available_output() # Attempt to read potential response
                    logger.debug(f"[execute] Read output after input: {len(stdout_data)} chars")
                    # print(f"[DEBUG][execute] Read output after input: {len(stdout_data)} chars")
                    return CmdOutputObservation(
                        content=stdout_data, # Return any immediate output
                        command=command,
                        metadata=CmdOutputMetadata(exit_code=0, working_dir=self._cwd)
                    )
                except Exception as e:
                    logger.error(f"[execute] Failed to send input: {e}", exc_info=True)
                    # print(f"[ERROR][execute] Failed to send input: {e}")
                    return ErrorObservation(
                        content=f"ERROR: Failed to send input: {str(e)}"
                    )
            else:
                # Empty command - should wait for ongoing process output if any, or return empty if none
                logger.debug("[execute] Received empty command, attempting to read available output...")
                # print("[DEBUG][execute] Reading output for empty command.")
                stdout_data = self._read_available_output() # Check for output from a potentially running command
                logger.debug(f"[execute] Read output for empty command: {len(stdout_data)} chars")
                # print(f"[DEBUG][execute] Read output for empty command: {len(stdout_data)} chars")
                return CmdOutputObservation(
                    content=stdout_data,
                    command=command,
                    metadata=CmdOutputMetadata(exit_code=0, working_dir=self._cwd)
                )
        
        # For normal commands, use file-based approach for reliable output capture
        output_file = None
        error_file = None
        exit_code_file = None
        debug_log_file = None # Keep debug log file for troubleshooting if needed
        try:
            run_uuid = uuid.uuid4()
            # Create unique files for this command
            output_file = self._temp_dir / f"output_{run_uuid}.txt"
            error_file = self._temp_dir / f"error_{run_uuid}.txt"
            exit_code_file = self._temp_dir / f"exitcode_{run_uuid}.txt"
            debug_log_file = self._temp_dir / f"debug_ps_{run_uuid}.log" # PS script's own log
            logger.debug(f"[execute] Temp files: out={output_file}, err={error_file}, exit={exit_code_file}, ps_log={debug_log_file}")
            # print(f"[DEBUG][execute] Temp files: out={output_file}, err={error_file}, exit={exit_code_file}, ps_log={debug_log_file}")

            # Function to append message to the PowerShell debug log (only enable if needed)
            enable_ps_logging = False # Set to True to enable PS script logging
            ps_log_func = ""
            if enable_ps_logging:
                ps_log_func = f"function Write-PSLog {{ param($Message) Add-Content -Path \"{debug_log_file}\" -Value \"($(Get-Date -Format 'HH:mm:ss.fff')) [PS_SCRIPT] $Message\" }}"
            else:
                # Create dummy function if logging is disabled
                ps_log_func = "function Write-PSLog { param($Message) # Logging disabled }"

            # Create a script to run the command and capture output
            wrapped_cmd = f"""
{ps_log_func}

# Write-PSLog "Starting command execution wrapper."

# *** Explicitly set output encoding for this script block ***
$OutputEncoding = [System.Text.Encoding]::UTF8

# Clear previous output variable if it exists
if (Test-Path variable:Global:output) {{ Remove-Variable output -Scope Global -Force }}

# Create empty files first to ensure they exist
# Write-PSLog "Creating temp files..."
$null > '{output_file}'
$null > '{error_file}'
$null > '{exit_code_file}'
# Write-PSLog "Temp files created."

# Run the command and capture output
try {{
    # Write-PSLog "Setting output variable."
    $Global:output = @() # Initialize output variable
    
    # Write-PSLog "Executing command: {command.replace("'", "''")}" # Escape single quotes for logging
    # Run the command
    $cmdOutput = Invoke-Expression -Command @'
{command}
'@ 2>&1
    # Write-PSLog "Command execution finished."
    
    # Save the output
    # Write-PSLog "Saving command output to variable."
    $Global:output = $cmdOutput
    
    # Save to file - explicitly set UTF8 encoding here too
    # Write-PSLog "Writing output to {output_file}"
    $cmdOutput | Out-File -FilePath '{output_file}' -Encoding UTF8 -Force
    # Write-PSLog "Output written to file."
    
    # Save the exit code
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {{ $exitCode = 0 }}
    # Write-PSLog "Saving exit code ($exitCode) to {exit_code_file}"
    $exitCode | Out-File -FilePath '{exit_code_file}' -Encoding UTF8 -Force
    # Write-PSLog "Exit code saved."
    
    # Signal completion
    # Write-PSLog "Writing completion marker to STDOUT."
    # Output completion marker to stdout to signal Python script
    Write-Output "COMMAND_COMPLETE_MARKER_{run_uuid}" 

}} catch {{
    # Write-PSLog "Caught exception during command execution: $($_.Exception.Message)"
    # Save error
    # Write-PSLog "Writing error details to {error_file}"
    $_ | Out-File -FilePath '{error_file}' -Append -Encoding UTF8 -Force
    # Write-PSLog "Error details saved."
    
    # Set exit code to 1 for error
    # Write-PSLog "Saving failure exit code (1) to {exit_code_file}"
    1 | Out-File -FilePath '{exit_code_file}' -Encoding UTF8 -Force
    # Write-PSLog "Failure exit code saved."
    
    # Signal completion even in error case
    # Write-PSLog "Writing error completion marker to STDOUT."
    Write-Output "COMMAND_ERROR_MARKER_{run_uuid}"
}}

# If the command might have changed directory, update the current directory
# Capture potential directory change output separately
$dirChangeOutput = ""
if ('{command.replace("'", "''")}' -match 'cd |Set-Location') {{
    # Write-PSLog "Command might have changed directory, getting current location."
    $dirChangeOutput = "Current directory: $(Get-Location)"
    Write-Output $dirChangeOutput # Write to stdout for Python to potentially capture
}}

# Write-PSLog "Command wrapper script finished."
"""
            
            # Send the command
            logger.debug("[execute] Sending wrapped command to PowerShell...")
            # print("[DEBUG][execute] Sending wrapped command to PowerShell...")
            self._send_command(wrapped_cmd)
            logger.debug("[execute] Wrapped command sent.")
            # print("[DEBUG][execute] Wrapped command sent.")
            
            # Wait for the command to complete by checking exit file or timeout
            start_time = time.time()
            command_complete = False
            completion_marker = f"COMMAND_COMPLETE_MARKER_{run_uuid}"
            error_marker = f"COMMAND_ERROR_MARKER_{run_uuid}"
            stdout_accumulator = "" # Accumulate stdout for marker detection

            logger.debug("[execute] Waiting for completion marker or exit code file...")
            # print("[DEBUG][execute] Waiting for exit code file...")
            # Wait loop
            while time.time() - start_time < timeout:
                # Check for stdout markers first
                stdout_chunk = self._read_available_output()
                if stdout_chunk:
                    stdout_accumulator += stdout_chunk
                    # print(f"[DEBUG][wait] Got stdout chunk: {len(stdout_chunk)} chars. Total: {len(stdout_accumulator)}")
                    if completion_marker in stdout_accumulator or error_marker in stdout_accumulator:
                        logger.debug("[execute] Found completion marker in STDOUT.")
                        # print("[DEBUG][execute] Found completion marker in accumulated STDOUT.")
                        command_complete = True
                        break

                # Check: If exit code file exists and has content
                if exit_code_file.exists():
                    try:
                        if exit_code_file.stat().st_size > 0:
                            logger.debug("[execute] Exit code file exists and has content. Assuming completion.")
                            # print("[DEBUG][execute] Exit code file exists and has content. Assuming completion.")
                            command_complete = True
                            break # Assume command finished if exit code file written
                    except Exception as e:
                         logger.warning(f"[execute] Error checking exit code file: {e}")
                         # print(f"[WARN][execute] Error checking exit code file: {e}")
                         pass # Ignore errors checking file status
                
                # Avoid busy-waiting
                time.sleep(0.1) # Short sleep
            
            # After loop: Read PowerShell debug log if enabled
            if enable_ps_logging and debug_log_file.exists():
                try:
                    ps_debug_log_content = self._read_file_with_encodings(debug_log_file, f"PS debug log {debug_log_file}")
                    logger.debug(f"[execute] PowerShell Script Debug Log ({debug_log_file}):\n------\n{ps_debug_log_content}\n------")
                    # print(f"[DEBUG][execute] PowerShell Script Debug Log ({debug_log_file}):\n------\n{ps_debug_log_content}\n------")
                except Exception as e:
                    logger.warning(f"[execute] Failed to read PS debug log {debug_log_file}: {e}")
                    # print(f"[WARN][execute] Failed to read PS debug log {debug_log_file}: {e}")

            # Read the final output and exit code from files
            logger.debug("[execute] Reading results from output/error/exit files...")
            # print("[DEBUG][execute] Reading results from output/error/exit files...")
            result = ""
            exit_code = 1  # Default to error
            
            # Read output file using helper
            if output_file.exists():
                 result = self._read_file_with_encodings(output_file, f"output file {output_file}")
            else:
                 logger.warning(f"[execute] Output file {output_file} not found.")
                 # print(f"[WARN][execute] Output file {output_file} not found.")
                    
            # Read error file and append to output if it exists
            if error_file.exists():
                try:
                    if error_file.stat().st_size > 0:
                        error_text = self._read_file_with_encodings(error_file, f"error file {error_file}")
                        if error_text and error_text.strip():
                           result += f"\n[ERROR_STREAM] {error_text}"
                except Exception as e:
                     logger.error(f"[execute] Error processing error file {error_file}: {e}", exc_info=True)
                     # print(f"[ERROR][execute] Error processing error file {error_file}: {e}")
                     pass
            else:
                 logger.warning(f"[execute] Error file {error_file} not found.")
                 # print(f"[WARN][execute] Error file {error_file} not found.")
                    
            # Read status file using helper
            if exit_code_file.exists():
                 exit_code_text = self._read_file_with_encodings(exit_code_file, f"exit code file {exit_code_file}").strip()
                 if exit_code_text:
                     logger.debug(f"[execute] Read exit code file ({exit_code_file}): {exit_code_text}")
                     # print(f"[DEBUG][execute] Read exit code file ({exit_code_file}): {exit_code_text}")
                     if exit_code_text.isdigit():
                         exit_code = int(exit_code_text)
                         logger.debug(f"[execute] Parsed exit code: {exit_code}")
                         # print(f"[DEBUG][execute] Parsed exit code: {exit_code}")
                     else:
                         logger.warning(f"[execute] Exit code file content is not a digit: {exit_code_text}")
                         # print(f"[WARN][execute] Exit code file content is not a digit: {exit_code_text}")
                 else:
                     logger.warning(f"[execute] Exit code file {exit_code_file} was empty.")
                     # print(f"[WARN][execute] Exit code file {exit_code_file} was empty.")
            else:
                 logger.warning(f"[execute] Exit code file {exit_code_file} not found.")
                 # print(f"[WARN][execute] Exit code file {exit_code_file} not found.")
            
            # Check if directory changed based on captured STDOUT
            working_dir = self._cwd
            # Check the accumulated stdout for directory change info
            if "Current directory:" in stdout_accumulator: 
                try:
                    dir_marker = "Current directory: "
                    relevant_lines = [line for line in stdout_accumulator.splitlines() if dir_marker in line]
                    if relevant_lines:
                        dir_line = relevant_lines[-1]
                        new_dir = dir_line.split(dir_marker, 1)[1].strip()
                        if new_dir and os.path.isdir(new_dir): # Check validity
                            logger.debug(f"[execute] Detected directory change in STDOUT: {new_dir}")
                            # print(f"[DEBUG][execute] Detected directory change in STDOUT: {new_dir}")
                            working_dir = new_dir
                            self._cwd = new_dir # Update session CWD
                        else:
                            logger.warning(f"[execute] Directory from STDOUT '{new_dir}' invalid, keeping old: {self._cwd}")
                            # print(f"[WARN][execute] Directory from STDOUT '{new_dir}' invalid, keeping old: {self._cwd}")
                except Exception as e:
                    logger.warning(f"[execute] Failed to parse directory from STDOUT: {e}", exc_info=True)
                    # print(f"[WARN][execute] Failed to parse directory from STDOUT: {e}")
            
            # Handle timeout
            if not command_complete:
                logger.warning(f"[execute] Command timed out after {timeout} seconds.")
                # print(f"[WARN][execute] Command timed out after {timeout} seconds.")
                # Read debug log again if enabled
                if enable_ps_logging and debug_log_file.exists():
                    try:
                        ps_debug_log_content_timeout = self._read_file_with_encodings(debug_log_file)
                        if ps_debug_log_content_timeout:
                           logger.debug(f"[execute] PowerShell Script Debug Log (After Timeout Check):\n------\n{ps_debug_log_content_timeout}\n------")
                           # print(f"[DEBUG][execute] PowerShell Script Debug Log (After Timeout Check):\n------\n{ps_debug_log_content_timeout}\n------")
                    except: pass
                return CmdOutputObservation(
                    content=f"Command timed out after {timeout} seconds. Partial output:\n{result}",
                    command=command,
                    metadata=CmdOutputMetadata(
                        exit_code=124,  # Standard timeout exit code
                        working_dir=working_dir,
                        suffix=f"\n[Command timed out after {timeout} seconds]"
                    )
                )
            
            # Return result
            logger.info(f"[execute] Command finished. ExitCode={exit_code}, CWD={working_dir}")
            # print(f"[DEBUG][execute] Command finished. ExitCode={exit_code}, CWD={working_dir}")
            metadata = CmdOutputMetadata(
                exit_code=exit_code,
                working_dir=working_dir,
                suffix=f"\n[Command completed with exit code {exit_code}]"
            )
            
            # Remove completion markers from the actual result content if they were captured
            # This can happen if the command output itself doesn't end with a newline
            clean_result = result.replace(completion_marker, "").replace(error_marker, "")

            return CmdOutputObservation(
                content=clean_result.strip(), # Strip trailing whitespace from file content
                command=command,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"[execute] Unexpected error: {e}", exc_info=True)
            # print(f"[ERROR][execute] Unexpected error: {e}")
            # import traceback
            # traceback.print_exc()
            return ErrorObservation(
                content=f"ERROR executing command: {str(e)}"
            )
        finally:
            # Clean up temp files
            logger.debug(f"[execute] Cleaning up temp files for command: {command[:50]}...")
            # print(f"[DEBUG][execute] Cleaning up temp files for command: {command[:50]}...")
            # Keep the PS debug log if logging was enabled and it exists
            files_to_delete = [output_file, error_file, exit_code_file]
            if not enable_ps_logging:
                files_to_delete.append(debug_log_file)

            for file in files_to_delete:
                if file and file.exists():
                    try:
                        file.unlink()
                        # logger.debug(f"[execute] Deleted {file}")
                        # print(f"[DEBUG][execute] Deleted {file}")
                    except Exception as e:
                        logger.warning(f"[execute] Failed to delete temp file {file}: {e}")
                        # print(f"[WARN][execute] Failed to delete temp file {file}: {e}")
            logger.debug(f"[execute] Finished cleanup.")
            # print(f"[DEBUG][execute] Finished cleanup.")

    
    def _read_available_output(self) -> str:
        """Read available output from the PowerShell process STDOUT non-blockingly."""
        if not self._process or not self._process.stdout:
            # logger.warning("[_read_available_output] Process or stdout not available.")
            # print("[WARN][_read_available_output] Process or stdout not available.")
            return ""
            
        output_chunks = []
        read_start_time = time.monotonic()
        try:
            # Set stdout to non-blocking mode temporarily (Windows specific)
            # stdout_fd = self._process.stdout.fileno()
            # Note: os.set_blocking might not be reliable or necessary if Popen uses pipes correctly.
            # We rely on reading until it would block.
            
            # Read character by character until no more data is immediately available
            read_limit = 16384 # Limit read amount
            bytes_read = 0
            while bytes_read < read_limit:
                try:
                    # Try reading a small chunk non-blockingly
                    # This relies on the underlying pipe behavior
                    chunk = self._process.stdout.read(1) # Read 1 byte/char
                    if chunk:
                        output_chunks.append(chunk)
                        bytes_read += len(chunk.encode('utf-8', errors='ignore')) # Track bytes approx
                    else:
                        # No more data available right now or EOF
                        break
                except (IOError, BlockingIOError):
                    # Expected error when no more data is available non-blockingly
                    break 
                except Exception as read_err:
                    logger.error(f"[_read_available_output] Error during read: {read_err}", exc_info=True)
                    # print(f"[ERROR][_read_available_output] Error during read: {read_err}")
                    break # Stop reading on error
                    
            if bytes_read >= read_limit:
                logger.warning("[_read_available_output] Read limit reached (16KB). Breaking read loop.")
                # print("[WARN][_read_available_output] Read limit reached (16KB). Breaking read loop.")

        except Exception as e:
            logger.error(f"[_read_available_output] Error setting up read: {str(e)}", exc_info=True)
            # print(f"[ERROR][_read_available_output] Error setting up read: {str(e)}")
        
        final_output = "".join(output_chunks)
        # read_duration = time.monotonic() - read_start_time # Can be useful for perf debugging
        # if final_output:
             # logger.debug(f"[_read_available_output] Read {len(final_output)} chars in {read_duration:.4f}s.")
             # print(f"[DEBUG][_read_available_output] Read {len(final_output)} chars in {read_duration:.4f}s.")
        # else: print(f"[DEBUG][_read_available_output] Read 0 chars in {read_duration:.4f}s.") # Too verbose
            
        return final_output
    
    def close(self):
        """Clean up the PowerShell session."""
        logger.info("[close] Closing PowerShell session...")
        # print("[DEBUG][close] Closing PowerShell session...")
        if hasattr(self, '_process') and self._process:
            logger.debug(f"[close] Terminating PowerShell process PID: {self._process.pid}")
            # print(f"[DEBUG][close] Terminating PowerShell process PID: {self._process.pid}")
            try:
                # Try to exit gracefully
                if self._process.stdin and not self._process.stdin.closed:
                    logger.debug("[close] Sending exit command...")
                    # print("[DEBUG][close] Sending exit command...")
                    self._send_command("exit")
                else:
                    logger.debug("[close] Stdin closed, skipping exit command.")
                    # print("[DEBUG][close] Stdin closed, skipping exit command.")
                
                logger.debug("[close] Terminating process...")
                # print("[DEBUG][close] Terminating process...")
                self._process.terminate()
                
                try:
                    logger.debug("[close] Waiting for process termination...")
                    # print("[DEBUG][close] Waiting for process termination...")
                    self._process.wait(timeout=1)
                    logger.debug("[close] Process terminated gracefully.")
                    # print("[DEBUG][close] Process terminated gracefully.")
                except subprocess.TimeoutExpired:
                    logger.warning("[close] Process did not terminate gracefully, killing.")
                    # print("[WARN][close] Process did not terminate gracefully, killing.")
                    self._process.kill()
                    logger.debug("[close] Process killed.")
                    # print("[DEBUG][close] Process killed.")
            except Exception as e:
                logger.error(f"[close] Exception during process termination: {e}", exc_info=True)
                # print(f"[ERROR][close] Exception during process termination: {e}")
                # If already terminated, just pass
                pass
                
            self._process = None
        
        # Clean up temp directory
        if hasattr(self, '_temp_dir') and self._temp_dir and self._temp_dir.exists():
            logger.debug(f"[close] Removing temp directory: {self._temp_dir}")
            # print(f"[DEBUG][close] Removing temp directory: {self._temp_dir}")
            try:
                import shutil
                shutil.rmtree(self._temp_dir)
                logger.debug(f"[close] Removed temp directory {self._temp_dir}")
                # print(f"[DEBUG][close] Removed temp directory {self._temp_dir}")
            except Exception as e:
                logger.error(f"[close] Failed to remove temp directory {self._temp_dir}: {e}", exc_info=True)
                # print(f"[ERROR][close] Failed to remove temp directory {self._temp_dir}: {e}")
                
        self._initialized = False
        logger.info("[close] Session closed.")
        # print("[DEBUG][close] Session closed.")
        
    def __del__(self):
        """Ensure resources are cleaned up."""
        self.close() 
    
    def _read_file_with_encodings(self, file: Path, description: str = "") -> str:
        """Read a file with multiple encodings and return the first successful read."""
        # Prioritize UTF-8 (no BOM), then UTF-8 BOM, then UTF-16, then ASCII
        encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'ascii'] 
        for encoding in encodings:
            try:
                content = file.read_text(encoding=encoding)
                # logger.debug(f"[_read_file_with_encodings] Read {len(content)} chars from {description} using {encoding}")
                # print(f"[DEBUG][_read_file_with_encodings] Read {len(content)} chars from {description} using {encoding}")
                return content
            except UnicodeDecodeError:
                # This encoding failed, try the next one
                # logger.debug(f"[_read_file_with_encodings] Decode failed for {description} with {encoding}. Trying next...")
                # print(f"[DEBUG][_read_file_with_encodings] Decode failed for {description} with {encoding}. Trying next...")
                continue
            except FileNotFoundError:
                logger.warning(f"[_read_file_with_encodings] File not found: {description} at {file}")
                # print(f"[WARN][_read_file_with_encodings] File not found: {description} at {file}")
                return "" # File doesn't exist
            except Exception as e:
                # Other error (e.g., permission denied)
                logger.error(f"[_read_file_with_encodings] Failed to read {description} with {encoding}: {e}", exc_info=True)
                # print(f"[ERROR][_read_file_with_encodings] Failed to read {description} with {encoding}: {e}")
                # Don't try further encodings if a fundamental read error occurred
                return f"[ERROR reading file: {e}]"
                
        # If all decoding attempts fail
        logger.warning(f"[_read_file_with_encodings] All attempted encodings failed for {description}. Reading as bytes.")
        # print(f"[WARN][_read_file_with_encodings] All attempted encodings failed for {description}. Reading as bytes.")
        try:
            # Final fallback: read raw bytes and decode lossily
            raw_bytes = file.read_bytes()
            # Try decoding as utf-8 replacing errors, as it's the most common target
            content = raw_bytes.decode('utf-8', errors='replace')
            logger.debug(f"[_read_file_with_encodings] Read {len(raw_bytes)} bytes from {description} and decoded with replace.")
            # print(f"[DEBUG][_read_file_with_encodings] Read {len(raw_bytes)} bytes from {description} and decoded with replace.")
            return content
        except Exception as e:
             logger.error(f"[_read_file_with_encodings] Failed to read {description} even as raw bytes: {e}", exc_info=True)
             # print(f"[ERROR][_read_file_with_encodings] Failed to read {description} even as raw bytes: {e}")
             return f"[ERROR reading raw bytes: {e}]" 