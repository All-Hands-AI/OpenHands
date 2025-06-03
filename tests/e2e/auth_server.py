import uvicorn
from fastapi import FastAPI, Request

# Configuration
app = FastAPI()


@app.get('/api/users/detail')
async def user_detail(request: Request):
    headers = request.headers
    bearer_token = headers.get('Authorization')
    return {
        'msg': 'success',
        'user': {
            'id': bearer_token.split(' ')[1],
            'publicAddress': bearer_token.split(' ')[1],
            'status': 1,
            'whitelisted': 1,
            'solanaThesisAddress': '0x11A87E9d573597d5A4271272df09C1177F34bEbC',
            'ethThesisAddress': '0x11A87E9d573597d5A4271272df09C1177F34bEbC',
            'mnemonic': '',
        },
    }


@app.post('/api/users/login')
async def login(request: Request):
    payload = await request.json()
    print(payload)
    return {
        'msg': 'success',
        'token': 'tokenJwt',
        'user': {
            'id': payload['publicAddress'],
            'publicAddress': payload['publicAddress'],
        },
    }


@app.post('/api/threads')
async def create_thread(request: Request):
    payload = await request.json()
    print(payload)
    return {'msg': 'success'}


@app.post('/api/knowledge/search')
async def search_knowledge(request: Request):
    payload = await request.json()
    print(payload)
    return {'msg': 'success'}


@app.post('/api/threads/webhook/rag-job')
async def rag_job(request: Request):
    payload = await request.json()
    print(payload)
    return {'msg': 'success'}


@app.post('/api/threads/delete-thread-by-conversation-id/{conversation_id}')
async def delete_thread(request: Request, conversation_id: str):
    payload = await request.json()
    print(payload)
    return {'msg': 'success'}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)
