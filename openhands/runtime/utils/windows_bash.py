import os
import subprocess
import tempfile
import uuid
import re
from pathlib import Path
import time
import base64

from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import (
    CmdOutputMetadata,
    CmdOutputObservation,
)

class WindowsBashSession:
    """A direct PowerShell executor for Windows that doesn't maintain a session."""
    
    def __init__(self, work_dir: str, username: str | None = None, no_change_timeout_seconds: int = 30, max_memory_mb: int | None = None):
        self.work_dir = os.path.abspath(work_dir)
        self.username = username
        self._cwd = self.work_dir
        self.no_change_timeout_seconds = no_change_timeout_seconds
        self.max_memory_mb = max_memory_mb
        try:
            self._temp_dir = Path(tempfile.mkdtemp())
            print(f"[DEBUG] Created temp directory: {self._temp_dir}")
        except Exception as e:
            print(f"[ERROR] Failed to create temp directory: {e}")
            raise
        self._initialized = True  # Always initialized since we don't maintain a session
    
    @property
    def cwd(self) -> str:
        """Get the current working directory."""
        return self._cwd
    
    def initialize(self):
        """No initialization needed since we run each command in a new process."""
        print(f"WindowsBashSession ready (work_dir: {self.work_dir})")
        return True
    
    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command using a dedicated PowerShell process."""
        command = action.command.strip()
        timeout = action.timeout or 30.0
        
        print(f"[DEBUG] Executing command: {command} with timeout {timeout}s")
        
        # Recreate temp directory if it was deleted
        if not hasattr(self, '_temp_dir') or not self._temp_dir.exists():
            try:
                self._temp_dir = Path(tempfile.mkdtemp())
                print(f"[DEBUG] Recreated temp directory: {self._temp_dir}")
            except Exception as e:
                print(f"[ERROR] Failed to recreate temp directory: {e}")
                return ErrorObservation(content=f"Failed to recreate temp directory: {e}")
        
        # Handle special cases
        if command.startswith("C-"):
            print("[DEBUG] Detected special key command, not supported.")
            return ErrorObservation(
                content=f"Special keys like {command} are not supported in direct execution mode"
            )
        
        if command == "":
            print("[DEBUG] Detected empty command.")
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
            print(f"[DEBUG] Modified git command for PowerShell: {command}")
        
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
            print(f"[DEBUG] Temp files: script={script_file}, out={output_file}, err={error_file}, status={status_file}")

            # Encode the command using Base64 to avoid PowerShell parsing issues
            print(f"[DEBUG] Encoding command using Base64: {command[:50]}...")
            encoded_command_bytes = command.encode('utf-8')
            base64_encoded_command = base64.b64encode(encoded_command_bytes).decode('utf-8')
            print(f"[DEBUG] Base64 encoded command: {base64_encoded_command[:50]}...")

            # Create PowerShell script to execute the command and write results to files
            script_content = f"""
Write-Host "[PS_SCRIPT] Starting script execution"
# Create empty files first
Write-Host "[PS_SCRIPT] Creating temp files..."
$null > '{output_file}'
$null > '{error_file}'
$null > '{status_file}'
Write-Host "[PS_SCRIPT] Temp files created."

# Save current directory
$originalDir = Get-Location
$originalDirPath = $originalDir.Path
Write-Host "[PS_SCRIPT] Original directory: $originalDirPath"

# Change to working directory
Write-Host "[PS_SCRIPT] Changing to working directory: {self._cwd}"
Set-Location '{self._cwd}'
Write-Host "[PS_SCRIPT] Changed directory."

