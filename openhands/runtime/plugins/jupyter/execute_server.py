#!/usr/bin/env python3

import asyncio
import logging
import os
import re
from uuid import uuid4

import tornado
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from tornado.escape import json_decode, json_encode, url_escape
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.ioloop import PeriodicCallback
from tornado.websocket import websocket_connect

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


from typing import cast
from tornado.websocket import WebSocketClientConnection


class JupyterKernel:
    def __init__(self, url_suffix: str, convid: str, lang: str = 'python') -> None:
        self.base_url = f'http://{url_suffix}'
        self.base_ws_url = f'ws://{url_suffix}'
        self.lang = lang
        self.kernel_id: str | None = None
        self.ws: WebSocketClientConnection | None = None
        self.convid = convid
        logging.info(
            f'Jupyter kernel created for conversation {convid} at {url_suffix}'
        )

        self.heartbeat_interval = 10000  # 10 seconds
        self.heartbeat_callback: PeriodicCallback | None = None
        self.initialized = False

    async def initialize(self) -> None:
        await self.execute(r'%colors nocolor')
        # pre-defined tools
        self.tools_to_run: list[str] = [
            # TODO: You can add code for your pre-defined tools here
        ]
        for tool in self.tools_to_run:
            res = await self.execute(tool)
            logging.info(f'Tool [{tool}] initialized:\n{res}')
        self.initialized = True

    async def _send_heartbeat(self) -> None:
        ws = self.ws
        if not ws:
            return
        try:
            ws.ping()
            # logging.info('Heartbeat sent...')
        except tornado.iostream.StreamClosedError:
            # logging.info('Heartbeat failed, reconnecting...')
            try:
                await self._connect()
            except ConnectionRefusedError:
                logging.info(
                    'ConnectionRefusedError: Failed to reconnect to kernel websocket - Is the kernel still running?'
                )

    async def _connect(self) -> None:
        # Close existing websocket
        ws = self.ws
        if ws:
            try:
                ws.close()
            except Exception:
                pass
            self.ws = None

        # Get or create kernel ID
        client = AsyncHTTPClient()
        kernel_id = self.kernel_id
        if not kernel_id:
            n_tries = 5
            while n_tries > 0:
                try:
                    response = await client.fetch(
                        '{}/api/kernels'.format(self.base_url),
                        method='POST',
                        body=json_encode({'name': self.lang}),
                    )
                    kernel = json_decode(response.body)
                    kernel_id = kernel['id']
                    self.kernel_id = kernel_id
                    break
                except Exception:
                    # kernels are not ready yet
                    n_tries -= 1
                    if n_tries > 0:
                        await asyncio.sleep(1)
                    else:
                        raise ConnectionRefusedError('Failed to connect to kernel')

        assert kernel_id is not None

        # Connect to websocket
        ws_req = HTTPRequest(
            url='{}/api/kernels/{}/channels'.format(
                self.base_ws_url, url_escape(kernel_id)
            )
        )
        ws = await websocket_connect(ws_req)
        if not ws:
            raise ConnectionRefusedError('Failed to connect to websocket')
        self.ws = ws
        logging.info('Connected to kernel websocket')

        # Setup heartbeat
        if self.heartbeat_callback:
            self.heartbeat_callback.stop()
        callback = PeriodicCallback(
            self._send_heartbeat, self.heartbeat_interval
        )
        callback.start()
        self.heartbeat_callback = callback

    @retry(
        retry=retry_if_exception_type(ConnectionRefusedError),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
    )
    async def execute(self, code: str, timeout: int = 120) -> str:
        # Connect to kernel if needed
        if not self.ws:
            try:
                await self._connect()
            except ConnectionRefusedError:
                return '[Failed to connect to kernel]'

        ws = self.ws
        if not ws:
            return '[Failed to connect to kernel]'

        # Send code to kernel
        msg_id = uuid4().hex
        try:
            res = await ws.write_message(
                json_encode(
                    {
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
                )
            )
            if not res:
                return '[Failed to send code to kernel]'
        except Exception:
            return '[Failed to send code to kernel]'

        logging.info(f'Executed code in jupyter kernel:\n{res}')

        outputs: list[str] = []

        async def wait_for_messages() -> bool:
            execution_done = False
            while not execution_done:
                ws = self.ws
                if not ws:
                    return False
                try:
                    msg = await ws.read_message()
                    if not msg:
                        return False
                    msg = json_decode(msg)
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
                            # use markdone to display image (in case of large image)
                            outputs.append(
                                f"\n![image](data:image/png;base64,{msg['content']['data']['image/png']})\n"
                            )

                    elif msg_type == 'execute_reply':
                        execution_done = True
                except Exception:
                    return False
            return execution_done

        async def interrupt_kernel() -> None:
            kernel_id = self.kernel_id
            if not kernel_id:
                return
            try:
                client = AsyncHTTPClient()
                interrupt_response = await client.fetch(
                    f'{self.base_url}/api/kernels/{kernel_id}/interrupt',
                    method='POST',
                    body=json_encode({'kernel_id': kernel_id}),
                )
                logging.info(f'Kernel interrupted: {interrupt_response}')
            except Exception:
                logging.error('Failed to interrupt kernel')

        try:
            execution_done = await asyncio.wait_for(wait_for_messages(), timeout)
            if not execution_done:
                await interrupt_kernel()
                return '[Failed to execute code]'
        except asyncio.TimeoutError:
            await interrupt_kernel()
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

    async def shutdown_async(self) -> None:
        # Delete kernel
        kernel_id = self.kernel_id
        if kernel_id:
            try:
                client = AsyncHTTPClient()
                await client.fetch(
                    '{}/api/kernels/{}'.format(self.base_url, kernel_id),
                    method='DELETE',
                )
            except Exception:
                logging.error('Failed to delete kernel')
            finally:
                self.kernel_id = None

        # Close websocket
        ws = self.ws
        if ws:
            try:
                ws.close()
            except Exception:
                logging.error('Failed to close websocket')
            finally:
                self.ws = None


class ExecuteHandler(tornado.web.RequestHandler):
    def initialize(self, jupyter_kernel: JupyterKernel) -> None:
        self.jupyter_kernel = jupyter_kernel

    async def post(self) -> None:
        data = json_decode(self.request.body)
        code = data.get('code')

        if not code:
            self.set_status(400)
            self.write('Missing code')
            return

        output = await self.jupyter_kernel.execute(code)

        self.write(output)


def make_app() -> tornado.web.Application:
    jupyter_kernel = JupyterKernel(
        f"localhost:{os.environ.get('JUPYTER_GATEWAY_PORT')}",
        os.environ.get('JUPYTER_GATEWAY_KERNEL_ID', ''),
    )
    asyncio.get_event_loop().run_until_complete(jupyter_kernel.initialize())

    return tornado.web.Application(
        [
            (r'/execute', ExecuteHandler, {'jupyter_kernel': jupyter_kernel}),
        ]
    )


if __name__ == '__main__':
    app = make_app()
    app.listen(os.environ.get('JUPYTER_EXEC_SERVER_PORT'))
    tornado.ioloop.IOLoop.current().start()
