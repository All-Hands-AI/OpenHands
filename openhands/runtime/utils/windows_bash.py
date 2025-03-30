import os
import re
import time
import traceback
import uuid
from enum import Enum
from typing import Optional
import subprocess
import json
from pathlib import Path
import signal  # Add signal import for Windows signal handling
import tempfile

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import (
    CMD_OUTPUT_PS1_END,
    CmdOutputMetadata,
    CmdOutputObservation,
)
from openhands.utils.shutdown_listener import should_continue


def split_bash_commands(commands):
    if not commands.strip():
        return ['']
    try:
        # For Windows PowerShell, we'll split on semicolons and newlines
        # This is a simplified version since PowerShell has different command separators
        return [cmd.strip() for cmd in commands.split(';') if cmd.strip()]
    except Exception:
        logger.debug(
            f'Failed to parse PowerShell commands\n'
            f'[input]: {commands}\n'
            f'[warning]: {traceback.format_exc()}\n'
            f'The original command will be returned as is.'
        )
        return [commands]


def escape_powershell_special_chars(command: str) -> str:
    """Escapes characters that have special meaning in PowerShell."""
    if command.strip() == '':
        return ''

    # Escape special characters in PowerShell
    special_chars = ['`', '$', '"', "'", ';', '|', '&', '>', '<', '(', ')']
    for char in special_chars:
        command = command.replace(char, f'`{char}')
    return command


class BashCommandStatus(Enum):
    CONTINUE = 'continue'
    COMPLETED = 'completed'
    NO_CHANGE_TIMEOUT = 'no_change_timeout'
    HARD_TIMEOUT = 'hard_timeout'


def _remove_command_prefix(command_output: str, command: str) -> str:
    return command_output.lstrip().removeprefix(command.lstrip()).lstrip()


