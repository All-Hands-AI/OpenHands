import os
import sys
import time
import traceback

import requests

# Read the Python code from STDIN
code = sys.stdin.read()


def execute_code(code, print_output=True):
    PORT = os.environ.get('JUPYTER_EXEC_SERVER_PORT')
    POST_URL = f'http://localhost:{PORT}/execute'

    # Set the default kernel ID
    kernel_id = 'default'
    output = ''
    for i in range(3):
        try:
            response = requests.post(
                POST_URL, json={'kernel_id': kernel_id, 'code': code}
            )
            output = response.text
            if '500: Internal Server Error' not in output:
                if print_output:
                    print(output)
                break
        except requests.exceptions.ConnectionError:
            if i == 2:
                traceback.print_exc()
        time.sleep(2)
    else:
        if not output:
            with open('/opendevin/logs/jupyter_execute_server.log', 'r') as f:
                output = f.read()
        print('Failed to connect to the Jupyter server', output)


if jupyter_pwd := os.environ.get('JUPYTER_PWD'):
    execute_code(
        f'import os\nos.environ["JUPYTER_PWD"] = "{jupyter_pwd}"\n', print_output=False
    )

execute_code(code)
