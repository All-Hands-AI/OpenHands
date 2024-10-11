#!/usr/bin/env python3

import json
import logging
import os
import re
import time
from threading import Thread
from uuid import uuid4

import requests
from flask import Flask, jsonify, request
from websockets.sync.client import connect as ws_connect

logging.basicConfig(level=logging.INFO)


def strip_ansi(o: str) -> str:
    """Removes ANSI escape sequences from `o`, as defined by ECMA-048 in
    http://www.ecma-international.org/publications/files/ECMA-ST/Ecma-048.pdf

    # https://github.com/ewen-lbh/python-strip-ansi/blob/master/strip_ansi/__init__.py

    >>> strip_ansi("\\033[33mLorem ipsum\\033[0m")
    'Lorem ipsum'

    >>> strip_ansi("Lorem \\033[38;25mIpsum\\033[0m sit\\namet.")
    'Lorem Ipsum sit\\namet.'

    >>> strip_ansi("")
    ''

    >>> strip_ansi("\\x1b[0m")
    ''

    >>> strip_ansi("Lorem")
    'Lorem'

    >>> strip_ansi('\\x1b[38;5;32mLorem ipsum\\x1b[0m')
    'Lorem ipsum'

    >>> strip_ansi('\\x1b[1m\\x1b[46m\\x1b[31mLorem dolor sit ipsum\\x1b[0m')
    'Lorem dolor sit ipsum'
    """
    # pattern = re.compile(r'/(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]/')
    pattern = re.compile(r'\x1B\[\d+(;\d+){0,2}m')
    stripped = pattern.sub('', o)
    return stripped


class JupyterKernel:
    def __init__(self, url_suffix, convid, lang='python'):
        self.base_url = f'http://{url_suffix}'
        self.base_ws_url = f'ws://{url_suffix}'
        self.lang = lang
        self.kernel_id = None
        self.ws = None
        self.convid = convid
        logging.info(
            f'Jupyter kernel created for conversation {convid} at {url_suffix}'
        )

        self.heartbeat_interval = 10
        self.heartbeat_thread = None
        self.initialized = False

    def initialize(self):
        self.execute(r'%colors nocolor')
        # pre-defined tools
        self.tools_to_run: list[str] = [
            # TODO: You can add code for your pre-defined tools here
        ]
        for tool in self.tools_to_run:
            res = self.execute(tool)
            logging.info(f'Tool [{tool}] initialized:\n{res}')
        self.initialized = True

    def _send_heartbeat(self):
        while True:
            if self.ws:
                try:
                    self.ws.ping()
                except Exception:
                    try:
                        self._connect()
                    except ConnectionRefusedError:
                        logging.info(
                            'ConnectionRefusedError: Failed to reconnect to kernel websocket - Is the kernel still running?'
                        )
            time.sleep(self.heartbeat_interval)

    def _connect(self):
        if self.ws:
            self.ws.close()
            self.ws = None

        if not self.kernel_id:
            n_tries = 5
            while n_tries > 0:
                try:
                    response = requests.post(
                        f'{self.base_url}/api/kernels', json={'name': self.lang}
                    )
                    kernel = response.json()
                    self.kernel_id = kernel['id']
                    break
                except Exception:
                    # kernels are not ready yet
                    n_tries -= 1
                    time.sleep(1)

            if n_tries == 0:
                raise ConnectionRefusedError('Failed to connect to kernel')

        self.ws = ws_connect(
            f'{self.base_ws_url}/api/kernels/{self.kernel_id}/channels'
        )
        logging.info('Connected to kernel websocket')

        # Setup heartbeat
        if not self.heartbeat_thread:
            self.heartbeat_thread = Thread(target=self._send_heartbeat, daemon=True)
            self.heartbeat_thread.start()

    def execute(self, code: str, timeout: int | None = None):
        if not self.ws:
            self._connect()
        assert self.ws is not None

        msg_id = uuid4().hex
        message = {
            'header': {
                'username': '',
                'version': '5.0',
                'session': '',
                'msg_id': msg_id,
                'msg_type': 'execute_request',
            },
            'parent_header': {},
            'channel': 'shell',
            'content': {
                'code': code,
                'silent': False,
                'store_history': False,
                'user_expressions': {},
                'allow_stdin': False,
            },
            'metadata': {},
            'buffers': {},
        }
        self.ws.send(json.dumps(message))
        logging.info(f'Executed code in jupyter kernel:\n{code}')

        outputs = []
        execution_done = False
        start_time = time.time()

        while not execution_done and time.time() - start_time < (timeout or 120):
            msg = json.loads(self.ws.recv())
            msg_type = msg['msg_type']
            parent_msg_id = msg['parent_header'].get('msg_id', None)

            if parent_msg_id != msg_id:
                continue

            if os.environ.get('DEBUG'):
                logging.info(
                    f"MSG TYPE: {msg_type.upper()} DONE:{execution_done}\nCONTENT: {msg['content']}"
                )

            if msg_type == 'error':
                traceback = '\n'.join(msg['content']['traceback'])
                outputs.append(traceback)
                execution_done = True
            elif msg_type == 'stream':
                outputs.append(msg['content']['text'])
            elif msg_type in ['execute_result', 'display_data']:
                outputs.append(msg['content']['data']['text/plain'])
                if 'image/png' in msg['content']['data']:
                    outputs.append(
                        f"\n![image](data:image/png;base64,{msg['content']['data']['image/png']})\n"
                    )
            elif msg_type == 'execute_reply':
                execution_done = True

        if not execution_done:
            self._interrupt_kernel()
            return f'[Execution timed out ({timeout} seconds).]'

        if not outputs and execution_done:
            ret = '[Code executed successfully with no output]'
        else:
            ret = ''.join(outputs)

        # Remove ANSI
        ret = strip_ansi(ret)

        if os.environ.get('DEBUG'):
            logging.info(f'OUTPUT:\n{ret}')
        return ret

    def _interrupt_kernel(self):
        requests.post(
            f'{self.base_url}/api/kernels/{self.kernel_id}/interrupt',
            json={'kernel_id': self.kernel_id},
        )
        logging.info('Kernel interrupted')

    def shutdown(self):
        if self.kernel_id:
            requests.delete(f'{self.base_url}/api/kernels/{self.kernel_id}')
            self.kernel_id = None
            if self.ws:
                self.ws.close()
                self.ws = None


if __name__ == '__main__':
    app = Flask(__name__)

    jupyter_kernel = JupyterKernel(
        f"localhost:{os.environ.get('JUPYTER_GATEWAY_PORT')}",
        os.environ.get('JUPYTER_GATEWAY_KERNEL_ID'),
    )
    jupyter_kernel.initialize()

    @app.route('/execute', methods=['POST'])
    def execute():
        data = request.json
        code = data.get('code')

        if not code:
            return jsonify({'error': 'Missing code'}), 400

        output = jupyter_kernel.execute(code)
        return jsonify({'output': output})

    app.run(port=int(os.environ.get('JUPYTER_EXEC_SERVER_PORT', 8000)))
