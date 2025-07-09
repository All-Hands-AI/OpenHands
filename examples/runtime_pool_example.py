#!/usr/bin/env python3
"""
Example demonstrating Runtime Pool usage.

This example shows how to configure and use the Runtime Pool for improved performance.
"""

import asyncio
import os
import tempfile
import time

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.events.action import CmdRunAction
from openhands.runtime import get_runtime_cls
from openhands.runtime.pool import RuntimePool
from openhands.storage import get_file_store


async def main():
    """Demonstrate Runtime Pool usage."""
    print('Runtime Pool Example')
    print('=' * 50)

    # Configure runtime pooling
    os.environ['POOLED_RUNTIME_CLASS'] = 'local'
    os.environ['INITIAL_NUM_WARM_SERVERS'] = '2'
    os.environ['TARGET_NUM_WARM_SERVERS'] = '3'

    try:
        # Clear any existing pool
        RuntimePool._instance = None

        # Create configuration
        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir

            # Set up the pool (this would normally be done during app startup)
            print('Setting up Runtime Pool...')
            pool = RuntimePool.get_instance()
            pool.setup(config)

            # Wait for warm-up to complete
            time.sleep(1)
            print(f'Pool initialized with {pool.pool.qsize()} warm runtimes')

            # Create multiple runtime instances to demonstrate pooling
            runtimes = []

            for i in range(3):
                print(f'\nCreating runtime {i + 1}...')

                # Create event stream
                file_store = get_file_store(config.file_store, config.file_store_path)
                event_stream = EventStream(f'session-{i}', file_store)

                # Get pooled runtime class
                runtime_cls = get_runtime_cls('pooled')
                runtime = runtime_cls(config, event_stream)

                # Connect (gets runtime from pool)
                start_time = time.time()
                await runtime.connect()
                connect_time = time.time() - start_time

                print(f'Runtime {i + 1} connected in {connect_time:.3f}s')
                print(f'Pool size after connect: {pool.pool.qsize()}')
                print(f'Active runtimes: {len(pool.active_runtimes)}')

                runtimes.append(runtime)

            # Use the runtimes
            print('\nUsing runtimes...')
            for i, runtime in enumerate(runtimes):
                action = CmdRunAction(
                    command='echo "Hello from runtime {}"'.format(i + 1)
                )
                try:
                    observation = runtime.run(action)
                    print(f'Runtime {i + 1} output: {observation.content.strip()}')
                except Exception as e:
                    print(f'Runtime {i + 1} error: {e}')

            # Close runtimes (returns them to pool)
            print('\nClosing runtimes...')
            for i, runtime in enumerate(runtimes):
                runtime.close()
                print(f'Runtime {i + 1} closed')
                print(f'Pool size after close: {pool.pool.qsize()}')
                print(f'Active runtimes: {len(pool.active_runtimes)}')

            print(f'\nFinal pool size: {pool.pool.qsize()}')

    finally:
        # Clean up (this would normally be done during app shutdown)
        print('\nTearing down Runtime Pool...')
        pool = RuntimePool.get_instance()
        if pool.enabled:
            pool.teardown()
        RuntimePool._instance = None

        # Clean up environment
        for key in [
            'POOLED_RUNTIME_CLASS',
            'INITIAL_NUM_WARM_SERVERS',
            'TARGET_NUM_WARM_SERVERS',
        ]:
            os.environ.pop(key, None)

    print('Example completed!')


def demonstrate_without_pool():
    """Demonstrate runtime creation without pooling for comparison."""
    print('\nComparison: Runtime creation without pooling')
    print('=' * 50)

    try:
        # Ensure pool is disabled
        RuntimePool._instance = None

        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir

            # Create runtimes without pooling
            for i in range(3):
                print(f'\nCreating runtime {i + 1} (no pool)...')

                file_store = get_file_store(config.file_store, config.file_store_path)
                event_stream = EventStream(f'session-no-pool-{i}', file_store)

                # Get regular runtime class
                runtime_cls = get_runtime_cls('local')
                runtime = runtime_cls(config, event_stream)

                # Connect (creates new runtime each time)
                start_time = time.time()
                asyncio.run(runtime.connect())
                connect_time = time.time() - start_time

                print(f'Runtime {i + 1} connected in {connect_time:.3f}s')

                # Close runtime
                runtime.close()
                print(f'Runtime {i + 1} closed')

    finally:
        RuntimePool._instance = None


if __name__ == '__main__':
    asyncio.run(main())
    demonstrate_without_pool()
