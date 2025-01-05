from openhands.events.observation.commands import (
    CmdOutputMetadata,
    CmdOutputObservation,
    IPythonRunCellObservation,
)


def test_cmd_output_success():
    # Test successful command
    obs = CmdOutputObservation(
        command='ls',
        content='file1.txt\nfile2.txt',
        metadata=CmdOutputMetadata(exit_code=0),
    )
    assert obs.success is True
    assert obs.error is False

    # Test failed command
    obs = CmdOutputObservation(
        command='ls',
        content='No such file or directory',
        metadata=CmdOutputMetadata(exit_code=1),
    )
    assert obs.success is False
    assert obs.error is True


def test_ipython_cell_success():
    # IPython cells are always successful
    obs = IPythonRunCellObservation(code='print("Hello")', content='Hello')
    assert obs.success is True
    assert obs.error is False
