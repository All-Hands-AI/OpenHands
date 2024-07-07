# client.py, this file is used in development to test the runtime client. It is not used in production.
import asyncio
import websockets
import pexpect
from websockets.exceptions import ConnectionClosed
import json

async def execute_command(websocket, path):
    shell = pexpect.spawn('/bin/bash', encoding='utf-8')
    shell.expect(r'[$#] ')
    
    try:
        async for message in websocket:
            try:
                print(f"Received command: {message}")
                shell.sendline(message)
                shell.expect(r'[$#] ')
                output = shell.before.strip().split('\r\n', 1)[1].strip()
                print("Yufan:",output)
                await websocket.send(output)
            except Exception as e:
                await websocket.send(f"Error: {str(e)}")
    except ConnectionClosed:
        print("Connection closed")
    finally:
        shell.close()


def is_valid_json(s):
    try:
        json.loads(s)
    except json.JSONDecodeError:
        return False
    return True

async def echo(websocket, path):
    async for message in websocket:
        if is_valid_json(message):
            event = json.loads(message)
            print("Received:", event)
            # event = "{'message': 'Running command: ls -l', 'action': 'run', 'args': {'command': 'ls -l', 'background': False, 'thought': ''}}"
            response = json.dumps(event)  
            await websocket.send(response)
        else:
            print("Received:", message)
            response = f"Echo: {message}"
            await websocket.send(response)


start_server = websockets.serve(execute_command, "0.0.0.0", 8080)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
