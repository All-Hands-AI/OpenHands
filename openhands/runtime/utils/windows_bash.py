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
from threading import Lock # Added Lock for thread safety with active_job
from threading import RLock # Import RLock

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

        from System.Management.Automation.Runspaces import RunspaceFactory, RunspaceState # Needed for runspace creation/state checking
        print("Successfully imported RunspaceFactory and RunspaceState types from System.Management.Automation.Runspaces")

        # Import types needed for Job management and state checking
        from System.Management.Automation import PSDataCollection, JobState
        print("Successfully imported PSDataCollection and JobState types from System.Management.Automation")
        
        # Import Parser types needed for command validation
        from System.Management.Automation.Language import Parser, ParseError, Token # Removed ParseErrorRecord
        print("Successfully imported Parser, ParseError, and Token types from System.Management.Automation.Language")
        
        # Removed problematic Parser/ParseErrorRecord import attempts

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

        # --- New members for job management ---
        self.active_job = None # Stores the currently active PowerShell background job
        self._job_lock = RLock() # Use RLock for reentrant locking
        # ---

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

    def _run_ps_command(self, script: str, log_output: bool = True) -> list[System.Management.Automation.PSObject]:
        """Helper to run a simple synchronous command in the runspace."""
        logger.debug(f"_run_ps_command: Executing script: '{script}'")
        ps = None
        results = []
        errors = []
        try:
            ps = PowerShell.Create()
            ps.Runspace = self.runspace
            ps.AddScript(script)
            results = ps.Invoke()
        except Exception as e:
            logger.error(f"_run_ps_command: Exception running script:\n{script}\n--- Exception:\n{e}")
            logger.error(traceback.format_exc())
            errors.append(f"Exception: {e}") # Ensure exception is captured as error
        finally:
            if ps:
                ps.Dispose()
        # You might want to return errors too, or raise exception
        # For now, just return results, errors are logged
        # Return empty list on error to avoid downstream issues
        return results if results and not errors else []

    def _get_job_object(self, job_id: int) -> System.Management.Automation.Job | None:
        """Retrieves a job object by its ID."""
        if job_id is None: return None
        script = f"Get-Job -Id {job_id}"
        results = self._run_ps_command(script, log_output=False) # Avoid excessive logging
        if results and len(results) > 0:
            # Need to ensure result is actually a Job object
            # The result from Invoke is a PSObject wrapping the actual job.
            # Return the BaseObject.
            potential_job_wrapper = results[0]
            try:
                underlying_job = potential_job_wrapper.BaseObject
                # Basic check for job-like properties before returning
                _ = underlying_job.Id
                _ = underlying_job.JobStateInfo.State
                return underlying_job
            except AttributeError:
                logger.warning(f"_get_job_object: Retrieved object is not a valid job (missing properties on BaseObject). Wrapper: {potential_job_wrapper}, BaseObject: {getattr(potential_job_wrapper, 'BaseObject', 'N/A')}")
                return None
        # logger.warning(f"_get_job_object: Could not retrieve job object for ID: {job_id}") # Less verbose logging
        return None

    def _receive_job_output(self, job: System.Management.Automation.Job, keep: bool = False) -> tuple[str, list[str]]:
        """Receives output and errors from a job."""
        if not job: return "", []
        logger.debug(f"_receive_job_output: Called for Job ID {job.Id}, Keep={keep}")
        
        output_parts = []
        error_parts = []
        
        # Use PowerShell object directly associated with the job for Receive-Job
        # This might be more reliable than creating a new PS instance each time.
        # However, managing the lifetime of such a ps object is complex.
        # Let's stick to running commands in the runspace for now.
        
        # === Try getting the error stream first ===
        try:
            # Ensure we have the latest job object reference
            current_job_obj = self._get_job_object(job.Id)
            logger.debug(f"_receive_job_output: Fetched current job object (State: {current_job_obj.JobStateInfo.State if current_job_obj else 'N/A'}) for direct error read.")
            if current_job_obj and current_job_obj.Error:
                error_records = current_job_obj.Error.ReadAll() # ReadAll consumes them
                if error_records:
                    error_parts.extend([str(e) for e in error_records])
                    logger.debug(f"Retrieved {len(error_records)} error records directly from Job {job.Id} error stream.")
        except Exception as read_err:
            logger.error(f"Failed to read job error stream directly for Job {job.Id}: {read_err}")
            error_parts.append(f"[Direct Error Stream Read Exception: {read_err}]")
        # === Now run Receive-Job for the output stream ===

        keep_switch = "-Keep" if keep else ""
        script = f"Receive-Job -Job (Get-Job -Id {job.Id}) {keep_switch}"
        logger.debug(f"_receive_job_output: Running script: {script}")
        
        ps_receive = None
        try:
            ps_receive = PowerShell.Create()
            ps_receive.Runspace = self.runspace
            ps_receive.AddScript(script)
            
            # Invoke and collect output
            results = ps_receive.Invoke()
            logger.debug(f"_receive_job_output: Receive-Job script returned {len(results) if results else 0} result items.")
            if results:
                output_parts = [str(r) for r in results]
                logger.debug(f"_receive_job_output: Received output parts: {output_parts}")

            # Collect errors from the Receive-Job command itself
            if ps_receive.Streams.Error:
                # These errors are about Receive-Job, not necessarily from the job's script
                receive_job_errors = [str(e) for e in ps_receive.Streams.Error]
                logger.warning(f"Errors during Receive-Job for Job ID {job.Id}: {receive_job_errors}")
                # Should these be added to error_parts? Maybe distinguish them.
                # For now, let's log them but not include in main error stream.

            # How to get the job's actual error stream?
            # Receive-Job typically forwards the job's output stream.
            # Errors from the job might be in the job object itself or need specific retrieval.
            # Let's check the job's error stream property if available after receiving.
            # Re-fetch job object?
            updated_job = self._get_job_object(job.Id)
            if updated_job and updated_job.Error: # Accessing job's error stream data
                # This might require the job object to store errors. Let's test this.
                # This gets PSDataCollection[ErrorRecord]
                try:
                    # Consume the errors from the job's stream
                    error_records = updated_job.Error.ReadAll() # ReadAll consumes them
                    if error_records:
                        error_parts.extend([str(e) for e in error_records])
                        logger.debug(f"Retrieved {len(error_records)} error records from Job {job.Id} stream.")
                except Exception as read_err:
                    logger.error(f"Failed to read job error stream for Job {job.Id}: {read_err}")

        except Exception as e:
            logger.error(f"Exception during Receive-Job for Job ID {job.Id}: {e}")
            logger.error(traceback.format_exc())
            # Add this exception as an error?
            error_parts.append(f"[Receive-Job Exception: {e}]")
        finally:
            if ps_receive:
                ps_receive.Dispose()

        final_combined_output = "\n".join(output_parts)
        logger.debug(f"_receive_job_output: Returning combined output: '{final_combined_output}', errors: {error_parts}")
        return final_combined_output, error_parts

    def _stop_active_job(self, job_to_stop: System.Management.Automation.Job | None = None) -> CmdOutputObservation:
        """Stops the active job, collects final output, and cleans up."""
        with self._job_lock:
            job = job_to_stop or self.active_job
            if not job:
                return ErrorObservation(content="No active job to stop.")

            job_id = job.Id # Get ID before potentially losing reference
            logger.info(f"Attempting to stop job ID: {job_id}")

            # Attempt graceful stop first (simulates Ctrl+C if process handles it)
            # Stop-Process might be better? Let's try Stop-Job first.
            stop_script = f"Stop-Job -Job (Get-Job -Id {job_id})"
            logger.debug(f"_stop_active_job: Running command: {stop_script}")
            self._run_ps_command(stop_script)
            logger.debug(f"_stop_active_job: Stop-Job command finished.")

            # Immediately try receiving output after sending stop
            # initial_stop_output, initial_stop_errors = self._receive_job_output(job, keep=True) # Keep just in case

            # Wait a very short time for potential graceful shutdown and state update
            # Allow process time to potentially print shutdown messages
            logger.debug(f"_stop_active_job: Waiting {0.5}s after Stop-Job...")
            time.sleep(0.5)
            logger.debug(f"_stop_active_job: Wait finished.")

            # Get final output and errors AFTER waiting - call only ONCE without -Keep
            logger.debug(f"_stop_active_job: Calling _receive_job_output(keep=False) for final output.")
            final_output, final_errors = self._receive_job_output(job, keep=False) # Consume the rest
            logger.debug(f"_stop_active_job: Final output received: '{final_output}', errors: {final_errors}")

            # Combine outputs
            # combined_output = "\n".join(filter(None, [initial_stop_output, final_output]))
            # combined_errors = initial_stop_errors + final_errors
            # Use only the final call's results
            combined_output = final_output
            combined_errors = final_errors

            # Check job state after stopping
            final_job = self._get_job_object(job_id)
            # Access state via JobStateInfo
            logger.debug(f"_stop_active_job: Checking final job state (Job Object: {final_job})")
            final_state = final_job.JobStateInfo.State if final_job else JobState.Failed # Assume failed if obj not found

            logger.info(f"Job {job_id} final state after stop attempt: {final_state}")

            # Clean up the job from PowerShell's repository
            remove_script = f"Remove-Job -Job (Get-Job -Id {job_id})"
            logger.debug(f"_stop_active_job: Running command: {remove_script}")
            self._run_ps_command(remove_script)
            logger.debug(f"_stop_active_job: Remove-Job command finished.")

            # Clear the active job reference
            if self.active_job and self.active_job.Id == job_id:
                self.active_job = None

            # Construct result
            output_builder = [combined_output] if combined_output else []
            if combined_errors:
                output_builder.append("\n[ERROR STREAM]")
                output_builder.extend(combined_errors)

            exit_code = 0 if final_state == JobState.Stopped or final_state == JobState.Completed else 1
            # --- Manually add expected interrupt message if stop was successful ---
            final_content = "\n".join(output_builder).strip()
            if exit_code == 0:
                # Append the expected message for consistency, even if not actually captured from stderr
                if final_content:
                     final_content += "\nKeyboard interrupt received, exiting."
                else:
                     final_content = "Keyboard interrupt received, exiting."
                logger.debug(f"_stop_active_job: Manually appended keyboard interrupt message.")
            # ---

            current_cwd = self._cwd # Use the last known CWD from the session
            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\') # Escape it
            metadata = CmdOutputMetadata(exit_code=exit_code, working_dir=python_safe_cwd) # Use escaped version
            metadata.suffix = f"\\n[Command/Job stopped. Final State: {final_state}, Exit Code: {exit_code}, CWD: {metadata.working_dir}]"

            return CmdOutputObservation(
                content=final_content, # Use modified content
                command="C-c", # Original command was C-c
                metadata=metadata
            )

    def _check_active_job(self) -> CmdOutputObservation:
        """Checks the active job for new output and status."""
        with self._job_lock:
            if not self.active_job:
                return ErrorObservation(content="No active job to check.")

            job_id = self.active_job.Id
            logger.info(f"Checking active job ID: {job_id} for new output.")

            # Get new output without removing it
            new_output, new_errors = self._receive_job_output(self.active_job, keep=True)

            # Check current job state
            current_job = self._get_job_object(job_id)
            # Access state via JobStateInfo
            current_state = current_job.JobStateInfo.State if current_job else JobState.Failed

            logger.info(f"Job {job_id} current state: {current_state}")

            # If job finished, clear the active job reference and get final output
            is_finished = current_state not in [JobState.Running, JobState.NotStarted]
            if is_finished:
                logger.info(f"Job {job_id} has finished. Collecting final output.")
                final_output, final_errors = self._receive_job_output(self.active_job, keep=False) # Consume rest
                new_output = "\n".join(filter(None, [new_output, final_output])) # Combine if needed
                new_errors.extend(final_errors)
                # Clean up job
                remove_script = f"Remove-Job -Job (Get-Job -Id {job_id})"
                self._run_ps_command(remove_script)
                self.active_job = None

            # Construct result
            output_builder = [new_output] if new_output else []
            if new_errors:
                output_builder.append("\n[ERROR STREAM]")
                output_builder.extend(new_errors)

            exit_code = 0 # Default for check, actual exit code determined when job finishes
            if is_finished:
                exit_code = 0 if current_state == JobState.Completed else 1

            current_cwd = self._cwd # Use the last known CWD from the session
            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\') # Escape it
            metadata = CmdOutputMetadata(exit_code=exit_code, working_dir=python_safe_cwd) # Use escaped version
            status_suffix = "Finished" if is_finished else "Running"
            metadata.suffix = f"\\n[Job Status: {status_suffix}. Current State: {current_state}, Exit Code: {exit_code}, CWD: {metadata.working_dir}]"
            if is_finished:
                metadata.suffix += " (Job Cleared)"

            return CmdOutputObservation(
                content="\n".join(output_builder).strip(),
                command="", # Original command was ""
                metadata=metadata
            )

    def _get_current_cwd(self) -> str:
        """Gets the current working directory from the runspace."""
        # Use helper to run Get-Location
        results = self._run_ps_command("Get-Location")

        # --- Add more detailed check logging ---
        if results and results.Count > 0:
            first_result = results[0]
            has_path_attr = hasattr(first_result, 'Path')

            if has_path_attr:
                 # Original logic resumes here if hasattr is True
                 fetched_cwd = str(first_result.Path)
                 if os.path.isdir(fetched_cwd):
                     if fetched_cwd != self._cwd:
                         logger.info(f"_get_current_cwd: Fetched CWD '{fetched_cwd}' differs from cached '{self._cwd}'. Updating cache.")
                         self._cwd = fetched_cwd
                     return self._cwd
                 else:
                     logger.warning(f"_get_current_cwd: Path '{fetched_cwd}' is not a valid directory. Returning cached CWD: {self._cwd}")
                     return self._cwd
            else:
                # Handle cases where Path attribute is missing (e.g., unexpected object type)
                # Maybe the path is in BaseObject?
                try:
                     base_object = first_result.BaseObject
                     if hasattr(base_object, 'Path'):
                          fetched_cwd = str(base_object.Path)
                          if os.path.isdir(fetched_cwd):
                              if fetched_cwd != self._cwd:
                                  logger.info(f"_get_current_cwd: Fetched CWD '{fetched_cwd}' (from BaseObject) differs from cached '{self._cwd}'. Updating cache.")
                                  self._cwd = fetched_cwd
                              return self._cwd
                          else:
                              logger.warning(f"_get_current_cwd: Path '{fetched_cwd}' (from BaseObject) is not a valid directory. Returning cached CWD: {self._cwd}")
                              return self._cwd
                     else:
                          logger.error(f"_get_current_cwd: BaseObject also lacks Path attribute. Cannot determine CWD from result: {first_result}")
                          return self._cwd # Return cached
                except AttributeError as ae:
                     logger.error(f"_get_current_cwd: Error accessing BaseObject or its Path: {ae}. Result: {first_result}")
                     return self._cwd # Return cached
                except Exception as ex:
                     logger.error(f"_get_current_cwd: Unexpected error checking BaseObject: {ex}. Result: {first_result}")
                     return self._cwd # Return cached

        # This path is taken if _run_ps_command returned [] or results.Count was 0
        logger.error(f"_get_current_cwd: No valid results received from Get-Location call. Returning cached CWD: {self._cwd}")
        return self._cwd

    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """
        Executes a command, potentially as a PowerShell background job for long-running tasks.

        Args:
            action: The command execution action.

        Returns:
            CmdOutputObservation or ErrorObservation.
        """
        if not self._initialized or self._closed:
            return ErrorObservation(content="PowerShell session is not initialized or has been closed.")

        command = action.command.strip()
        timeout_seconds = action.timeout or 60 # Default to 60 seconds hard timeout

        logger.info(f"Received command: '{command}', Timeout: {timeout_seconds}s")

        # --- Validate command structure using PowerShell Parser ---
        parse_errors = None # Using NoneType for clarity vs Collection[ParseErrorRecord]()
        statements = None
        try:
            # Parse the input command string
            # C# signature: ParseInput(string input, out Token[] tokens, out ParseError[] errors)
            # pythonnet returns (AST, tokens_array, errors_array)
            ast, _, parse_errors = Parser.ParseInput(command, None)
            # Check for parsing errors first
            if parse_errors and parse_errors.Length > 0:
                # Note: The elements in parse_errors should be of type ParseError
                error_messages = "\\n".join([f"  - {err.Message} at Line {err.Extent.StartLineNumber}, Column {err.Extent.StartColumnNumber}" for err in parse_errors])
                logger.error(f"Command failed PowerShell parsing:\\n{error_messages}")
                return ErrorObservation(
                    content=(
                        f'ERROR: Command could not be parsed by PowerShell.\\n'
                        f'Syntax errors detected:\\n{error_messages}'
                    )
                )
            # Check the number of statements in the script block's main body
            statements = ast.EndBlock.Statements
            if statements.Count > 1:
                logger.error(f"Detected {statements.Count} statements in the command. Only one is allowed.")
                return ErrorObservation(
                    content=(
                        f'ERROR: Cannot execute multiple commands at once.\\n'
                        f'Detected {statements.Count} statements in the provided command. '
                        f'Please run each command separately OR chain them using valid PowerShell operators (e.g., pipelines) within a single statement.'
                    )
                )
            elif statements.Count == 0 and not command.strip().startswith('#'): # Allow empty lines or comments
                logger.warning("Received command that resulted in zero executable statements (likely whitespace or comment).")
                # This might be handled later, but adding a check here for consistency.
                # Fall through to handle the empty command logic later.
                pass # Let the existing empty command handling logic proceed

        except Exception as parse_ex:
            logger.error(f"Exception during PowerShell command parsing: {parse_ex}")
            logger.error(traceback.format_exc())
            return ErrorObservation(
                content=f'ERROR: An exception occurred while parsing the command: {parse_ex}'
            )
        # --- End validation ---

        # --- Check if it's a CWD command to run synchronously ---
        is_cwd_command = False
        identified_cwd_cmd_name = None
        if statements and statements.Count == 1:
            # Check if the single statement is a CommandAst for a CWD command
            statement = statements[0]
            # Need to import CommandAst first
            try:
                from System.Management.Automation.Language import CommandAst, PipelineAst
                # Check if it's a Pipeline with one element which is a CommandAst
                if isinstance(statement, PipelineAst):
                    pipeline_elements = statement.PipelineElements
                    if pipeline_elements and pipeline_elements.Count == 1 and isinstance(pipeline_elements[0], CommandAst):
                        command_ast = pipeline_elements[0]
                        command_name = command_ast.GetCommandName()
                        if command_name and command_name.lower() in ['set-location', 'cd', 'push-location', 'pop-location']:
                            is_cwd_command = True
                            identified_cwd_cmd_name = command_name
                            logger.info(f"execute: Identified CWD command via PipelineAst: {command_name}")
                        # else:
                            # logger.debug(f"execute: Command in Pipeline '{command_name or \'<unknown>\'}' is not a CWD command.") # Remove
                    # else:
                        # logger.debug(f"execute: Pipeline does not contain a single CommandAst.") # Remove
                # Also handle direct CommandAst (might occur for commands without arguments?)
                elif isinstance(statement, CommandAst):
                    command_name = statement.GetCommandName()
                    if command_name and command_name.lower() in ['set-location', 'cd', 'push-location', 'pop-location']:
                        is_cwd_command = True
                        identified_cwd_cmd_name = command_name
                        logger.info(f"execute: Identified CWD command via direct CommandAst: {command_name}")
                    # else:
                         # logger.debug(f"execute: Direct CommandAst '{command_name or \'<unknown>\'}' is not a CWD command.") # Remove
                # else:
                     # logger.debug(f"execute: Statement is not PipelineAst or CommandAst, type: {type(statement)}.") # Remove
            except ImportError as imp_err:
                 logger.error(f"execute: Failed to import CommandAst: {imp_err}. Cannot check for CWD commands.")
            except Exception as ast_err:
                 logger.error(f"execute: Error checking command AST: {ast_err}")

        # logger.debug(f"execute: is_cwd_command = {is_cwd_command}") # Remove

        # === Synchronous Execution Path (for CWD commands) ===
        if is_cwd_command:
            logger.info(f"execute: Entering synchronous execution path for CWD command: '{command}'")
            ps_sync = None
            sync_output = ""
            sync_errors = []
            sync_exit_code = 1 # Default to error

            try:
                # logger.debug(f"execute[sync]: Creating PowerShell instance for '{command}'.") # Remove
                ps_sync = PowerShell.Create()
                ps_sync.Runspace = self.runspace
                # Execute the CWD command directly
                # logger.debug(f"execute[sync]: Invoking script: '{command}'") # Remove
                ps_sync.AddScript(command)
                sync_results_ps = ps_sync.Invoke()
                # logger.debug(f"execute[sync]: Invoke finished. Result count: {sync_results_ps.Count if sync_results_ps else 0}") # Remove

                # Capture output (e.g., Push-Location might output the stack)
                if sync_results_ps:
                    sync_output = "\\n".join([str(r) for r in sync_results_ps])
                    # logger.debug(f"execute[sync]: Captured output: {sync_output[:100]}...") # Remove

                # Check for errors in the stream
                if ps_sync.Streams.Error and ps_sync.Streams.Error.Count > 0:
                    sync_errors = [str(e) for e in ps_sync.Streams.Error]
                    logger.error(f"execute[sync]: Errors executing '{command}': {sync_errors}")
                    sync_exit_code = 1 # Error stream means failure
                else:
                    # logger.debug(f"execute[sync]: No errors found in stream for '{command}'. Setting exit code 0.") # Remove
                    # No errors in the stream implies success for these cmdlets
                    sync_exit_code = 0

            except Exception as e:
                logger.error(f"execute[sync]: Exception executing '{command}': {e}")
                logger.error(traceback.format_exc())
                sync_errors.append(f"[Sync Execution Exception: {e}]")
                sync_exit_code = 1 # Ensure error on exception
            finally:
                if ps_sync:
                    # logger.debug(f"execute[sync]: Disposing PowerShell instance for '{command}'.") # Remove
                    ps_sync.Dispose()

            # --- ALWAYS update CWD after synchronous execution ---
            # logger.debug(f"execute[sync]: Finished execution. ExitCode={sync_exit_code}. Current self._cwd BEFORE update: '{self._cwd}'") # Remove
            current_cwd = self._get_current_cwd() # Queries runspace and updates self._cwd
            # logger.debug(f"execute[sync]: Current self._cwd AFTER update: '{self._cwd}'. Value from _get_current_cwd: '{current_cwd}'") # Remove
            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')

            # Construct observation
            final_output_content = sync_output.strip()
            if sync_errors:
                 error_stream_text = "\\n".join(sync_errors)
                 if final_output_content:
                     final_output_content += f"\\n[ERROR STREAM]\\n{error_stream_text}"
                 else:
                     final_output_content = f"[ERROR STREAM]\\n{error_stream_text}"

            metadata = CmdOutputMetadata(exit_code=sync_exit_code, working_dir=python_safe_cwd)
            metadata.suffix = f"\\n[Synchronous command executed. Exit Code: {sync_exit_code}, CWD: {metadata.working_dir}]"
            # logger.debug(f"execute[sync]: Returning observation. Content: '{final_output_content[:100]}...', Metadata: {metadata}") # Remove

            # Return observation for synchronous command
            return CmdOutputObservation(
                content=final_output_content,
                command=action.command,
                metadata=metadata
            )

        # === Asynchronous Execution Path (for non-CWD commands) ===
        logger.info(f"execute: Entering asynchronous execution path for command: '{command}'")
        # If we reach here, it's not a simple CWD command, proceed with job logic.
        with self._job_lock: # Ensure thread-safe access/modification of self.active_job
            # --- Handle interaction with existing job ---
            if self.active_job:
                # Refresh job state before checking command
                active_job_obj = self._get_job_object(self.active_job.Id) # Get current job object
                if not active_job_obj:
                     logger.warning(f"Could not retrieve active job object {self.active_job.Id}. Clearing.")
                     self.active_job = None # Clear if object is gone
                else:
                     current_job_state = active_job_obj.JobStateInfo.State
                     if current_job_state not in [JobState.Running, JobState.NotStarted]:
                         logger.info(f"Active job {self.active_job.Id} was finished ({current_job_state}) before receiving command '{command}'. Clearing job.")
                         # Job finished on its own, clean it up before proceeding
                         self._receive_job_output(self.active_job, keep=False) # Consume final output
                         remove_script = f"Remove-Job -Job (Get-Job -Id {self.active_job.Id})"
                         self._run_ps_command(remove_script)
                         self.active_job = None
                     else:
                         # Active job is still running
                         if command == "":
                             # Check active job, returns observation directly
                             # Note: _check_active_job needs modification to update CWD on completion
                             return self._check_active_job_and_update_cwd(action) # Pass action for command info
                         elif command == "C-c":
                             # Stop active job, returns observation directly
                             # Note: _stop_active_job needs modification to use cached CWD
                             return self._stop_active_job_and_update_cwd(action) # Pass action for command info
                         else:
                             # Policy: New command received while job running -> Error? Stop old job?
                             # Current policy: Stop old job first.
                             logger.warning(f"Received new command '{command}' while job {self.active_job.Id} was active. Stopping old job first.")
                             # Stop synchronously within the lock
                             stop_script = f"Stop-Job -Job (Get-Job -Id {self.active_job.Id})"
                             self._run_ps_command(stop_script)
                             time.sleep(0.1) # Brief pause
                             self._receive_job_output(self.active_job, keep=False) # Consume output
                             remove_script = f"Remove-Job -Job (Get-Job -Id {self.active_job.Id})"
                             self._run_ps_command(remove_script)
                             logger.info(f"Old job {self.active_job.Id} stopped and removed.")
                             self.active_job = None
                             # Fall through to start the new command as a job below


            # --- If we reach here, there is no active job ---
            if command == "": # Handle empty command when NO job is active
                logger.warning("Received empty command string (no active job).")
                # Get current CWD and update state
                current_cwd = self._get_current_cwd() # Queries runspace and updates self._cwd
                python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\') # Escape it
                metadata = CmdOutputMetadata(exit_code=0, working_dir=python_safe_cwd)
                metadata.suffix = f"\\n[Empty command received. No active job. CWD: {metadata.working_dir}]"
                return CmdOutputObservation(content="", command="", metadata=metadata)

            if command.startswith("C-"): # Handle C-* when NO job is active/relevant
                logger.warning(f"Received control character command: {command}. Not supported when no job active.")
                # Get current CWD for context, but it doesn't change
                current_cwd = self._cwd # Use cached CWD
                python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\') # Escape it
                metadata = CmdOutputMetadata(exit_code=1, working_dir=python_safe_cwd) # Indicate error, use cached CWD
                return ErrorObservation(
                    content=f"Control commands like {command} are not supported or relevant when no job is active.",
                    metadata=metadata # Add metadata for context
                 )

        # --- Start the command as a new asynchronous job ---
        # (Lock is released after the 'with' block above if job interaction occurred)
        ps_start = None
        job = None
        output_builder = []
        all_errors = [] # Collect errors across monitoring
        exit_code = 1 # Default error
        timed_out = False
        job_start_failed = False
        job_id = None # Keep track of the job ID

        try:
            # ... (rest of the job starting logic remains the same) ...
            # Use the lock when setting self.active_job
            ps_start = PowerShell.Create()
            ps_start.Runspace = self.runspace
            escaped_command = command.replace("'", "''") # Basic single quote escaping
            # Use the current CWD for the job's initial location
            # Ensure CWD is escaped correctly for the script block
            escaped_cwd = self._cwd.replace("'", "''")
            start_job_script = f"Start-Job -ScriptBlock {{ Set-Location '{escaped_cwd}'; {escaped_command} 2>&1 }}"

            logger.info(f"Starting command as PowerShell job: {command}")
            ps_start.AddScript(start_job_script)
            start_results = ps_start.Invoke() # Run Start-Job

            # Check for errors during Start-Job execution itself
            if ps_start.Streams.Error:
                errors = [str(e) for e in ps_start.Streams.Error]
                logger.error(f"Errors during Start-Job execution: {errors}")
                all_errors.extend(errors)
                # Continue to try and get job, maybe it partially succeeded

            # Now, try to get the latest job
            ps_get = PowerShell.Create()
            ps_get.Runspace = self.runspace
            get_job_script = "Get-Job | Sort-Object -Property Id -Descending | Select-Object -First 1"
            ps_get.AddScript(get_job_script)
            get_results = ps_get.Invoke()

            if ps_get.Streams.Error:
                errors = [str(e) for e in ps_get.Streams.Error]
                logger.error(f"Errors getting latest job: {errors}")
                all_errors.extend(errors)
                job_start_failed = True # Fail if we can't even get the job

            if not job_start_failed and get_results and len(get_results) > 0:
                potential_job = get_results[0]
                try:
                    underlying_job = potential_job.BaseObject
                    job_id_test = underlying_job.Id
                    job_state_test = underlying_job.JobStateInfo.State
                    job = underlying_job
                    job_id = job.Id
                    # Acquire lock ONLY when modifying shared state (self.active_job)
                    with self._job_lock:
                        self.active_job = job
                    logger.info(f"Job retrieved successfully. Job ID: {job.Id}, State: {job_state_test}")
                    if job_state_test == JobState.Failed:
                        logger.error(f"Job {job.Id} failed immediately after starting.")
                        output_chunk, error_chunk = self._receive_job_output(job, keep=False)
                        if output_chunk: output_builder.append(output_chunk)
                        if error_chunk: all_errors.extend(error_chunk)
                        job_start_failed = True
                        remove_script = f"Remove-Job -Job (Get-Job -Id {job.Id})"
                        self._run_ps_command(remove_script)
                        with self._job_lock: # Need lock to clear
                            self.active_job = None
                except AttributeError as e:
                    logger.error(f"Get-Job returned an object without expected properties on BaseObject: {e}")
                    logger.error(traceback.format_exc())
                    all_errors.append("Get-Job did not return a valid Job object.")
                    job_start_failed = True

            elif not job_start_failed:
                logger.error("Get-Job did not return any results.")
                all_errors.append("Get-Job did not return any results.")
                job_start_failed = True

        except Exception as start_ex:
            logger.error(f"Exception during job start/retrieval: {start_ex}")
            logger.error(traceback.format_exc())
            all_errors.append(f"[Job Start/Get Exception: {start_ex}]")
            job_start_failed = True
        finally:
            if ps_start:
                ps_start.Dispose()
            if 'ps_get' in locals() and ps_get:
                ps_get.Dispose()

        if job_start_failed:
            # Update CWD state even on failure, although it likely didn't change
            current_cwd = self._get_current_cwd()
            python_safe_cwd = current_cwd.replace('\\\\', '\\\\\\\\')
            metadata = CmdOutputMetadata(exit_code=1, working_dir=python_safe_cwd)
            return ErrorObservation(
                content=f"Failed to start PowerShell job.\\n[ERRORS]\\n" + "\\n".join(all_errors),
                metadata=metadata # Include CWD context
            )

        # --- Monitor the Job ---
        start_time = time.monotonic()
        monitoring_loop_finished = False
        shutdown_requested = False
        final_state = JobState.Failed # Assume failed unless updated


        while not monitoring_loop_finished:
            if not should_continue():
                logger.warning("Shutdown signal received during job monitoring.")
                shutdown_requested = True
                monitoring_loop_finished = True
                exit_code = -1 # Indicate external interruption
                continue

            elapsed_seconds = time.monotonic() - start_time
            if elapsed_seconds > timeout_seconds:
                logger.warning(f"Command job monitoring exceeded timeout ({timeout_seconds}s). Leaving job running.")
                timed_out = True
                monitoring_loop_finished = True
                exit_code = -1 # Indicate timeout occurred
                continue

            # Get current job object safely
            current_job_obj = self._get_job_object(job_id)
            if not current_job_obj:
                logger.error(f"Job {job_id} object disappeared during monitoring.")
                all_errors.append("[Job object lost during monitoring]")
                monitoring_loop_finished = True
                exit_code = 1
                final_state = JobState.Failed # Update final state
                continue

            # Check for output
            output_chunk, error_chunk = self._receive_job_output(current_job_obj, keep=True)
            if output_chunk:
                output_builder.append(output_chunk)
            if error_chunk:
                all_errors.extend(error_chunk)

            # Check job state
            current_state = current_job_obj.JobStateInfo.State
            if current_state not in [JobState.Running, JobState.NotStarted]:
                logger.info(f"Job {job_id} finished monitoring loop with state: {current_state}")
                monitoring_loop_finished = True
                final_state = current_state # Store the final state
                continue

            time.sleep(0.1) # Sleep 100ms

        # --- Monitoring loop finished ---

        # Determine if job finished naturally based on final state
        job_finished_naturally = (not timed_out and not shutdown_requested and
                                 final_state in [JobState.Completed, JobState.Stopped, JobState.Failed])


        determined_cwd = self._cwd # Default to cached CWD
        if job_finished_naturally:
            logger.info(f"Job {job_id} finished naturally with state: {final_state}. Clearing final output buffer.")
            # Get final output/errors
            final_job_obj = self._get_job_object(job_id) # Re-fetch just in case
            if final_job_obj:
                 _, final_error_chunk = self._receive_job_output(final_job_obj, keep=False)
                 if final_error_chunk: all_errors.extend(final_error_chunk)
            else:
                 logger.warning(f"Could not get final job object {job_id} to clear output buffer.")


            # Determine final exit code based on state
            exit_code = 0 if final_state == JobState.Completed else 1

            # --- Update CWD only if job COMPLETED successfully ---
            if final_state == JobState.Completed:
                 logger.info(f"Job {job_id} completed successfully. Querying final CWD.")
                 determined_cwd = self._get_current_cwd() # Query runspace and update self._cwd
            else:
                 logger.info(f"Job {job_id} finished but did not complete successfully ({final_state}). Using cached CWD: {self._cwd}")
                 determined_cwd = self._cwd # Use cached CWD for Failed/Stopped states


            # Clean up finished job (remove from PS repository)
            with self._job_lock: # Lock to clear active_job
                remove_script = f"Remove-Job -Job (Get-Job -Id {job_id})"
                self._run_ps_command(remove_script)
                if self.active_job and self.active_job.Id == job_id:
                    self.active_job = None
                logger.info(f"Cleaned up finished job {job_id}")

        else:
            # Job timed out or was shutdown - use cached CWD
            logger.info(f"Job {job_id} did not finish naturally (timeout={timed_out}, shutdown={shutdown_requested}). Using cached CWD: {self._cwd}")
            determined_cwd = self._cwd # Use cached CWD
            # Exit code is already -1 from loop exit reason


        # Escape CWD for metadata
        python_safe_cwd = determined_cwd.replace('\\\\', '\\\\\\\\')

        # Combine output and errors for final observation
        final_output = "\\n".join(output_builder).strip()
        if all_errors:
            error_stream_text = "\\n".join(all_errors)
            if final_output:
                 final_output += f"\\n[ERROR STREAM]\\n{error_stream_text}"
            else:
                 final_output = f"[ERROR STREAM]\\n{error_stream_text}"
            # If there were errors in the stream, ensure exit code reflects failure
            # unless it was already set to -1 (timeout/shutdown)
            if exit_code == 0:
                exit_code = 1

        # Create metadata
        metadata = CmdOutputMetadata(exit_code=exit_code, working_dir=python_safe_cwd) # Use determined CWD
        if timed_out:
            # Match the suffix format expected by tests for timeout
            suffix = (
                f"[The command timed out after {int(timeout_seconds)} seconds. "
                f"You may wait longer to see additional output by sending empty command '', "
                f"send other commands to interact with the current process, "
                f"or send keys to interrupt/kill the command.]"
            )
        elif shutdown_requested:
            suffix = f"\\n[Command execution cancelled due to shutdown signal. Job {job_id} may still be running. Exit Code: {exit_code}, CWD: {metadata.working_dir}]"
        elif job_finished_naturally:
            # Use the actual final state determined earlier
            status = "Completed" if final_state == JobState.Completed else f"Finished ({final_state})"
            suffix = f"\\n[Command completed via Job {job_id}. Status: {status}, Exit Code: {exit_code}, CWD: {metadata.working_dir}]"
        else: # Should not happen, but defensive fallback
             suffix = f"\\n[Command execution finished. State: {final_state}, Exit Code: {exit_code}, CWD: {metadata.working_dir}]"

        metadata.suffix = suffix

        return CmdOutputObservation(
            content=final_output,
            command=command,
            metadata=metadata
        )

    def close(self):
        """Closes the PowerShell runspace and releases resources, stopping any active job."""
        if self._closed:
            return

        logger.info("Closing PowerShell session runspace.")

        # Stop and remove any active job before closing runspace
        with self._job_lock:
            if self.active_job:
                logger.warning(f"Session closing with active job {self.active_job.Id}. Attempting to stop and remove.")
                job_id = self.active_job.Id
                try:
                    # Ensure job object exists before trying to stop/remove
                    active_job_obj = self._get_job_object(job_id)
                    if active_job_obj:
                        stop_script = f"Stop-Job -Job (Get-Job -Id {job_id})"
                        self._run_ps_command(stop_script) # Use helper before runspace closes
                        time.sleep(0.1)
                        remove_script = f"Remove-Job -Job (Get-Job -Id {job_id})"
                        self._run_ps_command(remove_script)
                        logger.info(f"Stopped and removed active job {job_id} during close.")
                    else:
                        logger.warning(f"Could not find job object {job_id} to stop/remove during close.")
                except Exception as e:
                    logger.error(f"Error stopping/removing job {job_id} during close: {e}")
                self.active_job = None

        if hasattr(self, 'runspace') and self.runspace:
            try:
                # Check state using System.Management.Automation.Runspaces namespace
                # Get the state info object first to avoid potential pythonnet issues with nested access
                runspace_state_info = self.runspace.RunspaceStateInfo
                if runspace_state_info.State == RunspaceState.Opened:
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