try {{
    # Log original command for clarity - use escaped version in single quotes
    Write-Host '[PS_SCRIPT] Executing command (Base64 Encoded): {base64_encoded_command[:100]}...'

    # Use the command escaped in Python (single quotes replaced with '')
    $base64Command = '{base64_encoded_command}'
    Write-Host "[PS_SCRIPT] Decoding Base64 command..."
    try {{
        $decodedBytes = [System.Convert]::FromBase64String($base64Command)
        $decodedCommand = [System.Text.Encoding]::UTF8.GetString($decodedBytes)
        Write-Host "[PS_SCRIPT] Decoded command successfully (first 50 chars): $($decodedCommand.Substring(0, [System.Math]::Min(50, $decodedCommand.Length)))..."
    }} catch {{
        Write-Host "[PS_SCRIPT] ERROR decoding Base64 command: $($_.Exception.Message)"
        throw "Failed to decode Base64 command." # Propagate error
    }}

    # Create and execute the script block using the decoded command, capturing all output streams
    Write-Host "[PS_SCRIPT] Creating script block from decoded command..."
    $scriptBlock = [ScriptBlock]::Create($decodedCommand)
    Write-Host "[PS_SCRIPT] Executing script block..."
    $allOutput = & $scriptBlock *>&1
    
    # Separate Error Records and Standard Output
    $errorOutput = $allOutput | Where-Object {{ $_ -is [System.Management.Automation.ErrorRecord] }}
    $standardOutput = $allOutput | Where-Object {{ $_ -isnot [System.Management.Automation.ErrorRecord] }}

    Write-Host "[PS_SCRIPT] Command execution finished."
    
    # Save exit code
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {{ $exitCode = 0 }} # Check if command itself set exit code
    Write-Host "[PS_SCRIPT] Final exit code: $exitCode"
    
    # Write standard output to output file
    Write-Host "[PS_SCRIPT] Writing output to {output_file}"
    $standardOutput | Out-File -FilePath '{output_file}' -Encoding utf8
    Write-Host "[PS_SCRIPT] Output written."
    
    # Write error output to error file if any
    if ($errorOutput) {{
        Write-Host "[PS_SCRIPT] Writing error to {error_file}"
        # Format error records nicely
        $formattedErrors = $errorOutput | ForEach-Object {{ $_.ToString() }}
        $formattedErrors | Out-File -FilePath '{error_file}' -Encoding utf8
        Write-Host "[PS_SCRIPT] Error written."
    }}
    
    # Get current directory (may have changed)
    $newDir = Get-Location
    $newDirPath = $newDir.Path
    Write-Host "[PS_SCRIPT] New directory: $newDirPath"
    
    # Write status information (exit code and current directory)
    Write-Host "[PS_SCRIPT] Writing status to {status_file}"
    "EXIT_CODE=$exitCode`nWORKING_DIR=$newDirPath" | Out-File -FilePath '{status_file}' -Encoding utf8
    Write-Host "[PS_SCRIPT] Status written."
}} catch {{
    Write-Host "[PS_SCRIPT] Caught exception during command execution."
    # Write error details
    Write-Host "[PS_SCRIPT] Writing error to {error_file}"
    # Try to include specific error details
    $errorDetails = $_.ToString()
    if ($_.Exception) {{ $errorDetails += "`nException Message: $($_.Exception.Message)" }}
    if ($_.InvocationInfo) {{ $errorDetails += "`nScript Line Number: $($_.InvocationInfo.ScriptLineNumber)" }}
    $errorDetails | Out-File -FilePath '{error_file}' -Encoding utf8
    Write-Host "[PS_SCRIPT] Error written."
    
    # Write failure status (always exit code 1 in catch block)
    Write-Host "[PS_SCRIPT] Writing failure status to {status_file}"
    "EXIT_CODE=1`nWORKING_DIR=$originalDirPath" | Out-File -FilePath '{status_file}' -Encoding utf8
    Write-Host "[PS_SCRIPT] Failure status written."
}}
Write-Host "[PS_SCRIPT] Script execution complete."
"""
            # Write script to file
            print(f"[DEBUG] Writing PowerShell script to {script_file}")
            script_file.write_text(script_content, encoding='utf-8')
            print(f"[DEBUG] Script written successfully.")
            
            powershell_executable = "powershell.exe"
            # Check if pwsh (PowerShell 7+) exists
            try:
                subprocess.run(["pwsh", "-Command", "exit"], check=True, capture_output=True)
                powershell_executable = "pwsh.exe"
                print("[DEBUG] Using pwsh.exe")
            except FileNotFoundError:
                print("[DEBUG] pwsh.exe not found, using powershell.exe")
            except Exception as e:
                 print(f"[DEBUG] Error checking for pwsh: {e}, using powershell.exe")
            
            # Execute PowerShell script with timeout
            print(f"[DEBUG] Executing script via {powershell_executable}...")
            process = None
            try:
                start_time = time.monotonic()
                process = subprocess.Popen(
                    [powershell_executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_file)],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True, 
                    encoding='utf-8',
                    errors='replace',
                    cwd=self._cwd
                )
                
                # Wait for process to complete with timeout
                stdout_data, stderr_data = process.communicate(timeout=timeout)
                end_time = time.monotonic()
                print(f"[DEBUG] Script process finished in {end_time - start_time:.2f} seconds.")
                print(f"[DEBUG] Script STDOUT:\n{stdout_data}")
                print(f"[DEBUG] Script STDERR:\n{stderr_data}")
                process_exit_code = process.returncode
                print(f"[DEBUG] Script process exit code: {process_exit_code}")

            except subprocess.TimeoutExpired:
                print(f"[ERROR] Script execution timed out after {timeout} seconds.")
                if process:
                    print(f"[DEBUG] Killing process {process.pid}")
                    process.kill()
                    print(f"[DEBUG] Process killed, waiting for completion...")
                    # Add a short timeout to communicate after kill to prevent hangs
                    try:
                        stdout_data, stderr_data = process.communicate(timeout=2) # Timeout after 2 seconds
                        print(f"[DEBUG] Post-kill STDOUT:\n{stdout_data}")
                        print(f"[DEBUG] Post-kill STDERR:\n{stderr_data}")
                    except subprocess.TimeoutExpired:
                        print("[WARN] Timed out waiting for output after killing process. Output might be incomplete.")
                        # Ensure the process is really dead
                        process.kill()
                    except Exception as comm_err:
                        print(f"[WARN] Error during post-kill communicate: {comm_err}")

                # Handle timeout
                # Use captured stdout as content, keep timeout message in metadata
                return CmdOutputObservation(
                    content=stdout_data or "", # Use captured stdout, ensure it's a string
                    command=command,
                    metadata=CmdOutputMetadata(
                        exit_code=-1,
                        working_dir=self._cwd,
                        suffix=f"\\n[Command timed out after {timeout} seconds]"
                    )
                )
            except Exception as run_err:
                 print(f"[ERROR] Failed to run script: {run_err}")
                 return ErrorObservation(content=f"Failed to execute PowerShell script: {run_err}")

            # Process completed, read results from files
            print("[DEBUG] Reading results from files...")
            command_output = ""
            exit_code = 1 # Default to error
            working_dir = self._cwd
            
            # Read output file
            if output_file.exists():
                try:
                    command_output = output_file.read_text(encoding='utf-8')
                    print(f"[DEBUG] Read {len(command_output)} chars from output file.")
                except Exception as e:
                    print(f"[ERROR] Failed to read output file {output_file}: {e}")
                    command_output = f"[Error reading output file: {str(e)}]"
            else:
                 print(f"[WARN] Output file {output_file} not found.")
            
            # Read error file and append to output if it exists
            if error_file.exists():
                try:
                    if error_file.stat().st_size > 0:
                        error_text = error_file.read_text(encoding='utf-8')
                        print(f"[DEBUG] Read {len(error_text)} chars from error file.")
                        if error_text.strip():
                            command_output += f"\n[ERROR_STREAM] {error_text}" # Indicate it came from error stream
                except Exception as e:
                     print(f"[ERROR] Failed to read error file {error_file}: {e}")
                     pass
            else:
                 print(f"[WARN] Error file {error_file} not found.")
            
            # Read status file
            if status_file.exists():
                try:
                    status_text = status_file.read_text(encoding='utf-8')
                    print(f"[DEBUG] Read status file ({status_file}): {status_text.strip()}")
                    
                    # Extract exit code
                    exit_code_match = re.search(r'EXIT_CODE=(\d+)', status_text)
                    if exit_code_match:
                        exit_code = int(exit_code_match.group(1))
                        print(f"[DEBUG] Parsed exit code: {exit_code}")
                    
                    # Extract working directory
                    dir_match = re.search(r'WORKING_DIR=(.*)', status_text)
                    if dir_match:
                        new_dir = dir_match.group(1).strip()
                        if new_dir and os.path.isdir(new_dir): # Check if dir exists and is not empty
                            working_dir = new_dir
                            self._cwd = working_dir  # Update current working directory for next command
                            print(f"[DEBUG] Updated working directory to: {self._cwd}")
                        else:
                            print(f"[WARN] Parsed working directory '{new_dir}' is invalid or empty, keeping old: {self._cwd}")
                except Exception as e:
                     print(f"[ERROR] Failed to read or parse status file {status_file}: {e}")
                     pass
            else:
                 print(f"[WARN] Status file {status_file} not found.")

            # If PowerShell script itself failed (e.g., syntax error), reflect that
            if process_exit_code != 0 and exit_code == 0:
                 print(f"[WARN] Script process exited with {process_exit_code} but command exit code was 0. Overriding to 1.")
                 exit_code = 1 # Indicate failure
                 if stderr_data:
                      command_output += f"\n[POWERSHELL_ERROR] {stderr_data}" # Add PS error

            # Return result
            metadata = CmdOutputMetadata(
                exit_code=exit_code,
                working_dir=working_dir,
                suffix=f"\n[Command completed with exit code {exit_code}]"
            )
            
            print(f"[DEBUG] Returning observation. ExitCode={exit_code}, CWD={working_dir}")
            return CmdOutputObservation(
                content=command_output,
                command=command,
                metadata=metadata
            )
                
        except Exception as e:
            print(f"[ERROR] Unexpected error during command execution: {e}")
            import traceback
            traceback.print_exc()
            return ErrorObservation(
                content=f"ERROR executing command: {str(e)}"
            )
        finally:
            # Clean up files
            print("[DEBUG] Cleaning up temp files...")
            for file in [output_file, error_file, status_file, script_file]:
                if file and file.exists():
                    try:
                        file.unlink()
                        print(f"[DEBUG] Deleted {file}")
                    except Exception as e:
                        print(f"[WARN] Failed to delete temp file {file}: {e}")
    
    def close(self):
        """Clean up resources."""
        print("[DEBUG] Closing WindowsBashSession.")
        # No process to clean up, just remove temp directory
        if hasattr(self, '_temp_dir') and self._temp_dir and self._temp_dir.exists():
            print(f"[DEBUG] Removing temp directory: {self._temp_dir}")
            try:
                import shutil
                shutil.rmtree(self._temp_dir)
                print(f"[DEBUG] Removed temp directory {self._temp_dir}")
            except Exception as e:
                print(f"[ERROR] Failed to remove temp directory {self._temp_dir}: {e}")
        
        self._initialized = False
    
    def __del__(self):
        """Ensure resources are cleaned up."""
        self.close() 