# execute_server.py, this file is used in development to test the runtime client. It is not used in production.
import asyncio
import websockets
import pexpect
from websockets.exceptions import ConnectionClosed
import json

# Function for testing execution of shell commands
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


start_server = websockets.serve(execute_command, "0.0.0.0", 8080)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
