import uvicorn
from fastapi import FastAPI, WebSocket

from openhands.core.logger import openhands_logger as logger
from openhands.utils.shutdown_listener import should_continue

app = FastAPI()


@app.websocket('/ws')  # type: ignore
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        while should_continue():
            # receive message
            data = await websocket.receive_json()
            logger.debug(f'Received message: {data}')

            # send mock response to client
            response = {'message': f'receive {data}'}
            await websocket.send_json(response)
            logger.debug(f'Sent message: {response}')
    except Exception as e:
        logger.debug(f'WebSocket Error: {e}')


@app.get('/')  # type: ignore
def read_root() -> dict[str, str]:
    return {'message': 'This is a mock server'}


@app.get('/api/options/models')  # type: ignore
def read_llm_models() -> list[str]:
    return [
        'gpt-4',
        'gpt-4-turbo-preview',
        'gpt-4-0314',
        'gpt-4-0613',
    ]


@app.get('/api/options/agents')  # type: ignore
def read_llm_agents() -> list[str]:
    return [
        'CodeActAgent',
    ]


@app.get('/api/list-files')  # type: ignore
def refresh_files() -> list[str]:
    return ['hello_world.py']


@app.get('/api/options/config')  # type: ignore
def get_config() -> dict[str, str]:
    return {'APP_MODE': 'oss'}


@app.get('/api/options/security-analyzers')  # type: ignore
def get_analyzers() -> list[str]:
    return []


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=3000)
