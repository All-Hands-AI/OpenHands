'''
This module provides a Windows-specific implementation for running commands
in a PowerShell session using the pythonnet library to interact with the .NET
PowerShell SDK directly. This aims to provide a more robust and integrated
way to manage PowerShell processes compared to using temporary script files.
'''

import os
import time
import traceback
from pathlib import Path

# Import logger early so it's available in the initialization blocks
from openhands.core.logger import openhands_logger as logger

# Explicitly initialize pythonnet to use CoreCLR
# This should happen before any 'clr' or 'System' usage if possible.
try:
    import pythonnet
    # Attempt to load using the CoreCLR runtime
    # If this fails, pythonnet might already be initialized (e.g., by another module)
    # or CoreCLR might not be properly discoverable despite being installed.
    pythonnet.load("coreclr")
    print("Successfully called pythonnet.load('coreclr')")
    logger.info("Successfully called pythonnet.load('coreclr')")
except Exception as py_net_ex:
    print(f"WARNING: Could not explicitly load pythonnet with 'coreclr'. Error: {py_net_ex}. Proceeding with default initialization...")
    logger.warning(f"Could not explicitly load pythonnet with 'coreclr'. Error: {py_net_ex}. Proceeding with default initialization...")

# Now that pythonnet is initialized, import clr and System
try:
    import clr
    print(f"Imported clr module from: {clr.__file__}")
    # Load System assembly *after* pythonnet is initialized
    clr.AddReference("System")
    import System
    print("Successfully imported System namespace")
    clr_system_load_success = True
except Exception as clr_sys_ex:
    print(f"FATAL: Failed to import clr or System. Error: {clr_sys_ex}")
    logger.critical(f"FATAL: Failed to import clr or System. Error: {clr_sys_ex}")
    logger.critical(traceback.format_exc())
    # Set flags/dummies to prevent downstream errors
    clr_system_load_success = False
    clr = None
    System = None
    PowerShell = None # Ensure dependent types are also None
    # ... (add other dependent types here if needed)

# Attempt to load the PowerShell SDK assembly only if clr and System loaded
ps_sdk_path = None
sdk_load_success = False
if clr_system_load_success:
    try:
        # Prioritize PowerShell 7+ if available (adjust path if necessary)
        pwsh7_path = Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "PowerShell" / "7" / "System.Management.Automation.dll"
        if pwsh7_path.exists():
            ps_sdk_path = str(pwsh7_path)
            clr.AddReference(ps_sdk_path)
            print(f"Loaded PowerShell SDK (Core): {ps_sdk_path}") # Use print for immediate feedback during module load
        else:
            # Fallback to Windows PowerShell 5.1 bundled with Windows
            winps_path = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "System.Management.Automation.dll"
            if winps_path.exists():
                ps_sdk_path = str(winps_path)
                clr.AddReference(ps_sdk_path)
                print(f"Loaded PowerShell SDK (Desktop): {ps_sdk_path}")
            else:
                # Last resort: try loading by assembly name (might work if in GAC or path)
                clr.AddReference("System.Management.Automation")
                print("Attempted to load PowerShell SDK by name (System.Management.Automation)")

        # Import necessary .NET types after adding the reference
        # Let's try importing only PowerShell first to isolate the issue
        from System.Management.Automation import PowerShell
        print("Successfully imported PowerShell type from System.Management.Automation")

        # Now try importing the others that were causing issues
        from System.Management.Automation import PSInvocationState # Needed for state checking
        print("Successfully imported PSInvocationState type from System.Management.Automation")
        # RunspaceInvoke might be deprecated or unnecessary if using RunspaceFactory/PowerShell.Create()
        # from System.Management.Automation import RunspaceInvoke

        from System.Management.Automation.Runspaces import RunspaceFactory # Needed for runspace creation
        print("Successfully imported RunspaceFactory type from System.Management.Automation.Runspaces")

        from System.Management.Automation import PSDataCollection # Import PSDataCollection for BeginInvoke
        
        from System import TimeSpan, Uri # Uri might be needed for some operations
        from System.Collections.ObjectModel import Collection
        from System.Text import Encoding # Though maybe not directly needed here
        sdk_load_success = True

    except Exception as e:
        sdk_load_success = False
        # Log the error and make it clear that the session class will be unusable.
        detailed_error = f"FATAL: Failed to load PowerShell SDK components. Error: {e}. Check pythonnet installation and .NET Runtime compatibility. Path searched: {ps_sdk_path}"
        print(detailed_error) # Use print for immediate visibility
        logger.critical(detailed_error) # Also log as critical
        logger.critical(traceback.format_exc())

        # Define dummy types so the rest of the file parses, but __init__ will fail.
        PowerShell = None
        PSInvocationState = None
        RunspaceFactory = None
        TimeSpan = None
        Collection = None
        # Optionally, raise an ImportError or RuntimeError here to prevent the module from being used further?
        # raise ImportError(detailed_error) # Consider uncommenting if you want immediate failure at import time

