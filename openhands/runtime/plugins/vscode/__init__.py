import subprocess
import time
from dataclasses import dataclass
from typing import Any, Callable

import requests
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import ClosingIterator

from openhands.core.logger import openhands_logger as logger
from openhands.runtime.plugins.requirement import Plugin, PluginRequirement
from openhands.runtime.utils import find_available_tcp_port
from openhands.runtime.utils.shutdown_listener import should_continue


@dataclass
class VSCodeRequirement(PluginRequirement):
    name: str = 'vscode'


class VSCodePlugin(Plugin):
    name: str = 'vscode'

    async def initialize(self, username: str):
        self.vscode_port = find_available_tcp_port(40000, 49999)
        self._vscode_url = f'http://localhost:{self.vscode_port}'
        self.gateway_process = subprocess.Popen(
            (
                f"su - {username} -s /bin/bash << 'EOF'\n"
                f'sudo chown -R {username}:{username} /openhands/.openvscode-server\n'
                'cd /workspace\n'
                f'exec /openhands/.openvscode-server/bin/openvscode-server --host 0.0.0.0 --without-connection-token --port {self.vscode_port}\n'
                'EOF'
            ),
            stderr=subprocess.STDOUT,
            shell=True,
        )
        # read stdout until the kernel gateway is ready
        output = ''
        while should_continue() and self.gateway_process.stdout is not None:
            line = self.gateway_process.stdout.readline().decode('utf-8')
            print(line)
            output += line
            if 'at' in line:
                break
            time.sleep(1)
            logger.debug('Waiting for VSCode server to start...')

        logger.debug(
            f'VSCode server started at port {self.vscode_port}. Output: {output}'
        )

    @property
    def vscode_proxy(self) -> Any:
        """
        Returns a WSGI application that proxies requests to the VSCode server
        """

        def application(environ: dict, start_response: Callable) -> ClosingIterator:
            request = Request(environ)

            # Remove the /vscode prefix from the path
            path = request.path
            if path.startswith('/vscode'):
                path = path[len('/vscode') :]

            # Forward the request to VSCode server
            url = f'{self._vscode_url}{path}'

            # Forward the request method and headers
            headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower() not in ('host', 'content-length')
            }

            try:
                response = requests.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    data=request.get_data(),
                    stream=True,
                    params=request.args,
                    allow_redirects=False,
                )

                # Create the response
                proxy_response = Response(
                    response=response.iter_content(chunk_size=1024),
                    status=response.status_code,
                    headers=dict(response.headers),
                )

                return proxy_response.get_wsgi_response(environ)(
                    environ, start_response
                )

            except requests.RequestException as e:
                # Handle connection errors
                proxy_response = Response(f'VSCode server error: {str(e)}', status=502)
                return proxy_response.get_wsgi_response(environ)(
                    environ, start_response
                )

        return application
