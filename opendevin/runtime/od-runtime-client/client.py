# client.py, this file is used in development to test the runtime client. It is not used in production.
import asyncio
import websockets

class EventStreamRuntime:
    uri = 'ws://localhost:8080'

    def __init__(self):
        self.websocket = None
        # self.loop = asyncio.get_event_loop()
        # self.loop.run_until_complete(self._init_websocket_connect())

    # async def _init_websocket_connect(self):
    #     print("Connecting to WebSocket...")
    #     self.websocket = await websockets.connect(self.uri)
    #     print("WebSocket connected.")

    # async def connect(self):
    #     print("Connecting to WebSocket...")
    #     if self.websocket is None or self.websocket.closed:
    #         self.websocket = await websockets.connect(self.uri)
    #         if self.websocket is None:
    #             raise Exception("WebSocket is not connected.")

    async def execute(self, command):
        self.websocket = await websockets.connect(self.uri)

        print(f"Sending command: {command}")
        await self.websocket.send(command)
        print("Command sent, waiting for response...")
        try:
            output = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            print("Received output")
            print(output)
        except asyncio.TimeoutError:
            print("No response received within the timeout period.")
        
        await self.websocket.close()


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
                    exit_code = response[-1].strip()\
                    # command_output = '\n'.join(response[1:-1]).strip()
                    # print("Yufan:", command_output)
                    print("Exit Code:", exit_code)
                    print(response)
        except (websockets.exceptions.ConnectionClosed, OSError) as e:
            print(f"Connection closed, retrying... ({str(e)})")
            await asyncio.sleep(1)

# if __name__ == "__main__":
#     asyncio.run(send_command())


if __name__ == "__main__":
    runtime = EventStreamRuntime()
    asyncio.run(runtime.execute('ls -l'))
    asyncio.run(runtime.execute('pwd'))