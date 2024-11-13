import toml
import os
import openhands_resolver

def test_version():
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one directory to reach the project root
    project_root = os.path.dirname(current_dir)
    # Construct the path to pyproject.toml
    pyproject_path = os.path.join(project_root, 'pyproject.toml')
    
    # Read the pyproject.toml file
    with open(pyproject_path, 'r') as f:
        pyproject_data = toml.load(f)
    
    # Get the version from the pyproject.toml file
    version = pyproject_data['tool']['poetry']['version']
    
    assert version == openhands_resolver.__version__
