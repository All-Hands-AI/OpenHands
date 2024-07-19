# echo_server.py, this file is used in development to test the runtime client. It is not used in production.
import asyncio
import websockets
import pexpect
from websockets.exceptions import ConnectionClosed
import json

def is_valid_json(s):
    try:
        json.loads(s)
    except json.JSONDecodeError:
        return False
    return True

# Function for testing websocket echo
async def echo(websocket, path):
    async for message in websocket:
        if is_valid_json(message):
            event = json.loads(message)
            print("Received:", event)
            response = json.dumps(event)  
            await websocket.send(response)
        else:
            print("Received:", message)
            response = f"Echo: {message}"
            await websocket.send(response)

start_server = websockets.serve(echo, "0.0.0.0", 8080)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
