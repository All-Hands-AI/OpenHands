#!/usr/bin/env python3

import asyncio
import sys
import tempfile

# Add the OpenHands directory to the path
sys.path.insert(0, '/workspace/OpenHands')

from openhands.core.config import OpenHandsConfig
from openhands.core.config.mcp_config import MCPConfig, MCPStdioServerConfig
from openhands.events import EventStream
from openhands.events.action.mcp import MCPAction
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
from openhands.storage import get_file_store


async def debug_mcp():
    print('Starting MCP debug...')

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f'Using temp dir: {temp_dir}')

        # Create MCP config
        mcp_stdio_server_config = MCPStdioServerConfig(
            name='fetch', command='uvx', args=['mcp-server-fetch']
        )
        mcp_config = MCPConfig(stdio_servers=[mcp_stdio_server_config])
        print(f'MCP config: {mcp_config}')

        # Create OpenHands config
        config = OpenHandsConfig(
            workspace_base=temp_dir,
            workspace_mount_path=temp_dir,
            workspace_mount_path_in_sandbox='/workspace',
            mcp=mcp_config,
        )

        # Create file store and event stream
        file_store = get_file_store(
            config.file_store,
            config.file_store_path,
            config.file_store_web_hook_url,
            config.file_store_web_hook_headers,
        )
        event_stream = EventStream('test_sid', file_store)

        # Create runtime
        print('Creating Docker runtime...')
        runtime = DockerRuntime(
            config=config, event_stream=event_stream, sid='test_sid', plugins=[]
        )

        try:
            print('Connecting to runtime...')
            await runtime.connect()
            print('Runtime connected successfully')

            # Check the MCP config
            print('Getting MCP config from runtime...')
            if hasattr(runtime, 'get_mcp_config'):
                runtime_mcp_config = runtime.get_mcp_config()
                print(f'Runtime MCP config: {runtime_mcp_config}')
            else:
                print('Runtime does not have get_mcp_config method')

            # Try to call MCP tool
            print('Calling MCP tool...')
            mcp_action = MCPAction(
                name='fetch', arguments={'url': 'http://httpbin.org/get'}
            )
            obs = await runtime.call_tool_mcp(mcp_action)
            print(f'MCP observation: {obs}')

        except Exception as e:
            print(f'Error: {e}')
            import traceback

            traceback.print_exc()
        finally:
            print('Closing runtime...')
            runtime.close()


if __name__ == '__main__':
    asyncio.run(debug_mcp())
