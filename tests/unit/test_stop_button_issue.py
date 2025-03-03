import time

from openhands.events.action import CmdRunAction
from openhands.runtime.utils.bash import BashSession


def test_stop_button_background_process():
    session = BashSession(work_dir='/tmp', no_change_timeout_seconds=2)
    session.initialize()

    # Start a process that runs indefinitely and detaches from the terminal
    session.execute(
        CmdRunAction(
            'nohup sleep 60 > /dev/null 2>&1 &'
        )  # Background process that detaches from terminal
    )
    time.sleep(2)  # Give time for the process to start

    # Get initial process info
    process_info = session.get_running_processes()
    print('Initial process info:', process_info)  # Debug output
    assert any(
        'sleep' in p for p in process_info['processes']
    ), 'Expected to find sleep process'
    initial_processes = [p for p in process_info['processes'] if 'sleep' in p]
    assert len(initial_processes) > 0, 'Expected at least one sleep process'

    # Send kill command to stop it
    session.execute(CmdRunAction('pkill -P $$'))
    time.sleep(1)  # Give time for processes to be killed

    # Check if process is still running (it should be terminated)
    process_info = session.get_running_processes()
    print('Process info after kill command:', process_info)  # Debug output
    assert not any(
        'sleep' in p for p in process_info['processes']
    ), 'Background process should be terminated'

    session.close()
