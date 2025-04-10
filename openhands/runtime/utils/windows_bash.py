import os
import subprocess
import tempfile
import uuid
import re
import traceback
from pathlib import Path
import time
import base64

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import (
    CmdOutputMetadata,
    CmdOutputObservation,
)
from openhands.utils.shutdown_listener import should_continue

class WindowsBashSession:
    """A direct PowerShell executor for Windows that doesn't maintain a session."""
    
    def __init__(self, work_dir: str, username: str | None = None, no_change_timeout_seconds: int = 30, max_memory_mb: int | None = None):
        self.work_dir = os.path.abspath(work_dir)
        self.username = username
        self._cwd = self.work_dir
        self.NO_CHANGE_TIMEOUT_SECONDS = no_change_timeout_seconds
        self.max_memory_mb = max_memory_mb
        self.prev_status = None
        self.prev_output = ""
        self._closed = False
        try:
            self._temp_dir = Path(tempfile.mkdtemp())
            logger.debug(f"Created temp directory: {self._temp_dir}")
        except Exception as e:
            logger.error(f"Failed to create temp directory: {e}")
            raise
        self._initialized = True  # Always initialized since we don't maintain a session
    
    @property
    def cwd(self) -> str:
        """Get the current working directory."""
        return self._cwd
    
    def initialize(self):
        """No initialization needed since we run each command in a new process."""
        logger.debug(f"WindowsBashSession ready (work_dir: {self.work_dir})")
        return True
    
    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command using a dedicated PowerShell process."""
        command = action.command.strip()
        is_input = action.is_input
        timeout = action.timeout or 30.0
        
        logger.debug(f"Executing command: {command} with timeout {timeout}s")
        
        # Recreate temp directory if it was deleted
        if not hasattr(self, '_temp_dir') or not self._temp_dir.exists():
            try:
                self._temp_dir = Path(tempfile.mkdtemp())
                logger.debug(f"Recreated temp directory: {self._temp_dir}")
            except Exception as e:
                logger.error(f"Failed to recreate temp directory: {e}")
                return ErrorObservation(content=f"Failed to recreate temp directory: {e}")
        
        # Handle special cases
        if command.startswith("C-"):
            logger.debug(f"Detected special key command: {command}")
            return ErrorObservation(
                content=f"Special keys like {command} are not supported in Windows direct execution mode. Please use a different approach."
            )
        
        if command == "":
            logger.debug("Detected empty command.")
            # If no previous command is running, return a message similar to Linux version
            if not self.prev_status:
                return CmdOutputObservation(
                    content="ERROR: No previous running command to retrieve logs from.",
                    command="",
                    metadata=CmdOutputMetadata(),
                )
            return CmdOutputObservation(
                content="",
                command="",
                metadata=CmdOutputMetadata(exit_code=0, working_dir=self._cwd)
            )

        # Handle git configuration command specially
        if "git config" in command and "alias" in command:
            # Convert bash-style git alias to PowerShell function
            command = command.replace(
                'alias git="git --no-pager"',
                'Set-Item -Path Alias:git -Value { git.exe --no-pager $args }'
            )
            logger.debug(f"Modified git command for PowerShell: {command}")
        
        # For normal commands, use file-based approach with a new process
        script_file = None
        output_file = None
        error_file = None
        status_file = None
        stdout_data = ''
        stderr_data = ''
        try:
            # Create unique files for this command
            run_uuid = uuid.uuid4()
            output_file = self._temp_dir / f"output_{run_uuid}.txt"
            error_file = self._temp_dir / f"error_{run_uuid}.txt"
            status_file = self._temp_dir / f"status_{run_uuid}.txt"
            script_file = self._temp_dir / f"script_{run_uuid}.ps1"
            logger.debug(f"Temp files: script={script_file}, out={output_file}, err={error_file}, status={status_file}")

            # Encode the command using Base64 to avoid PowerShell parsing issues
            logger.debug(f"Encoding command using Base64: {command[:50]}...")
            encoded_command_bytes = command.encode('utf-8')
            base64_encoded_command = base64.b64encode(encoded_command_bytes).decode('utf-8')
            logger.debug(f"Base64 encoded command: {base64_encoded_command[:50]}...")

            # Create PowerShell script to execute the command and write results to files
            script_content = f"""
