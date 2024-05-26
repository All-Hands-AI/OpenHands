import os
import sys
import time

import requests

# Read the Python code from STDIN
code = sys.stdin.read()

# Set the default kernel ID
kernel_id = 'default'

PORT = os.environ.get('JUPYTER_EXEC_SERVER_PORT')
POST_URL = f'http://localhost:{PORT}/execute'

for i in range(10):
    try:
        response = requests.post(POST_URL, json={'kernel_id': kernel_id, 'code': code})
        if '500: Internal Server Error' not in response.text:
            print(response.text)
            break
    except requests.exceptions.ConnectionError:
        pass
    time.sleep(2)
else:
    print('Failed to connect to the Jupyter server')
