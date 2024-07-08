# client.py, this file is used in development to test the runtime client. It is not used in production.
import asyncio
import websockets

# Function for sending commands to the server in EventStreamRuntime
class EventStreamRuntime:
    uri = 'ws://localhost:8080'

    def __init__(self):
        self.websocket = None

    def _init_websocket(self):
        self.websocket = None
        # TODO: need to initialization globally only once
        # self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(self.loop)
        # self.loop.run_until_complete(self._init_websocket_connect())
    
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

# Function for testing sending commands to the server
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

if __name__ == "__main__":
    asyncio.run(send_command())


# if __name__ == "__main__":
#     runtime = EventStreamRuntime()
#     asyncio.run(runtime.execute('ls -l'))
#     asyncio.run(runtime.execute('pwd'))