import time

from openhands.events.action import CmdRunAction
from openhands.runtime.utils.bash import BashSession


def test_stop_button_background_process():
    session = BashSession(work_dir="/tmp", no_change_timeout_seconds=2)
    session.initialize()

    # Start a process that runs indefinitely
    obs = session.execute(
        CmdRunAction("yes > /dev/null &")  # Background process that runs forever
    )
    time.sleep(2)  # Give time for the process to start

    # Get initial process info
    process_info = session.get_running_processes()
    print("Initial process info:", process_info)  # Debug output
    assert any("yes" in p for p in process_info["processes"]), "Expected to find yes process"
    initial_processes = [p for p in process_info["processes"] if "yes" in p]
    assert len(initial_processes) > 0, "Expected at least one yes process"

    # Send Ctrl+C to try to stop it
    obs = session.execute(CmdRunAction("C-c", is_input=True))
    time.sleep(1)  # Give time for Ctrl+C to take effect

    # Check if process is still running (it shouldn't be, but it is - this is the bug)
    process_info = session.get_running_processes()
    print("Process info after Ctrl+C:", process_info)  # Debug output
    assert not any("yes" in p for p in process_info["processes"]), "Background process should be terminated but is still running"

    session.close()