# client.py
import asyncio
import websockets

async def send_command():
    uri = "ws://localhost:8080"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                while True:
                    command = input("Enter the command to execute in the Docker container (type 'exit' to quit): ")
                    if command.lower() == 'exit':
                        return
                    await websocket.send(command)
                    response = await websocket.recv()
                    print(response)
        except (websockets.exceptions.ConnectionClosed, OSError) as e:
            print(f"Connection closed, retrying... ({str(e)})")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(send_command())

