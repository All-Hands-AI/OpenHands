import uvicorn
from fastapi import FastAPI, WebSocket

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ActionType
from openhands.utils.shutdown_listener import should_continue

app = FastAPI()


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # send message to mock connection
    await websocket.send_json(
        {'action': ActionType.INIT, 'message': 'Control loop started.'}
    )

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


@app.get('/')
def read_root():
    return {'message': 'This is a mock server'}


@app.get('/api/options/models')
def read_llm_models():
    return [
        'gpt-4',
        'gpt-4-turbo-preview',
        'gpt-4-0314',
        'gpt-4-0613',
    ]


@app.get('/api/options/agents')
def read_llm_agents():
    return [
        'CodeActAgent',
    ]


@app.get('/api/list-files')
def refresh_files():
    return ['hello_world.py']


@app.get('/api/options/config')
def get_config():
    return {'APP_MODE': 'oss'}


@app.get('/api/options/security-analyzers')
def get_analyzers():
    return []


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=3000)
