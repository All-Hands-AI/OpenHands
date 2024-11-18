"""
A dummy agent which copies the `sample_submission.csv` from the workspace/data directory
and uses that as its `submission.csv`.
"""

import getpass
import os
import shutil
import sys
from pathlib import Path

# Get the current user's username
username = getpass.getuser()

# Check if the current user ID is 0 (root user ID on Unix-like systems)
if os.getuid() == 0:
    print(f"You are running this script as root. Your username is '{username}'.")
else:
    print(f'You do not have root access. Your username is {username}.')

print('The script is being run with the following python interpreter:')
print(sys.executable)

cwd = Path(__file__).parent
workspace_data_dir = cwd.parent / 'data'

print('Copying sample submission...')

shutil.copy(
    workspace_data_dir / 'sample_submission.csv',
    cwd.parent / 'submission' / 'submission.csv',
)

print(f"Sample submission copied to {cwd.parent / 'submission' / 'submission.csv'}.")