# Create empty files first
$outputFilePath = \'{output_file}\'
$errorFilePath = \'{error_file}\'
$statusFilePath = \'{status_file}\'
$null > $outputFilePath
$null > $errorFilePath
$null > $statusFilePath

# Save current directory
$originalDir = Get-Location
$originalDirPath = $originalDir.Path

# Change to working directory
$targetWorkDir = \'{self._cwd}\'
try {{
    Set-Location $targetWorkDir
}} catch {{
    # Write error to error file and status file, then exit
    $errorDetails = "Failed to change working directory: $($_.Exception.Message)"
    $errorDetails | Out-File -FilePath $errorFilePath -Encoding utf8 -Append
    "EXIT_CODE=1`nWORKING_DIR=$originalDirPath\" | Out-File -FilePath $statusFilePath -Encoding utf8
    exit 1 # Exit the script early
}}

try {{
    $base64Command = \'{base64_encoded_command}\'
    try {{
        $decodedBytes = [System.Convert]::FromBase64String($base64Command)
        $decodedCommand = [System.Text.Encoding]::UTF8.GetString($decodedBytes)
    }} catch {{
        # Write decoding error to error file before throwing
        $errorDetails = "Failed to decode Base64 command: $($_.Exception.Message)"
        $errorDetails | Out-File -FilePath $errorFilePath -Encoding utf8 -Append
        throw "Failed to decode Base64 command." # Propagate error to main catch block
    }}

    # Execute the script block, redirecting ALL output streams (*)
    # and APPENDING (>>) them to the output file AS THEY ARE GENERATED.
    & {{
        Invoke-Command -ScriptBlock ([ScriptBlock]::Create($decodedCommand))
    }} *>> $outputFilePath # Redirect all streams, append to file

    # Get exit code AFTER execution attempt
    $successStatus = $? # True if the last command succeeded, False otherwise
    $exitCode = $LASTEXITCODE
    if ($successStatus -and ($null -eq $exitCode -or $exitCode -eq 0)) {{
        $exitCode = 0
    }} elseif (-not $successStatus) {{
         if ($null -eq $exitCode -or $exitCode -eq 0) {{ $exitCode = 1 }} # If $? is False but exit code is 0/null, force to 1
    }} else {{
         # $? is True, but $LASTEXITCODE is non-zero. Use $LASTEXITCODE.
         # No action needed, $exitCode already holds the value
         : # PowerShell requires something in the block, ':' is a no-op
    }}

    # Output/Error streams were redirected directly.

    # Get current directory (may have changed)
    $newDir = Get-Location
    $newDirPath = $newDir.Path

    # Write status information (exit code and current directory)
    \"EXIT_CODE=$exitCode`nWORKING_DIR=$newDirPath\" | Out-File -FilePath $statusFilePath -Encoding utf8

}} catch {{
    # Write error details to error file
    $errorDetails = $_.ToString()
    if ($_.Exception) {{ $errorDetails += \"`nException Message: $($_.Exception.Message)\" }}
    if ($_.InvocationInfo) {{ $errorDetails += \"`nScript Line Number: $($_.InvocationInfo.ScriptLineNumber)\" }}
    # Append error details to the error file
    $errorDetails | Out-File -FilePath $errorFilePath -Encoding utf8 -Append

    # Write failure status (always exit code 1 in catch block)
    \"EXIT_CODE=1`nWORKING_DIR=$originalDirPath\" | Out-File -FilePath $statusFilePath -Encoding utf8
}} finally {{
    # Script execution finishes here
}}
"""
            # Write script to file
            logger.debug(f"Writing PowerShell script to {script_file}")
            script_file.write_text(script_content, encoding='utf-8')
            
            powershell_executable = "powershell.exe"
            # Check if pwsh (PowerShell 7+) exists
            try:
                subprocess.run(["pwsh", "-Command", "exit"], check=True, capture_output=True)
                powershell_executable = "pwsh.exe"
                logger.debug("Using pwsh.exe")
            except FileNotFoundError:
                logger.debug("pwsh.exe not found, using powershell.exe")
            except Exception as e:
                logger.debug(f"Error checking for pwsh: {e}, using powershell.exe")
            
            # Execute PowerShell script with timeout
            logger.debug(f"Executing script via {powershell_executable}...")
            process = None
            try:
                start_time = time.monotonic()
                last_change_time = start_time
                last_output_size = 0
                process = subprocess.Popen(
                    [powershell_executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_file)],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True, 
                    encoding='utf-8',
                    errors='replace',
                    cwd=self._cwd
                )
                
                # For long-running processes, we need to implement a no-change timeout
                # similar to bash.py's approach
                if action.blocking:
                    # Simple wait for completion if blocking
                    stdout_data, stderr_data = process.communicate(timeout=timeout)
                else:
                    # Poll for output with no-change detection
                    stdout_chunks = []
                    stderr_chunks = []
                    
                    while should_continue() and process.poll() is None:
                        # Check if output file has changed
                        current_output_size = 0
                        if output_file.exists():
                            try:
                                current_output_size = output_file.stat().st_size
                            except Exception:
                                pass  # Ignore file access errors during polling
                                
                        if current_output_size != last_output_size:
                            last_change_time = time.monotonic()
                            last_output_size = current_output_size
                            
                        # Check for no-change timeout
                        time_since_last_change = time.monotonic() - last_change_time
                        if time_since_last_change >= self.NO_CHANGE_TIMEOUT_SECONDS:
                            # Read current output
                            file_output = ""
                            if output_file.exists():
                                try:
                                    file_output = output_file.read_text(encoding='utf-8', errors='replace')
                                except Exception as e:
                                    logger.warning(f"Failed to read output file on no-change timeout: {e}")
                                    file_output = f"[Error reading output file during no-change timeout: {e}]"
                                    
                            # Read error file
                            error_output = ""
                            if error_file.exists() and error_file.stat().st_size > 0:
                                try:
                                    error_output = error_file.read_text(encoding='utf-8', errors='replace')
                                    if error_output.strip():
                                        file_output += f"\n[ERROR_STREAM] {error_output}"
                                except Exception as e:
                                    logger.warning(f"Failed to read error file on no-change timeout: {e}")
                                    
                            # Create metadata with suffix similar to bash.py
                            metadata = CmdOutputMetadata(working_dir=self._cwd)
                            metadata.suffix = (
                                f"\n[The command has no new output after {self.NO_CHANGE_TIMEOUT_SECONDS} seconds. "
                                "Note: On Windows, commands run in isolated processes. "
                                f"You can wait longer to see additional output by sending empty command '', "
                                "or terminate the current process using a new command."
                            )
                            
                            # Set status for tracking
                            self.prev_status = "NO_CHANGE_TIMEOUT"
                            self.prev_output = file_output
                            
                            # Return the observation before completely terminating
                            return CmdOutputObservation(
                                content=file_output,
                                command=command,
                                metadata=metadata
                            )
                            
                        # Check for hard timeout
                        if timeout and time.monotonic() - start_time >= timeout:
                            raise subprocess.TimeoutExpired(process.args, timeout)
                            
                        # Short sleep to prevent CPU spinning
                        time.sleep(0.5)
                        
                    # Process completed or we're breaking out of the loop
                    try:
                        stdout_data, stderr_data = process.communicate(timeout=1)
                    except subprocess.TimeoutExpired:
                        # Last attempt timed out, but we already have partial output
                        process.kill()
                        stdout_data = "".join(stdout_chunks)
                        stderr_data = "".join(stderr_chunks)
                
                end_time = time.monotonic()
                logger.debug(f"Script process finished in {end_time - start_time:.2f} seconds.")
                logger.debug(f"Script STDOUT:\n{stdout_data}")
                logger.debug(f"Script STDERR:\n{stderr_data}")
                process_exit_code = process.returncode
                logger.debug(f"Script process exit code: {process_exit_code}")

            except subprocess.TimeoutExpired:
                logger.error(f"Script execution timed out after {timeout} seconds.")
                stdout_after_kill = ""
                stderr_after_kill = ""
                if process:
                    logger.debug(f"Killing process {process.pid}")
                    # Try to kill the process tree using taskkill first
                    try:
                        kill_result = subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], check=False, capture_output=True, timeout=5)
                        logger.debug(f"Attempted taskkill /T on PID {process.pid}. Result: {kill_result.returncode}, Output: {kill_result.stdout.decode(errors='replace')}, Error: {kill_result.stderr.decode(errors='replace')}")
                        if kill_result.returncode != 0:
                             logger.warning(f"taskkill failed or process {process.pid} not found, falling back to process.kill()")
                             process.kill() # Fallback if taskkill fails
                    except FileNotFoundError:
                         logger.warning("taskkill command not found. Falling back to process.kill()")
                         process.kill() # Fallback if taskkill command doesn't exist
                    except Exception as kill_err:
                        logger.warning(f"Error during taskkill for {process.pid}: {kill_err}. Falling back to process.kill()")
                        process.kill() # Fallback on other errors

                    logger.debug(f"Process killed/terminated, attempting final communication...")
                    try:
                        # Explicitly wait for the process to ensure it's terminated after kill signal
                        logger.debug(f"Waiting briefly for process {process.pid} to terminate...")
                        process.wait(timeout=2) # Wait up to 2 seconds
                        logger.debug(f"Process {process.pid} terminated.")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Process {process.pid} did not terminate quickly after kill signal.")
                    except Exception as wait_err:
                        logger.warning(f"Error waiting for process {process.pid} termination: {wait_err}")

                    try:
                        # Try short communicate to get remaining output/errors
                        stdout_after_kill, stderr_after_kill = process.communicate(timeout=1) # Short timeout
                        logger.debug(f"Post-kill STDOUT:\n{stdout_after_kill}")
                        logger.debug(f"Post-kill STDERR:\n{stderr_after_kill}")
                    except subprocess.TimeoutExpired:
                        logger.warning("Timed out waiting for output after killing process. Output might be incomplete.")
                        # Ensure the process is really dead if communicate times out again
                        try:
                            process.kill()
                        except OSError:
                            pass # Process already dead
                    except Exception as comm_err:
                        logger.warning(f"Error during post-kill communicate: {comm_err}")

                # Combine any potentially captured output
                # Priority to stdout captured post-kill, fallback to empty
                final_output = stdout_after_kill or ""
                if stderr_after_kill: # Append any stderr captured post-kill
                     final_output += f"\n[POST_KILL_STDERR] {stderr_after_kill}"

                # Also read from output and error files, as they contain the direct stream
                file_output = ""
                if output_file and output_file.exists():
                    try:
                        file_output = output_file.read_text(encoding='utf-8', errors='replace')
                        logger.debug(f"Read {len(file_output)} chars from output file ({output_file}) on timeout.")
                    except Exception as e:
                        logger.warning(f"Failed to read output file {output_file} on timeout: {e}")
                        file_output = f"[Error reading output file: {e}]"
                else:
                    logger.debug(f"Output file {output_file} not found on timeout.")

                if error_file and error_file.exists():
                    try:
                        if error_file.stat().st_size > 0:
                            error_text = error_file.read_text(encoding='utf-8', errors='replace')
                            logger.debug(f"Read {len(error_text)} chars from error file ({error_file}) on timeout.")
                            # Append error file content to file_output
                            if error_text.strip():
                                file_output += f"\n[ERROR_FILE_CONTENT] {error_text}"
                    except Exception as e:
                        logger.warning(f"Failed to read error file {error_file} on timeout: {e}")
                        file_output += f"\n[Error reading error file: {e}]"

                # Prepend file content (which has the direct stream) to the final output
                # If file_output is empty, this does nothing
                # If final_output (from communicate) is empty, this uses just file_output
                final_output = file_output + final_output

                # Set status for tracking subsequent commands
                self.prev_status = "HARD_TIMEOUT"
                self.prev_output = final_output

                # Handle timeout - use message format similar to bash.py
                metadata = CmdOutputMetadata(
                    exit_code=-1,
                    working_dir=self._cwd,
                    suffix=(
                        f"\n[The command timed out after {timeout} seconds and was terminated. "
                        "Note: On Windows, unlike Linux, timed-out processes are forcibly terminated. "
                        "The output shown may be incomplete."
                    )
                )
                
                # Return timeout observation with combined captured output
                return CmdOutputObservation(
                    content=final_output, # Use combined file and communicate output
                    command=command,
                    metadata=metadata
                )
            except Exception as run_err:
                 logger.error(f"Failed to run script: {run_err}")
                 logger.error(traceback.format_exc())
                 return ErrorObservation(content=f"Failed to execute PowerShell script: {run_err}")

            # Process completed, read results from files
            logger.debug("Reading results from files...")
            command_output = ""
            exit_code = 1 # Default to error
            working_dir = self._cwd
            
            # Read output file
            if output_file.exists():
                try:
                    command_output = output_file.read_text(encoding='utf-8')
                    logger.debug(f"Read {len(command_output)} chars from output file.")
                except Exception as e:
                    logger.error(f"Failed to read output file {output_file}: {e}")
                    command_output = f"[Error reading output file: {str(e)}]"
            else:
                 logger.warning(f"Output file {output_file} not found.")
            
            # Read error file and append to output if it exists
            if error_file.exists():
                try:
                    if error_file.stat().st_size > 0:
                        error_text = error_file.read_text(encoding='utf-8')
                        logger.debug(f"Read {len(error_text)} chars from error file.")
                        if error_text.strip():
                            command_output += f"\n[ERROR_STREAM] {error_text}" # Indicate it came from error stream
                except Exception as e:
                     logger.error(f"Failed to read error file {error_file}: {e}")
                     pass
            else:
                 logger.warning(f"Error file {error_file} not found.")
            
            # Read status file
            if status_file.exists():
                try:
                    status_text = status_file.read_text(encoding='utf-8')
                    logger.debug(f"Read status file ({status_file}): {status_text.strip()}")
                    
                    # Extract exit code
                    exit_code_match = re.search(r'EXIT_CODE=(\d+)', status_text)
                    if exit_code_match:
                        exit_code = int(exit_code_match.group(1))
                        logger.debug(f"Parsed exit code: {exit_code}")
                    
                    # Extract working directory
                    dir_match = re.search(r'WORKING_DIR=(.*)', status_text)
                    if dir_match:
                        new_dir = dir_match.group(1).strip()
                        if new_dir and os.path.isdir(new_dir): # Check if dir exists and is not empty
                            working_dir = new_dir
                            self._cwd = working_dir  # Update current working directory for next command
                            logger.debug(f"Updated working directory to: {self._cwd}")
                        else:
                            logger.warning(f"Parsed working directory '{new_dir}' is invalid or empty, keeping old: {self._cwd}")
                except Exception as e:
                     logger.error(f"Failed to read or parse status file {status_file}: {e}")
                     pass
            else:
                 logger.warning(f"Status file {status_file} not found.")

            # If PowerShell script itself failed (e.g., syntax error), reflect that
            if process_exit_code != 0 and exit_code == 0:
                 logger.warning(f"Script process exited with {process_exit_code} but command exit code was 0. Overriding to 1.")
                 exit_code = 1 # Indicate failure
                 if stderr_data:
                      command_output += f"\n[POWERSHELL_ERROR] {stderr_data}" # Add PS error

            # Reset tracking variables for completed commands
            self.prev_status = "COMPLETED"
            self.prev_output = ""
                  
            # Return result with metadata suffix format matching bash.py
            metadata = CmdOutputMetadata(
                exit_code=exit_code,
                working_dir=working_dir,
                suffix=f"\n[The command completed with exit code {exit_code}.]"
            )
            
            logger.debug(f"Returning observation. ExitCode={exit_code}, CWD={working_dir}")
            return CmdOutputObservation(
                content=command_output,
                command=command,
                metadata=metadata
            )
                
        except Exception as e:
            logger.error(f"Unexpected error during command execution: {e}")
            logger.error(traceback.format_exc())
            return ErrorObservation(
                content=f"ERROR executing command: {str(e)}"
            )
        finally:
            # Clean up files
            logger.debug("Cleaning up temp files...")
            for file in [output_file, error_file, status_file, script_file]:
                if file and file.exists():
                    try:
                        file.unlink()
                        logger.debug(f"Deleted {file}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file}: {e}")
    
    def close(self):
        """Clean up resources."""
        if self._closed:
            return
            
        logger.debug("Closing WindowsBashSession.")
        # No process to clean up, just remove temp directory
        if hasattr(self, '_temp_dir') and self._temp_dir and self._temp_dir.exists():
            logger.debug(f"Removing temp directory: {self._temp_dir}")
            try:
                import shutil
                shutil.rmtree(self._temp_dir)
                logger.debug(f"Removed temp directory {self._temp_dir}")
            except Exception as e:
                logger.error(f"Failed to remove temp directory {self._temp_dir}: {e}")
        
        self._initialized = False
        self._closed = True
    
    def __del__(self):
        """Ensure resources are cleaned up."""
        self.close() 