class WindowsBashSession:
    POLL_INTERVAL = 0.5
    HISTORY_LIMIT = 10_000
    PS1 = CmdOutputMetadata.to_ps1_prompt()
    # Define custom PowerShell prompt markers as class variables
    PS1_BEGIN_MARKER = "###PS1BEGIN###"
    PS1_END_MARKER = "###PS1END###"

    def __init__(
        self,
        work_dir: str,
        username: str | None = None,
        no_change_timeout_seconds: int = 30,
        max_memory_mb: int | None = None,
    ):
        self.NO_CHANGE_TIMEOUT_SECONDS = no_change_timeout_seconds
        self.work_dir = work_dir
        self.username = username
        self._initialized = False
        self.max_memory_mb = max_memory_mb
        self._process: Optional[subprocess.Popen] = None
        self._output_buffer = []
        self._last_output = ""
        self._cwd = os.path.abspath(work_dir)
        self._closed = False

    def initialize(self):
        """Initialize the PowerShell session."""
        # Create a temporary script file for PowerShell initialization
        self._temp_dir = Path(tempfile.mkdtemp())
        self._init_script = self._temp_dir / "init.ps1"
        self._command_script = self._temp_dir / "command.ps1"

        # First find the best PowerShell executable to use
        powershell_exe = "powershell.exe"  # Default
        
        # Try to find PowerShell 7 (pwsh.exe) first, as it's more modern and reliable
        try:
            ps7_check = subprocess.run(
                ["pwsh.exe", "-Command", "echo 'PS7 AVAILABLE'"], 
                capture_output=True, 
                text=True,
                check=False
            )
            if ps7_check.returncode == 0 and "PS7 AVAILABLE" in ps7_check.stdout:
                powershell_exe = "pwsh.exe"
                print(f"[+] PowerShell 7 (pwsh.exe) found and will be used")
                logger.debug(f"PowerShell 7 (pwsh.exe) found and will be used")
            else:
                print(f"[+] PowerShell 7 not found, using standard powershell.exe")
                logger.debug(f"PowerShell 7 not found, using standard powershell.exe")
        except Exception as e:
            print(f"[!] Error checking for PowerShell 7: {e}")
            logger.warning(f"Error checking for PowerShell 7: {e}")

        # First check if PowerShell is available and get its version
        try:
            ps_version_check = subprocess.run(
                [powershell_exe, "-Command", "$PSVersionTable.PSVersion | ConvertTo-Json"], 
                capture_output=True, 
                text=True,
                check=False
            )
            if ps_version_check.returncode == 0 and ps_version_check.stdout:
                print(f"[+] PowerShell version detected: {ps_version_check.stdout.strip()}")
                logger.debug(f"PowerShell version detected: {ps_version_check.stdout.strip()}")
            else:
                print(f"[!] Warning: PowerShell version check failed: {ps_version_check.stderr}")
                logger.warning(f"PowerShell version check failed: {ps_version_check.stderr}")
        except Exception as e:
            print(f"[!] Error checking PowerShell version: {e}")
            logger.error(f"Error checking PowerShell version: {e}")
        
        # Create a PowerShell-compatible PS1 prompt (overriding the default one)
        # This handles the issue where the PS1 prompt from CmdOutputMetadata.to_ps1_prompt() uses Bash syntax
        ps_data = {
            "pid": "$PID",  # PowerShell PID variable
            "exit_code": "$LASTEXITCODE",  # PowerShell last exit code
            "username": "$env:USERNAME",  # PowerShell username 
            "hostname": "$env:COMPUTERNAME",  # PowerShell hostname
            "working_dir": "$(Get-Location)",  # PowerShell equivalent of pwd
            "py_interpreter_path": "$(Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)"  # PowerShell which equivalent
        }
        ps_json = json.dumps(ps_data)
        # Fix: Use PowerShell's here-string format to avoid escaping issues
        ps1_prompt = f"'{self.PS1_BEGIN_MARKER}{ps_json}{self.PS1_END_MARKER}'"
        
        # Store the PS1 prompt for later use
        self._ps1_prompt = ps1_prompt
        
        # Write initialization script with more robust setup and PowerShell-compatible syntax
        init_script_content = f'''
# First line should immediately output a marker to test stdout
Write-Output "POWERSHELL_INIT_START"
[Console]::Out.Flush()  # Explicit flush after each output

$Host.UI.RawUI.FlushInputBuffer()

# PowerShell environment information for debugging
Write-Output "PowerShell Version: $($PSVersionTable.PSVersion)"
[Console]::Out.Flush()
Write-Output "Current Directory: $(Get-Location)"
[Console]::Out.Flush()
Write-Output "Current User: $env:USERNAME"
[Console]::Out.Flush()

# Try changing to the work directory and report any errors
try {{
    Set-Location "{self.work_dir}" -ErrorAction Stop
    Write-Output "Successfully changed directory to: $(Get-Location)"
    [Console]::Out.Flush()
}} catch {{
    Write-Error "Failed to change directory to: {self.work_dir}"
    [Console]::Error.Flush()
    Write-Error $_.Exception.Message
    [Console]::Error.Flush()
}}

# Set up encoding for consistent output
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues["*:Encoding"] = "utf8"
$MaximumHistoryCount = {self.HISTORY_LIMIT}

# Define PS1 prompt using a PowerShell here-string to avoid escaping issues
$ps1Data = @'
{ps_json}
'@
$env:PROMPT = "{self.PS1_BEGIN_MARKER}" + $ps1Data + "{self.PS1_END_MARKER}"

# Explicitly configure error action
$ErrorActionPreference = "Continue"

# Improved function to handle commands with explicit output and flushing
function Process-Command {{
    param($command)
    try {{
        # Announce command start - this helps with debugging
        Write-Output "COMMAND_START: $command" 
        [Console]::Out.Flush()
        
        # Execute the command and capture output
        $output = Invoke-Expression $command 2>&1
        $exitCode = $LASTEXITCODE
        if (-not $exitCode) {{ $exitCode = 0 }}  # Default to 0 if not set
        
        # Output the result with explicit flushing
        if ($output) {{ 
            # Output each line individually with flushing
            foreach ($line in $output) {{
                Write-Output $line
                [Console]::Out.Flush()
            }}
        }} else {{
            # If no output, at least send a marker
            Write-Output "NO_OUTPUT_FROM_COMMAND"
            [Console]::Out.Flush()
        }}
        
        # Explicitly output PS1 prompt with metadata and flush
        Write-Output $env:PROMPT
        [Console]::Out.Flush()
        
        # Additional flush to ensure all output is sent
        [Console]::Out.Flush()
        
        # Return exit code
        return $exitCode
    }} catch {{
        Write-Error "Error executing command: $command"
        [Console]::Error.Flush()
        Write-Error $_.Exception.Message
        [Console]::Error.Flush()
        Write-Output $env:PROMPT
        [Console]::Out.Flush()
        return 1
    }}
}}

# Output initial PS1 prompt with explicit flush to ensure it appears
Write-Output "INIT_COMPLETE"
[Console]::Out.Flush()
Write-Output $env:PROMPT
[Console]::Out.Flush()

# Extra flush to ensure all initialization output is visible
[Console]::Out.Flush()

# Main command processing loop
while ($true) {{
    try {{
        $input = Read-Host
        
        # Debug output
        if ($input -eq "exit") {{ 
            Write-Output "EXIT_COMMAND_RECEIVED"
            [Console]::Out.Flush()
            break 
        }}
        
        $exitCode = Process-Command $input
        $LASTEXITCODE = $exitCode
        [Console]::Out.Flush() # Ensure output is flushed after each command
    }} catch {{
        Write-Error "Error in main loop: $_"
        [Console]::Error.Flush()
        Write-Output $env:PROMPT
        [Console]::Out.Flush()
    }}
}}

Write-Output "POWERSHELL_SESSION_ENDED"
[Console]::Out.Flush()
'''
        # Write the initialization script to the temp file
        self._init_script.write_text(init_script_content)
        
        print(f'[+] Initialization script created at {self._init_script}')
        logger.debug(f'Initialization script created at {self._init_script}')
        
        # Create PowerShell process with more robust settings
        powershell_command = [
            powershell_exe,  # Use the detected PowerShell executable
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-OutputFormat', 'Text',
            '-Command', f"& '{self._init_script}'"  # Use -Command instead of -File
        ]

        if self.username and self.username.lower() in ['root', 'openhands']:
            # For elevated privileges, we'll use Start-Process with RunAs
            powershell_command = [
                powershell_exe,  # Use the detected PowerShell executable
                '-NoProfile',
                '-ExecutionPolicy', 'Bypass',
                '-WindowStyle', 'Hidden',
                '-Command',
                f'Start-Process {powershell_exe} -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -OutputFormat Text -Command & \'{self._init_script}\'"'
            ]

        logger.debug(f'Initializing PowerShell session with command: {powershell_command}')
        print(f'[+] Initializing PowerShell session with command: {powershell_command}')
        
        try: # Added try block for early failure detection
            self._process = subprocess.Popen(
                powershell_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=0,  # No buffering for stdout/stderr
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            print(f'[+] PowerShell process created with PID: {self._process.pid}')
        except Exception as e:
            logger.error(f"Failed to start PowerShell process: {e}", exc_info=True)
            print(f"[!] Failed to start PowerShell process: {e}")
            raise RuntimeError(f"Failed to start PowerShell process: {e}")

        # Check if the process terminated immediately
        time.sleep(0.5) # Give it a moment to potentially fail
        if self._process.poll() is not None:
            exit_code = self._process.poll()
            stderr_output = ""
            try:
                stderr_output = self._process.stderr.read()
            except Exception:
                pass # Ignore errors reading stderr if process died quickly
            error_msg = f"PowerShell process terminated immediately after launch with exit code {exit_code}. Stderr: {stderr_output}"
            logger.error(error_msg)
            print(f"[!] {error_msg}")
            raise RuntimeError(error_msg)

        # Wait specifically for the initial PS1 prompt with more patience
        print('[+] Waiting for initial PowerShell output and PS1 prompt...')
        logger.debug("Waiting for initial PowerShell output and PS1 prompt...")
        initial_output_buffer = ""
        start_wait_time = time.time()
        initial_timeout = 20.0 # Increased timeout to wait for the first prompt
        markers_found = False
        
        print(f'[+] Initial wait timeout set to {initial_timeout}s')
        
        while time.time() - start_wait_time < initial_timeout:
            try:
                # Check process status more frequently in this phase
                if self._process.poll() is not None:
                    error_msg = f"PowerShell process terminated while waiting for initial prompt. Exit code: {self._process.poll()}"
                    print(f"[!] {error_msg}")
                    logger.error(error_msg)
                    # Try to read stderr for diagnostics
                    try:
                        stderr_data = self._process.stderr.read()
                        if stderr_data:
                            print(f"[!] Process stderr: {stderr_data}")
                            logger.error(f"Process stderr: {stderr_data}")
                    except:
                        pass
                    raise RuntimeError(error_msg)

                # Use our improved _get_process_output method with better non-blocking behavior
                chunk = self._get_process_output() 
                if chunk:
                    print(f'[+] Received chunk from PowerShell ({len(chunk)} chars)')
                    initial_output_buffer += chunk
                    
                    # Check for our markers in the output
                    if "POWERSHELL_INIT_START" in initial_output_buffer:
                        print('[+] Found POWERSHELL_INIT_START marker!')
                    
                    if "INIT_COMPLETE" in initial_output_buffer:
                        print('[+] Found INIT_COMPLETE marker!')
                    
                    # Check for PS1 prompt - our primary marker of readiness
                    if self.PS1 in initial_output_buffer:
                        print(f'[+] Found PS1 prompt marker! PowerShell session ready.')
                        logger.debug(f"Initial PS1 prompt received after {time.time() - start_wait_time:.2f} seconds.")
                        markers_found = True
                        break
                    # Add check for our custom PowerShell PS1 prompt format
                    elif self.PS1_BEGIN_MARKER in initial_output_buffer and self.PS1_END_MARKER in initial_output_buffer:
                        print(f'[+] Found custom PowerShell PS1 prompt markers! PowerShell session ready.')
                        logger.debug(f"Custom PS1 prompt received after {time.time() - start_wait_time:.2f} seconds.")
                        markers_found = True
                        break
                else:
                    print('[+] No data received yet, waiting...')
                    logger.debug("Initial read returned empty, PowerShell might still be initializing.")
                    # Try direct stdout read to see if that works better
                    try:
                        if self._process.stdout:
                            # Check if there's data using select-like approach
                            import msvcrt
                            if msvcrt.kbhit():
                                print('[+] Direct stdin data available')
                                # Try to read available data
                                direct_data = self._process.stdout.read(4096)
                                if direct_data:
                                    print(f'[+] Direct read got {len(direct_data)} chars')
                                    initial_output_buffer += direct_data
                    except Exception as direct_err:
                        print(f'[!] Direct read attempt failed: {direct_err}')
                    
                    # Sleep a bit longer between tries
                    time.sleep(1.0)
            except Exception as e:
                print(f'[!] Error waiting for initial PowerShell output: {e}')
                logger.error(f"Error while reading initial PowerShell output: {e}", exc_info=True)
                time.sleep(0.5)  # Brief pause before retrying
        
        # Check if we found our markers
        if not markers_found:
            error_msg = f"Timeout ({initial_timeout}s) waiting for initial PS1 prompt. Output received: {initial_output_buffer!r}"
            print(f'[!] {error_msg}')
            logger.error(error_msg)
            self.close() # Clean up the process
            raise RuntimeError(error_msg)

        # Process seems okay
        print('[+] PowerShell initialization successful!')
        logger.debug("PowerShell initialization successful!")

        # Verify the process is still running
        if self._process.poll() is not None:
            # Try to get any error output
            error_output = ""
            try:
                error_output = self._process.stderr.read() if self._process.stderr else "No error output available"
            except:
                pass
            error_msg = f'PowerShell process terminated unexpectedly after sending initial prompt. Error: {error_output}'
            print(f'[!] {error_msg}')
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Store the last command for interactive input handling
        self.prev_status: BashCommandStatus | None = None
        self.prev_output: str = ''
        self._closed: bool = False
        logger.debug(f'PowerShell session initialized with work dir: {self.work_dir}')
        self._initialized = True
        print(f'[+] PowerShell session fully initialized with working directory: {self.work_dir}')

    def __del__(self):
        """Ensure the session is closed when the object is destroyed."""
        self.close()

    def _send_command(self, command: str) -> None:
        """Send a command to the PowerShell process."""
        if not self._process:
            raise RuntimeError('PowerShell session is not initialized')
        
        try:
            # Check if process is still running
            if self._process.poll() is not None:
                raise RuntimeError('PowerShell process has terminated')
            
            # Log the command we're about to send
            logger.debug(f'Attempting to send command to PowerShell: {command!r}')
            print(f'[+] Attempting to send command to PowerShell: {command!r}')
            
            # Ensure stdin is still open
            if self._process.stdin is None:
                raise RuntimeError('PowerShell stdin pipe is closed')
            
            # Log process state before sending
            logger.debug(f'Process state before send: poll={self._process.poll()}, stdin={self._process.stdin is not None}')
            print(f'[+] Process state before send: poll={self._process.poll()}, stdin={self._process.stdin is not None}')
            
            # Send command directly to PowerShell
            print(f'[+] Writing command to stdin')
            self._process.stdin.write(f"{command}\n")
            print(f'[+] Flushing stdin')
            self._process.stdin.flush()
            logger.debug('Command sent and flushed to stdin')
            print('[+] Command sent and flushed to stdin')
            
            # Try multiple flush approaches for Windows
            try:
                if hasattr(self._process.stdin, 'flush'):
                    self._process.stdin.flush()
                    logger.debug('Secondary stdin.flush() called')
                    print('[+] Secondary stdin.flush() called')
            except Exception as flush_error:
                logger.warning(f'Error during secondary flush: {flush_error}')
                print(f'[!] Error during secondary flush: {flush_error}')
            
            time.sleep(0.3)  # Increased sleep to give PowerShell more time to process
            logger.debug('After sleep, checking process state')
            print('[+] After sleep, checking process state')
            
            # Check process state after sending
            if self._process.poll() is not None:
                logger.error(f'Process terminated after sending command. Exit code: {self._process.poll()}')
                print(f'[!] Process terminated after sending command. Exit code: {self._process.poll()}')
                if self._process.stderr:
                    error_output = self._process.stderr.read()
                    logger.error(f'Process stderr: {error_output}')
                    print(f'[!] Process stderr: {error_output}')
                raise RuntimeError('PowerShell process terminated after sending command')
                
        except (OSError, IOError) as e:
            logger.error(f'Failed to send command to PowerShell: {e}')
            logger.error(f'Process state: poll={self._process.poll()}, stdin={self._process.stdin is not None}')
            print(f'[!] Failed to send command to PowerShell: {e}')
            print(f'[!] Process state: poll={self._process.poll() if self._process else "None"}, stdin={self._process.stdin is not None if self._process else "None"}')
            raise RuntimeError(f'Failed to send command to PowerShell: {e}')

    def _get_process_output(self) -> str:
        """Get the current output from the PowerShell process using subprocess communicate with timeout."""
        if not self._process:
            logger.error("_get_process_output called with no process")
            return ""

        # Simple implementation using a small timeout to read available output
        try:
            # Create a copy of the process that we can use for non-blocking reads
            # This avoids interfering with the main process stdin/stdout
            output = ""
            stderr_output = ""
            
            # Try a simpler approach - poll and read directly from stdout
            # This is more reliable on Windows than non-blocking I/O
            if self._process.stdout:
                # Check if process is still running
                if self._process.poll() is not None:
                    print(f'[!] Process already terminated with code {self._process.poll()}')
                    # Try to read any remaining output
                    try:
                        output = self._process.stdout.read() or ""
                        stderr_output = self._process.stderr.read() if self._process.stderr else ""
                    except Exception as e:
                        print(f'[!] Error reading final output: {e}')
                    return output
                
                # Process is still running, try to read available output
                print('[+] Reading available output from stdout')
                
                # On Windows, don't use select which only works with sockets.
                # Instead, try direct read with msvcrt which is more reliable for Windows
                try:
                    # Try direct read which might work without blocking
                    try:
                        # Make sure stdout is in binary mode for read operations
                        import msvcrt
                        stdout_fd = self._process.stdout.fileno()
                        
                        # Try to peek if data is available using a simple non-blocking read
                        chunk = ""
                        # Read one character at a time to avoid blocking
                        while msvcrt.kbhit():
                            try:
                                char = self._process.stdout.read(1)
                                if char:
                                    chunk += char
                                else:
                                    break  # No more data
                            except Exception as e:
                                print(f'[!] Error reading character: {e}')
                                break
                        
                        if chunk:
                            print(f'[+] Read {len(chunk)} characters from stdout')
                            output += chunk
                        else:
                            print('[+] No data available from msvcrt.kbhit()')
                    except Exception as msvcrt_err:
                        print(f'[!] msvcrt.kbhit() error: {msvcrt_err}')
                        
                        # Fall back to direct read with a short timeout
                        try:
                            # Try a simple read with a timeout by temporarily setting a timeout on the stream
                            import socket
                            original_timeout = self._process.stdout._sock.gettimeout() if hasattr(self._process.stdout, '_sock') else None
                            
                            if hasattr(self._process.stdout, '_sock'):
                                self._process.stdout._sock.settimeout(0.1)  # 100ms timeout
                                
                            try:
                                data = self._process.stdout.read(4096)
                                if data:
                                    print(f'[+] Read {len(data)} bytes with timeout read')
                                    output += data
                            except socket.timeout:
                                print('[+] Timeout on read as expected')
                            finally:
                                # Restore original timeout
                                if hasattr(self._process.stdout, '_sock') and original_timeout is not None:
                                    self._process.stdout._sock.settimeout(original_timeout)
                        except Exception as direct_err:
                            print(f'[!] Direct read error: {direct_err}')
                            
                except Exception as e:
                    print(f'[!] Error during stdout reading: {e}')
                
                # Even if not readable, try direct read which might be buffered
                try:
                    # Create a temporary file to store the current output
                    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
                    temp_path = temp_file.name
                    temp_file.close()
                    
                    # Execute a simple command to dump current output to file
                    dump_cmd = f'Get-Content (Get-Variable -Name output -ValueOnly) > "{temp_path}"'
                    self._process.stdin.write(dump_cmd + "\n")
                    self._process.stdin.flush()
                    time.sleep(0.2)  # Give time for file to be written
                    
                    # Read the dumped output from the file
                    if os.path.exists(temp_path):
                        with open(temp_path, 'r') as f:
                            file_content = f.read()
                            if file_content:
                                print(f'[+] Read {len(file_content)} chars from temp file')
                                output += file_content
                        
                        # Clean up temp file
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                except Exception as dump_err:
                    print(f'[!] Error during output dump: {dump_err}')
            
            return output
            
        except Exception as e:
            logger.error(f"Error in _get_process_output: {e}", exc_info=True)
            print(f'[!] Error in _get_process_output: {e}')
            return ""

    def close(self):
        """Clean up the PowerShell session."""
        if self._closed or not self._process:
            return
        
        try:
            # First try to terminate gracefully
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If terminate doesn't work, try to kill the process
                self._process.kill()
        except Exception as e:
            logger.error(f'Error while closing PowerShell session: {e}')
        finally:
            # Clean up temporary files
            try:
                if hasattr(self, '_temp_dir') and self._temp_dir.exists():
                    import shutil
                    shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.error(f'Error while cleaning up temporary files: {e}')
            
            self._process = None
            self._closed = True

    @property
    def cwd(self):
        return self._cwd

    def _is_special_key(self, command: str) -> bool:
        """Check if the command is a special key."""
        # Special keys are of the form C-<key>
        _command = command.strip()
        return _command.startswith('C-') and len(_command) == 3

    def _clear_screen(self):
        """Clear the PowerShell screen."""
        self._send_command('Clear-Host')
        time.sleep(0.1)

    def _get_command_output(
        self,
        command: str,
        raw_command_output: str,
        metadata: CmdOutputMetadata,
        continue_prefix: str = '',
    ) -> str:
        """Get the command output with the previous command output removed."""
        if self.prev_output:
            command_output = raw_command_output.removeprefix(self.prev_output)
            metadata.prefix = continue_prefix
        else:
            command_output = raw_command_output
        self.prev_output = raw_command_output
        command_output = _remove_command_prefix(command_output, command)
        return command_output.rstrip()

    def _handle_completed_command(
        self, command: str, pane_content: str, ps1_matches: list[re.Match]
    ) -> CmdOutputObservation:
        is_special_key = self._is_special_key(command)
        
        # First, check if we need to handle custom PowerShell prompt
        ps1_begin_marker = self.PS1_BEGIN_MARKER
        ps1_end_marker = self.PS1_END_MARKER
        using_custom_prompt = ps1_begin_marker in pane_content and ps1_end_marker in pane_content
        
        if using_custom_prompt:
            # Extract the last PowerShell PS1 prompt metadata
            last_prompt_start = pane_content.rfind(ps1_begin_marker)
            if last_prompt_start != -1:
                last_prompt_end = pane_content.find(ps1_end_marker, last_prompt_start)
                if last_prompt_end != -1:
                    # Extract the JSON portion
                    ps1_json_str = pane_content[last_prompt_start + len(ps1_begin_marker):last_prompt_end]
                    try:
                        # The JSON string might have PowerShell variables that won't parse as JSON
                        # Replace $PID, $LASTEXITCODE, etc. with placeholder values
                        ps1_json_str = ps1_json_str.replace('$PID', '"0"')
                        ps1_json_str = ps1_json_str.replace('$LASTEXITCODE', '0')
                        ps1_json_str = ps1_json_str.replace('$env:USERNAME', '"user"')
                        ps1_json_str = ps1_json_str.replace('$env:COMPUTERNAME', '"host"')
                        ps1_json_str = ps1_json_str.replace('$(Get-Location)', '"/path"')
                        ps1_json_str = ps1_json_str.replace('$(Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)', '"/path/to/python"')
                        
                        # Clean up any PowerShell formatting artifacts
                        ps1_json_str = ps1_json_str.replace('\"', '"')
                        ps1_json_str = ps1_json_str.replace('\\', '/')
                        
                        print(f"[+] Attempting to parse PS1 JSON: {ps1_json_str}")
                        ps1_data = json.loads(ps1_json_str)
                        print(f"[+] Successfully parsed PS1 data: {ps1_data}")
                        
                        # Create metadata from our custom PS1 data
                        metadata = CmdOutputMetadata()
                        metadata.exit_code = int(str(ps1_data.get("exit_code", 0)).replace('$LASTEXITCODE', '0'))
                        metadata.working_dir = str(ps1_data.get("working_dir", "")).replace('$(Get-Location)', '')
                        # Use these values instead of relying on PS1 match
                        ps1_matches = [1]  # Just need a non-empty list for later assertions
                    except Exception as e:
                        print(f"[!] Error parsing PS1 data: {e}")
                        logger.error(f"Error parsing PS1 data: {e}")
                        # Fall back to default behavior
                        assert len(ps1_matches) >= 1, (
                            f'Expected at least one PS1 metadata block, but got {len(ps1_matches)}.\n'
                            f'---FULL OUTPUT---\n{pane_content!r}\n---END OF OUTPUT---'
                        )
                        metadata = CmdOutputMetadata.from_ps1_match(ps1_matches[-1])
            else:
                # Fall back to default behavior if no metadata found
                assert len(ps1_matches) >= 1, (
                    f'Expected at least one PS1 metadata block, but got {len(ps1_matches)}.\n'
                    f'---FULL OUTPUT---\n{pane_content!r}\n---END OF OUTPUT---'
                )
                metadata = CmdOutputMetadata.from_ps1_match(ps1_matches[-1])
        else:
            # Use the original PS1 match behavior
            assert len(ps1_matches) >= 1, (
                f'Expected at least one PS1 metadata block, but got {len(ps1_matches)}.\n'
                f'---FULL OUTPUT---\n{pane_content!r}\n---END OF OUTPUT---'
            )
            metadata = CmdOutputMetadata.from_ps1_match(ps1_matches[-1])

        # Special case where the previous command output is truncated due to history limit
        get_content_before_last_match = bool(len(ps1_matches) == 1)

        # Update the current working directory if it has changed
        if metadata.working_dir != self._cwd and metadata.working_dir:
            self._cwd = metadata.working_dir

        logger.debug(f'COMMAND OUTPUT: {pane_content}')
        # Extract the command output between the two PS1 prompts
        raw_command_output = self._combine_outputs_between_matches(
            pane_content,
            ps1_matches,
            get_content_before_last_match=get_content_before_last_match,
        )

        if get_content_before_last_match:
            # Count the number of lines in the truncated output
            num_lines = len(raw_command_output.splitlines())
            metadata.prefix = f'[Previous command outputs are truncated. Showing the last {num_lines} lines of the output below.]\n'

        metadata.suffix = (
            f'\n[The command completed with exit code {metadata.exit_code}.]'
            if not is_special_key
            else f'\n[The command completed with exit code {metadata.exit_code}. CTRL+{command[-1].upper()} was sent.]'
        )
        command_output = self._get_command_output(
            command,
            raw_command_output,
            metadata,
        )
        self.prev_status = BashCommandStatus.COMPLETED
        self.prev_output = ''  # Reset previous command output
        self._ready_for_next_command()
        return CmdOutputObservation(
            content=command_output,
            command=command,
            metadata=metadata,
        )

    def _handle_nochange_timeout_command(
        self,
        command: str,
        pane_content: str,
        ps1_matches: list[re.Match],
    ) -> CmdOutputObservation:
        self.prev_status = BashCommandStatus.NO_CHANGE_TIMEOUT
        if len(ps1_matches) != 1:
            logger.warning(
                'Expected exactly one PS1 metadata block BEFORE the execution of a command, '
                f'but got {len(ps1_matches)} PS1 metadata blocks:\n---\n{pane_content!r}\n---'
            )
        raw_command_output = self._combine_outputs_between_matches(
            pane_content, ps1_matches
        )
        metadata = CmdOutputMetadata()  # No metadata available
        metadata.suffix = (
            f'\n[The command has no new output after {self.NO_CHANGE_TIMEOUT_SECONDS} seconds. '
            "You may wait longer to see additional output by sending empty command '', "
            'send other commands to interact with the current process, '
            'or send keys to interrupt/kill the command.]'
        )
        command_output = self._get_command_output(
            command,
            raw_command_output,
            metadata,
            continue_prefix='[Below is the output of the previous command.]\n',
        )
        return CmdOutputObservation(
            content=command_output,
            command=command,
            metadata=metadata,
        )

    def _handle_hard_timeout_command(
        self,
        command: str,
        pane_content: str,
        ps1_matches: list[re.Match],
        timeout: float,
    ) -> CmdOutputObservation:
        self.prev_status = BashCommandStatus.HARD_TIMEOUT
        if len(ps1_matches) != 1:
            logger.warning(
                'Expected exactly one PS1 metadata block BEFORE the execution of a command, '
                f'but got {len(ps1_matches)} PS1 metadata blocks:\n---\n{pane_content!r}\n---'
            )
        raw_command_output = self._combine_outputs_between_matches(
            pane_content, ps1_matches
        )
        metadata = CmdOutputMetadata()  # No metadata available
        metadata.suffix = (
            f'\n[The command timed out after {timeout} seconds. '
            "You may wait longer to see additional output by sending empty command '', "
            'send other commands to interact with the current process, '
            'or send keys to interrupt/kill the command.]'
        )
        command_output = self._get_command_output(
            command,
            raw_command_output,
            metadata,
            continue_prefix='[Below is the output of the previous command.]\n',
        )

        return CmdOutputObservation(
            command=command,
            content=command_output,
            metadata=metadata,
        )

    def _ready_for_next_command(self):
        """Reset the content buffer for a new command."""
        self._clear_screen()

    def _combine_outputs_between_matches(
        self,
        pane_content: str,
        ps1_matches: list[re.Match],
        get_content_before_last_match: bool = False,
    ) -> str:
        """Combine all outputs between PS1 matches."""
        # First, try to handle our custom PowerShell prompt format if present
        ps1_begin_marker = self.PS1_BEGIN_MARKER
        ps1_end_marker = self.PS1_END_MARKER
        
        # If we're using the custom PowerShell format, look for these markers
        if ps1_begin_marker in pane_content and ps1_end_marker in pane_content:
            # Find all occurrences of the custom prompt pattern
            custom_prompts = []
            start_pos = 0
            while True:
                begin_pos = pane_content.find(ps1_begin_marker, start_pos)
                if begin_pos == -1:
                    break
                end_pos = pane_content.find(ps1_end_marker, begin_pos)
                if end_pos == -1:
                    break
                custom_prompts.append((begin_pos, end_pos + len(ps1_end_marker)))
                start_pos = end_pos + len(ps1_end_marker)
            
            # If we found custom prompts, use them instead of the PS1 matches
            if custom_prompts:
                print(f"[+] Using {len(custom_prompts)} custom PowerShell prompts to extract content")
                # Handle similar to regular PS1 matches
                if len(custom_prompts) == 1:
                    if get_content_before_last_match:
                        return pane_content[:custom_prompts[0][0]]
                    else:
                        return pane_content[custom_prompts[0][1]:]
                elif len(custom_prompts) == 0:
                    return pane_content
                
                combined_output = ''
                for i in range(len(custom_prompts) - 1):
                    output_segment = pane_content[
                        custom_prompts[i][1] : custom_prompts[i+1][0]
                    ]
                    combined_output += output_segment + '\n'
                logger.debug(f'COMBINED OUTPUT (custom prompts): {combined_output}')
                return combined_output
        
        # Fall back to the original PS1 match logic
        if len(ps1_matches) == 1:
            if get_content_before_last_match:
                # The command output is the content before the last PS1 prompt
                return pane_content[: ps1_matches[0].start()]
            else:
                # The command output is the content after the last PS1 prompt
                return pane_content[ps1_matches[0].end() + 1 :]
        elif len(ps1_matches) == 0:
            return pane_content
        combined_output = ''
        for i in range(len(ps1_matches) - 1):
            # Extract content between current and next PS1 prompt
            output_segment = pane_content[
                ps1_matches[i].end() + 1 : ps1_matches[i + 1].start()
            ]
            combined_output += output_segment + '\n'
        logger.debug(f'COMBINED OUTPUT (PS1 matches): {combined_output}')
        return combined_output

    def direct_execute(self, command: str, timeout: float = 30.0) -> str:
        """Run a command directly and get its output using a simpler approach."""
        if not self._process or not self._initialized:
            raise RuntimeError('PowerShell session is not initialized')
        
        print(f'[+] Running command directly: {command!r}')
        
        try:
            # For Windows, use a more direct approach to avoid subprocess pipe issues
            # Create a unique temp file to capture command output
            output_file = self._temp_dir / f"output_{uuid.uuid4()}.txt"
            error_file = self._temp_dir / f"error_{uuid.uuid4()}.txt"
            status_file = self._temp_dir / f"status_{uuid.uuid4()}.txt"
            
            # Create PowerShell script with redirected output to files
            wrapped_command = f'''
try {{
    $ErrorActionPreference = "Continue"
    
    # Run the command and redirect stdout/stderr to separate files
    # The $null > ensures the file is created or overwritten before starting command
    $null > "{output_file}"
    $null > "{error_file}"
    
    # Execute command and capture output to file
    $output = Invoke-Expression @'
{command}
'@ 2>&1
    
    # Save output to file
    $output | Out-File -FilePath "{output_file}" -Encoding utf8
    
    # Save exit code
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {{ $exitCode = 0 }}
    $exitCode | Out-File -FilePath "{status_file}" -Encoding utf8
    
    # Signal completion
    Write-Output "COMMAND_COMPLETED"
}} catch {{
    # Save error
    $_ | Out-File -FilePath "{error_file}" -Append -Encoding utf8
    
    # Default to exit code 1 on error
    1 | Out-File -FilePath "{status_file}" -Encoding utf8
    
    # Signal completion even on error
    Write-Output "COMMAND_COMPLETED_WITH_ERROR"
}}
'''
            # Write the wrapped command to a temporary file
            temp_script = self._temp_dir / f"cmd_{uuid.uuid4()}.ps1"
            temp_script.write_text(wrapped_command)
            
            # Execute the script
            self._send_command(f". '{temp_script}'")
            
            # Wait for the command to complete by checking for completion marker in the output
            start_time = time.time()
            exit_code = 1  # Default to error
            command_completed = False
            
            # Wait for command to complete
            while (time.time() - start_time) < timeout and not command_completed:
                # Check if we received completion marker
                current_output = self._get_process_output()
                if "COMMAND_COMPLETED" in current_output or "COMMAND_COMPLETED_WITH_ERROR" in current_output:
                    command_completed = True
                    break
                
                # Check if output file exists and has content (another way to check completion)
                if output_file.exists() and status_file.exists():
                    # Check if status file has content, which indicates completion
                    try:
                        if status_file.stat().st_size > 0:
                            command_completed = True
                            break
                    except:
                        pass
                
                # Small sleep to avoid CPU spinning
                time.sleep(0.2)
                
            # Read output from files
            result = ""
            
            if output_file.exists():
                try:
                    result = output_file.read_text(encoding='utf-8')
                    print(f'[+] Read {len(result)} chars from output file')
                except Exception as read_err:
                    print(f'[!] Error reading output file: {read_err}')
                    result = f"[ERROR] Failed to read command output: {read_err}"
            
            # Add error output if any
            if error_file.exists():
                try:
                    error_content = error_file.read_text(encoding='utf-8')
                    if error_content.strip():
                        print(f'[+] Command produced error output: {len(error_content)} chars')
                        result += f"\n[STDERR] {error_content}"
                except Exception as err_read_err:
                    print(f'[!] Error reading error file: {err_read_err}')
            
            # Get exit code
            if status_file.exists():
                try:
                    exit_code_str = status_file.read_text(encoding='utf-8').strip()
                    if exit_code_str.isdigit():
                        exit_code = int(exit_code_str)
                        print(f'[+] Command exit code: {exit_code}')
                except:
                    print('[!] Failed to read exit code file')
            
            # Add exit code to result
            result += f"\nEXIT_CODE:{exit_code}"
            
            # Clean up temp files
            for file in [output_file, error_file, status_file, temp_script]:
                try:
                    if file.exists():
                        file.unlink()
                except:
                    pass
                
            # If the command didn't complete within timeout, indicate timeout
            if not command_completed:
                return f"[TIMEOUT] Command execution timed out after {timeout} seconds. Partial output follows:\n{result}"
                
            return result
            
        except Exception as e:
            logger.error(f"Error in direct_execute: {e}", exc_info=True)
            print(f'[!] Error in direct_execute: {e}')
            return f"[ERROR] {str(e)}"

    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command in the PowerShell session."""
        if not self._initialized:
            raise RuntimeError('PowerShell session is not initialized')

        # Strip the command of any leading/trailing whitespace
        logger.debug(f'RECEIVED ACTION: {action}')
        print(f'RECEIVED ACTION: {action}')
        command = action.command.strip()
        is_input: bool = action.is_input
        timeout = action.timeout or 60.0  # Default timeout of 60 seconds

        # Check if the command is a single command or multiple commands
        splited_commands = split_bash_commands(command)
        print(f'SPLIT COMMANDS: {splited_commands}')
        if len(splited_commands) > 1:
            return ErrorObservation(
                content=(
                    f'ERROR: Cannot execute multiple commands at once.\n'
                    f'Please run each command separately OR chain them into a single command via && or ;\n'
                    f'Provided commands:\n{"\n".join(f"({i+1}) {cmd}" for i, cmd in enumerate(splited_commands))}'
                )
            )

        # Use our simplified direct execution approach
        try:
            # If it's just an empty command for continuation or a special key, use legacy approach
            if command == '' or self._is_special_key(command) or is_input:
                # Create a simple output for these cases
                metadata = CmdOutputMetadata()
                if self._is_special_key(command):
                    # Handle special keys (like C-c)
                    if command == 'C-c':
                        # Send Ctrl+C to interrupt running process
                        try:
                            # In Windows, Ctrl+C is sent via the CTRL_C_EVENT
                            os.kill(self._process.pid, signal.CTRL_C_EVENT)
                            time.sleep(0.5)  # Give time for the signal to process
                            metadata.exit_code = 130  # Standard exit code for Ctrl+C
                            return CmdOutputObservation(
                                content="[Interrupt signal (Ctrl+C) sent to process]",
                                command=command,
                                metadata=metadata,
                            )
                        except Exception as e:
                            return ErrorObservation(
                                content=f"ERROR: Failed to send interrupt: {str(e)}"
                            )
                    elif command == 'C-d':
                        # Send EOF (Ctrl+D)
                        try:
                            # Send Ctrl+D equivalent
                            self._send_command("\x04")
                            metadata.exit_code = 0
                            return CmdOutputObservation(
                                content="[EOF signal (Ctrl+D) sent to process]",
                                command=command,
                                metadata=metadata,
                            )
                        except Exception as e:
                            return ErrorObservation(
                                content=f"ERROR: Failed to send EOF: {str(e)}"
                            )
                elif command == '':
                    # Empty command just returns current output
                    curr_output = self._get_process_output()
                    metadata.exit_code = 0
                    return CmdOutputObservation(
                        content=curr_output,
                        command=command,
                        metadata=metadata,
                    )
                elif is_input:
                    # Send the input directly to the process
                    try:
                        self._send_command(command)
                        time.sleep(0.5)  # Give time for processing
                        metadata.exit_code = 0
                        return CmdOutputObservation(
                            content=f"[Input sent: {command}]",
                            command=command,
                            metadata=metadata,
                        )
                    except Exception as e:
                        return ErrorObservation(
                            content=f"ERROR: Failed to send input: {str(e)}"
                        )
                
            # For normal commands, use our direct execution approach
            print(f'[+] Using direct execution approach for command: {command}')
            result_output = self.direct_execute(command, timeout=timeout)
            
            # Extract exit code if present
            exit_code = 0
            exit_code_match = re.search(r'EXIT_CODE:(\d+)', result_output)
            if exit_code_match:
                try:
                    exit_code = int(exit_code_match.group(1))
                    # Remove the exit code line from the output
                    result_output = re.sub(r'EXIT_CODE:\d+\s*', '', result_output)
                except:
                    pass
            
            # Create metadata for the output
            metadata = CmdOutputMetadata()
            metadata.exit_code = exit_code
            metadata.working_dir = self._cwd  # Use current working directory
            
            # If the command might change directory, try to detect that
            if 'cd ' in command.lower() or 'set-location' in command.lower():
                try:
                    # Run pwd command to get current directory
                    pwd_result = self.direct_execute('Get-Location', timeout=5.0)
                    if pwd_result and not pwd_result.startswith('[ERROR]') and not pwd_result.startswith('[TIMEOUT]'):
                        # Extract the path (should be first line)
                        pwd_lines = [line for line in pwd_result.splitlines() if line.strip()]
                        if pwd_lines:
                            new_path = pwd_lines[0].strip()
                            if os.path.isabs(new_path):
                                metadata.working_dir = new_path
                                self._cwd = new_path
                except Exception as e:
                    print(f'[!] Error detecting working directory change: {e}')
            
            # Set appropriate metadata for the output
            metadata.suffix = f'\n[The command completed with exit code {metadata.exit_code}.]'
            
            # Create and return the observation
            return CmdOutputObservation(
                content=result_output,
                command=command,
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"Error in execute: {e}", exc_info=True)
            return ErrorObservation(
                content=f"ERROR: Command execution failed: {str(e)}"
            )
