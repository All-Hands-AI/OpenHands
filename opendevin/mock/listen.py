import uvicorn
from fastapi import FastAPI, WebSocket

from opendevin.schema import ActionType

app = FastAPI()


@app.websocket('/ws')   # type: ignore[misc]
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    # send message to mock connection
    await websocket.send_json(
        {'action': ActionType.INIT, 'message': 'Control loop started.'}
    )

    try:
        while True:
            # receive message
            data = await websocket.receive_json()
            print(f'Received message: {data}')

            # send mock response to client
            response = {'message': f'receive {data}'}
            await websocket.send_json(response)
            print(f'Sent message: {response}')
    except Exception as e:
        print(f'WebSocket Error: {e}')


@app.get('/')   # type: ignore[misc]
def read_root() -> dict[str, str]:
    return {'message': 'This is a mock server'}


@app.get('/litellm-models')   # type: ignore[misc]
def read_llm_models() -> list[str]:
    return [
        'gpt-4',
        'gpt-4-turbo-preview',
        'gpt-4-0314',
        'gpt-4-0613',
    ]


@app.get('/litellm-agents')   # type: ignore[misc]
def read_llm_agents() -> list[str]:
    return [
        'MonologueAgent',
        'CodeActAgent',
        'PlannerAgent',
    ]


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=3000)
