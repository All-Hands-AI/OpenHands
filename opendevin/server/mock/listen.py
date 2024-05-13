import uvicorn
from fastapi import FastAPI, WebSocket

from opendevin.core.schema import ActionType

app = FastAPI()


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
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


@app.get('/')
def read_root():
    return {'message': 'This is a mock server'}


@app.get('/api/litellm-models')
def read_llm_models():
    return [
        'gpt-4',
        'gpt-4-turbo-preview',
        'gpt-4-0314',
        'gpt-4-0613',
    ]


@app.get('/api/agents')
def read_llm_agents():
    return [
        'MonologueAgent',
        'CodeActAgent',
        'PlannerAgent',
    ]


@app.get('/api/messages')
async def get_messages():
    return {'messages': []}


@app.get('/api/messages/total')
async def get_message_total():
    return {'msg_total': 0}


@app.get('/api/refresh-files')
def refresh_files():
    return {
        'name': 'workspace',
        'children': [
            {'name': 'hello_world.py', 'children': []},
        ],
    }


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=3000)
