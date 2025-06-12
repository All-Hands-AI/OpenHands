import time

from fastapi import FastAPI, Request

from openhands.core.config import OpenHandsConfig
from openhands.runtime.prebuilt_runtime_manager import get_runtime_manager
from openhands.runtime.utils.system_stats import get_system_stats

start_time = time.time()
last_execution_time = start_time


def add_health_endpoints(app: FastAPI):
    @app.get('/alive')
    async def alive():
        return {'status': 'ok'}

    @app.get('/health')
    async def health() -> str:
        return 'OK'

    @app.get('/server_info')
    async def get_server_info():
        current_time = time.time()
        uptime = current_time - start_time
        idle_time = current_time - last_execution_time

        response = {
            'uptime': uptime,
            'idle_time': idle_time,
            'resources': get_system_stats(),
        }
        return response

    @app.get('/runtime_status')
    async def get_runtime_status():
        """Get the status of the pre-built runtime system."""
        try:
            config = OpenHandsConfig()
            runtime_manager = get_runtime_manager(config)
            status = runtime_manager.get_status()
            
            return {
                'status': 'ok',
                'runtime': status,
                'timestamp': time.time()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }

    @app.middleware('http')
    async def update_last_execution_time(request: Request, call_next):
        global last_execution_time
        response = await call_next(request)
        last_execution_time = time.time()
        return response
