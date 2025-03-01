import time

from openhands.events.action import CmdRunAction, StopProcessesAction
from openhands.runtime.utils.bash import BashSession


def test_stop_button_background_process():
    session = BashSession(work_dir="/tmp", no_change_timeout_seconds=2)
    session.initialize()

    # Start a process that runs indefinitely and detaches from the terminal
    obs = session.execute(
        CmdRunAction("nohup sleep 60 > /dev/null 2>&1 &")  # Background process that detaches from terminal
    )
    time.sleep(2)  # Give time for the process to start

    # Get initial process info
    process_info = session.get_running_processes()
    print("Initial process info:", process_info)  # Debug output
    assert any("sleep" in p for p in process_info["processes"]), "Expected to find sleep process"
    initial_processes = [p for p in process_info["processes"] if "sleep" in p]
    assert len(initial_processes) > 0, "Expected at least one sleep process"

    # Send Ctrl+C to try to stop it
    obs = session.execute(CmdRunAction("C-c", is_input=True))
    time.sleep(1)  # Give time for Ctrl+C to take effect

    # Check if process is still running (it shouldn't be, but it is - this is the bug)
    process_info = session.get_running_processes()
    print("Process info after Ctrl+C:", process_info)  # Debug output
    assert not any("sleep" in p for p in process_info["processes"]), "Background process should be terminated but is still running"

    session.close()