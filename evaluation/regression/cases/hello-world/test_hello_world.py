import os

import pytest
from conftest import agents


@pytest.mark.parametrize('agent', agents())
def test_hello_world(task_file, run_test_case, agent):
    """Test case for the "Hello, World!" Bash script using different agents."""
    # Run the test case for the specified agent
    workspace_dir = run_test_case(agent, 'hello-world')

    # Validate the generated workspace
    assert os.path.exists(workspace_dir)
    assert os.path.isfile(os.path.join(workspace_dir, 'hello_world.sh'))

    # Execute the hello_world.sh script
    os.chdir(workspace_dir)
    output = os.popen('bash hello_world.sh').read()
    assert output == 'Hello, World!\n'
