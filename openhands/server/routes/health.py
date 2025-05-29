import time

from fastapi import FastAPI, Request

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

    @app.middleware('http')
    async def update_last_execution_time(request: Request, call_next):
        global last_execution_time
        response = await call_next(request)
        last_execution_time = time.time()
        return response