# If loading failed at any stage, ensure PowerShell is None for the check in __init__
if not clr_system_load_success or not sdk_load_success:
    PowerShell = None # Explicitly ensure it's None if any exception occurred above

from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import (
    CmdOutputMetadata,
    CmdOutputObservation,
)
from openhands.utils.shutdown_listener import should_continue


class WindowsPowershellSession:
    """
    Manages a persistent PowerShell session using the .NET SDK via pythonnet.

    Allows executing commands within a single runspace, preserving state
    (variables, current directory) between calls.
    Handles basic timeout and captures output/error streams.
    """

    def __init__(self, work_dir: str, username: str | None = None, no_change_timeout_seconds: int = 30, max_memory_mb: int | None = None):
        """
        Initializes the PowerShell session.

        Args:
            work_dir: The starting working directory for the session.
            username: (Currently ignored) Username for execution. PowerShell SDK typically runs as the current user.
            no_change_timeout_seconds: Timeout in seconds if no output change is detected (currently NOT fully implemented).
            max_memory_mb: (Currently ignored) Maximum memory limit for the process.
        """
        # Initialize state flags early to prevent AttributeError in __del__ if init fails
        self._closed = False
        self._initialized = False
        self.runspace = None # Initialize runspace to None

        if PowerShell is None: # Check if SDK loading failed during module import
            # Logged critical error during import, just raise here to prevent instantiation
            raise RuntimeError("PowerShell SDK (System.Management.Automation.dll) could not be loaded. Cannot initialize WindowsPowershellSession.")

        self.work_dir = os.path.abspath(work_dir)
        self.username = username # Note: Impersonation is complex with direct SDK usage.
        self._cwd = self.work_dir
        self.NO_CHANGE_TIMEOUT_SECONDS = no_change_timeout_seconds # Stored, but not fully used yet
        self.max_memory_mb = max_memory_mb # Stored, but not used.

        # Create and open the persistent runspace
        try:
            # Consider InitialSessionState for more control (e.g., execution policy)
            # iss = InitialSessionState.CreateDefault()
            # iss.ExecutionPolicy = Microsoft.PowerShell.ExecutionPolicy.Unrestricted # Requires importing Microsoft.PowerShell namespace
            # self.runspace = RunspaceFactory.CreateRunspace(iss)
            self.runspace = RunspaceFactory.CreateRunspace()
            self.runspace.Open()
            # Set initial working directory within the runspace
            self._set_initial_cwd()
            self._initialized = True # Set to True only on successful initialization
            logger.info(f"PowerShell runspace created. Initial CWD set to: {self._cwd}")
        except Exception as e:
            logger.error(f"Failed to create or open PowerShell runspace: {e}")
            logger.error(traceback.format_exc())
            self.close() # Ensure cleanup if init fails partially
            raise RuntimeError(f"Failed to initialize PowerShell runspace: {e}")

    def _set_initial_cwd(self):
        """Sets the initial working directory in the runspace."""
        ps = None
        try:
            ps = PowerShell.Create()
            ps.Runspace = self.runspace
            ps.AddScript(f'Set-Location -Path "{self._cwd}"').Invoke()
            if ps.Streams.Error:
                 errors = "\n".join([str(err) for err in ps.Streams.Error])
                 logger.warning(f"Error setting initial CWD to '{self._cwd}': {errors}")
                 # Confirm actual CWD if setting failed
                 self._confirm_cwd()
            else:
                logger.debug(f"Successfully set initial runspace CWD to {self._cwd}")
                # Optional: Confirm CWD even on success for robustness
                # self._confirm_cwd()
        except Exception as e:
            logger.error(f"Exception setting initial CWD: {e}")
            logger.error(traceback.format_exc())
            # Attempt to confirm CWD even if setting threw an exception
            self._confirm_cwd()
        finally:
            if ps:
                ps.Dispose()

    def _confirm_cwd(self):
        """Confirms the actual CWD in the runspace and updates self._cwd."""
        ps_confirm = None
        try:
            ps_confirm = PowerShell.Create()
            ps_confirm.Runspace = self.runspace
            ps_confirm.AddScript("Get-Location")
            results = ps_confirm.Invoke()
            if results and results.Count > 0 and hasattr(results[0], 'Path'):
                actual_cwd = str(results[0].Path)
                if os.path.isdir(actual_cwd):
                    if actual_cwd != self._cwd:
                        logger.warning(f"Runspace CWD ({actual_cwd}) differs from expected ({self._cwd}). Updating session CWD.")
                        self._cwd = actual_cwd
                    else:
                        logger.debug(f"Confirmed runspace CWD is {self._cwd}")
                else:
                     logger.error(f"Get-Location returned an invalid path: {actual_cwd}. Session CWD may be inaccurate.")
            elif ps_confirm.Streams.Error:
                 errors = "\n".join([str(err) for err in ps_confirm.Streams.Error])
                 logger.error(f"Error confirming runspace CWD: {errors}")
            else:
                  logger.error("Could not confirm runspace CWD (No result or error).")
        except Exception as e:
            logger.error(f"Exception confirming CWD: {e}")
        finally:
             if ps_confirm:
                  ps_confirm.Dispose()

    @property
    def cwd(self) -> str:
        """Gets the last known working directory of the session."""
        return self._cwd

    def initialize(self):
        """Initialization logic is handled in __init__."""
        # This method might be redundant now but kept for potential API compatibility.
        return self._initialized

    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """
        Executes a command in the persistent PowerShell runspace.

        Args:
            action: The command execution action containing the command string and timeout.

        Returns:
            CmdOutputObservation with results or ErrorObservation on failure.
        """
        if not self._initialized or self._closed:
            return ErrorObservation(content="PowerShell session is not initialized or has been closed.")

        command = action.command.strip()
        # Use provided timeout, default to a reasonable value (e.g., 60 seconds)
        # The original default was NO_CHANGE_TIMEOUT_SECONDS, which is complex here.
        # Let's use a simpler overall timeout for now.
        timeout_seconds = action.timeout or 60 # Default to 60 seconds hard timeout
        timeout_ms = int(timeout_seconds * 1000)

        logger.info(f"Executing command (timeout={timeout_seconds}s): {command}")

        # Handle specific cases similar to the original bash implementation if needed
        if command == "":
             logger.warning("Received empty command string.")
             # Return empty success, mirroring bash.py behavior for empty command
             return CmdOutputObservation(content="", command="", metadata=CmdOutputMetadata(exit_code=0, working_dir=self._cwd))

        if command.startswith("C-"): # e.g., C-c, C-d
            logger.warning(f"Received control character command: {command}. Not directly supported.")
            return ErrorObservation(content=f"Control commands like {command} are not supported in PowerShell SDK mode.")

        ps = None
        output_builder = []
        exit_code = 1 # Default to error exit code
        final_cwd = self._cwd # Start with the current known CWD
        error_message = None
        timed_out = False

        try:
            ps = PowerShell.Create()
            ps.Runspace = self.runspace

            # Add the user's command script
            ps.AddScript(command)
            # IMPORTANT: Add commands to get exit code and CWD *after* the user command
            ps.AddScript("$LASTEXITCODE")
            ps.AddScript("Get-Location")

            # Prepare for asynchronous invocation
            # output_collection = PSDataCollection[System.Management.Automation.PSObject]() # No longer needed here
            async_result = ps.BeginInvoke() # Use overload without output collection argument

            start_time = time.monotonic()

            # Wait loop with timeout and shutdown check
            while not async_result.IsCompleted:
                if not should_continue():
                     logger.warning("Shutdown signal received, attempting to stop PowerShell command.")
                     ps.Stop()
                     # Wait briefly for stop to potentially take effect
                     async_result.AsyncWaitHandle.WaitOne(TimeSpan.FromSeconds(2))
                     error_message = "[Command execution cancelled due to shutdown signal]"
                     # Even if stopped, we need EndInvoke to clean up, so don't break loop here?
                     # Let the loop condition (IsCompleted) handle it after stop.
                     # Break might prevent EndInvoke and proper stream reading.

                # Check hard timeout
                elapsed_seconds = time.monotonic() - start_time
                if elapsed_seconds > timeout_seconds:
                    logger.warning(f"Command execution exceeded timeout ({timeout_seconds}s). Stopping.")
                    ps.Stop()
                    timed_out = True
                    # Wait briefly after stopping before checking completion again or calling EndInvoke
                    async_result.AsyncWaitHandle.WaitOne(TimeSpan.FromSeconds(2))
                    error_message = f"[Command timed out after {timeout_seconds:.1f} seconds and was stopped]"
                    # EndInvoke must still be called even after Stop()
                    # So don't break, let IsCompleted become true.

                # Wait briefly before checking again (e.g., 100ms)
                # WaitOne returns true if the handle is signaled (completed), false if timeout expires
                wait_completed = async_result.AsyncWaitHandle.WaitOne(TimeSpan.FromMilliseconds(100))
                # if wait_completed: break # Exit loop if completed

            # --- Execution Finished (Normally, Timed Out, or Stopped) --- 
            logger.debug(f"Async invocation completed. State: {ps.InvocationStateInfo.State}")

            # Always call EndInvoke to get results and clean up async operation
            # This might block briefly if the command is still somehow running after stop
            # It can also throw exceptions if the command itself had a terminating error.
            results = None
            try:
                 logger.debug("Calling EndInvoke...")
                 results = ps.EndInvoke(async_result)
                 logger.debug("EndInvoke completed.")
            except Exception as end_invoke_ex:
                 # This often indicates a script error or that Stop() was forceful
                 logger.error(f"Error during EndInvoke: {end_invoke_ex}")
                 if not error_message: # Prioritize timeout/cancellation messages
                      error_message = f"[Error during command finalization: {end_invoke_ex}]"
                 # Still try to read streams below

            # Process output streams regardless of EndInvoke success

            # 1. Output Stream (Results from EndInvoke)
            if results is not None and results.Count > 0:
                # Expecting N results + $LASTEXITCODE + Get-Location
                num_actual_results = results.Count - 2
                if num_actual_results < 0: num_actual_results = 0 # Handle case where only exit code/cwd ran

                for i in range(num_actual_results):
                    if results[i] is not None:
                        output_builder.append(str(results[i]))

                # Extract $LASTEXITCODE (second to last result)
                if results.Count >= 2 and results[-2] is not None:
                    try:
                        exit_code = int(str(results[-2]))
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse $LASTEXITCODE as int: {results[-2]}. Assuming error.")
                        exit_code = 1 # Assume error if parsing fails
                else:
                     logger.warning("$LASTEXITCODE was not found in results. Checking streams/state.")
                     # If exit code is missing, assume error if errors occurred or state is Failed
                     if ps.Streams.Error.Count > 0 or ps.InvocationStateInfo.State == PSInvocationState.Failed:
                         exit_code = 1
                     elif timed_out or error_message: # If timed out or cancelled, assume error code
                         exit_code = 1 # Or maybe a specific code for timeout?
                     else:
                         # If no errors, no timeout, command completed, but no $LASTEXITCODE... assume 0? Risky.
                         logger.warning("No $LASTEXITCODE, no errors, no timeout. Assuming exit code 0, but this might be incorrect.")
                         exit_code = 0

                # Extract CWD (last result)
                if results.Count >= 1 and results[results.Count - 1] is not None:
                     try:
                          # Result is often a PathInfo object, get the Path property
                          if hasattr(results[results.Count - 1], 'Path'):
                               final_cwd = str(results[results.Count - 1].Path)
                          else: # Or maybe just a string?
                               final_cwd = str(results[results.Count - 1])

                          # Validate CWD path
                          if os.path.isdir(final_cwd):
                              if final_cwd != self._cwd:
                                  logger.info(f"Working directory changed to: {final_cwd}")
                                  self._cwd = final_cwd # Update session CWD
                              else:
                                  logger.debug(f"Working directory remains: {self._cwd}")
                          else:
                              logger.warning(f"Command returned invalid CWD '{final_cwd}', keeping old CWD: {self._cwd}")
                              final_cwd = self._cwd # Use old CWD for metadata reporting
                     except Exception as cwd_ex:
                          logger.warning(f"Could not parse Get-Location result: {results[results.Count - 1]}, Error: {cwd_ex}. Keeping old CWD.")
                          final_cwd = self._cwd # Use old CWD for metadata reporting
                else:
                     logger.warning("Get-Location result was not found. Keeping old CWD.")
                     final_cwd = self._cwd # Use old CWD if Get-Location failed

            # 2. Error Stream
            if ps.Streams.Error and ps.Streams.Error.Count > 0:
                if output_builder: output_builder.append("\n") # Separator
                output_builder.append("[ERROR STREAM]")
                for err_record in ps.Streams.Error:
                    output_builder.append(str(err_record))
                    # Also log errors prominently
                    logger.error(f"PowerShell Error Record: {err_record}")
                # If errors occurred, ensure exit code is non-zero
                if exit_code == 0:
                    logger.warning("Errors detected in stream, but $LASTEXITCODE was 0. Forcing exit code to 1.")
                    exit_code = 1

            # 3. Other Streams (Optional, add if needed for debugging)
            # Example: Verbose Stream
            # if ps.Streams.Verbose and ps.Streams.Verbose.Count > 0:
            #     if output_builder: output_builder.append("\n")
            #     output_builder.append("[VERBOSE STREAM]")
            #     for record in ps.Streams.Verbose: output_builder.append(str(record))

            # Check final invocation state
            if ps.InvocationStateInfo.State == PSInvocationState.Failed:
                logger.error(f"PowerShell final invocation state is FAILED. Reason: {ps.InvocationStateInfo.Reason}")
                if exit_code == 0: exit_code = 1 # Ensure failure is reported
                if not error_message and ps.InvocationStateInfo.Reason:
                     # Add failure reason if no other message (like timeout) exists
                     error_message = f"[PowerShell invocation failed: {ps.InvocationStateInfo.Reason}]"

            # Combine output and add any timeout/error messages
            final_output = "\n".join(output_builder).strip()
            if error_message:
                 final_output += f"\n{error_message}"

            # Create metadata
            metadata = CmdOutputMetadata(exit_code=exit_code, working_dir=self._cwd)
            suffix = f"\n[Command completed with exit code {exit_code} in CWD: {self._cwd}]"
            if timed_out:
                suffix = f"\n[Command timed out after {timeout_seconds:.1f} seconds and was stopped. Exit code: {exit_code}, CWD: {self._cwd}]"
            elif error_message and "[Command execution cancelled due to shutdown signal]" in error_message:
                 suffix = f"\n[Command execution cancelled due to shutdown signal. Exit code: {exit_code}, CWD: {self._cwd}]"
            metadata.suffix = suffix

            logger.info(f"Command finished. ExitCode={exit_code}, CWD={self._cwd}")
            return CmdOutputObservation(
                content=final_output,
                command=command,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Unhandled exception during PowerShell command execution: {e}")
            logger.error(traceback.format_exc())
            # Try to include partial output if available
            partial_output = "\n".join(output_builder).strip()
            err_content = f"FATAL ERROR executing PowerShell command: {e}\nPartial Output (if any):\n{partial_output}"
            # Return an ErrorObservation, using current CWD state
            return ErrorObservation(content=err_content, error_type="sdk_execution_error")
        finally:
            # Ensure the PowerShell object is disposed to release resources
            if ps:
                try:
                    ps.Dispose()
                except Exception as dispose_ex:
                     logger.error(f"Exception disposing PowerShell object: {dispose_ex}")

    def close(self):
        """Closes the PowerShell runspace and releases resources."""
        if self._closed:
            return

        logger.info("Closing PowerShell session runspace.")
        if hasattr(self, 'runspace') and self.runspace:
            try:
                if self.runspace.RunspaceStateInfo.State == System.Management.Automation.Runspaces.RunspaceState.Opened:
                    self.runspace.Close()
                self.runspace.Dispose()
                logger.info("PowerShell runspace closed and disposed.")
            except Exception as e:
                logger.error(f"Error closing/disposing PowerShell runspace: {e}")
                logger.error(traceback.format_exc())

        self.runspace = None
        self._initialized = False
        self._closed = True

    def __del__(self):
        """Destructor ensures the runspace is closed."""
        self.close()
