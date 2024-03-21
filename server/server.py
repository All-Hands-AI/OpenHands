import json
import os
from time import sleep

import docker
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

app = FastAPI()

CONTAINER_NAME = "devin-agent"

AGENT_LISTEN_PORT = 8080
AGENT_BIND_PORT = os.environ.get("AGENT_PORT", 4522)
MAX_WAIT_TIME_SECONDS = 30

agent_listener = None
client_fast_websocket = None
agent_websocket = None

def get_message_payload(message):
    return {"source": "server", "message": message}

def get_error_payload(message):
    payload = get_message_payload(message)
    payload["error"] = True
    return payload

# This endpoint recieves events from the client (i.e. the browser)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global client_fast_websocket
    global agent_websocket

    await websocket.accept()
    client_fast_websocket = websocket

    try:
        while True:
            data = await websocket.receive_json()
            if "action" not in data:
                await send_message_to_client(get_error_payload("No action specified"))
                continue
            action = data["action"]
            if action == "start":
                await send_message_to_client(get_message_payload("Starting new agent..."))
                directory = os.getcwd()
                if "directory" in data:
                    directory = data["directory"]
                try:
                    await restart_docker_container(directory)
                except Exception as e:
                    print("error while restarting docker container:", e)
                    await send_message_to_client(get_error_payload("Failed to start container: " + str(e)))
                    continue

            if action == "terminal":
                msg = {
                    "action": "terminal",
                    "data": data["data"]
                }
                await send_message_to_client(get_message_payload(msg))
            else:
                if agent_websocket is None:
                    await send_message_to_client(get_error_payload("Agent not connected"))
                    continue

    except WebSocketDisconnect:
        print("Client websocket disconnected")
        await close_all_websockets(get_error_payload("Client disconnected"))

async def stop_docker_container():
    docker_client = docker.from_env()
    try:
        container = docker_client.containers.get(CONTAINER_NAME)
        container.stop()
        container.remove()
        elapsed = 0
        while container.status != "exited":
            print("waiting for container to stop...")
            sleep(1)
            elapsed += 1
            if elapsed > MAX_WAIT_TIME_SECONDS:
                break
            container = docker_client.containers.get(CONTAINER_NAME)
    except docker.errors.NotFound:
        pass

async def restart_docker_container(directory):
    await stop_docker_container()
    docker_client = docker.from_env()
    container = docker_client.containers.run(
            "jmalloc/echo-server",
            name=CONTAINER_NAME,
            detach=True,
            ports={str(AGENT_LISTEN_PORT) + "/tcp": AGENT_BIND_PORT},
            volumes={directory: {"bind": "/workspace", "mode": "rw"}})

    # wait for container to be ready
    elapsed = 0
    while container.status != "running":
        if container.status == "exited":
            print("container exited")
            print("container logs:")
            print(container.logs())
            break
        print("waiting for container to start...")
        sleep(1)
        elapsed += 1
        container = docker_client.containers.get(CONTAINER_NAME)
        if elapsed > MAX_WAIT_TIME_SECONDS:
            break
    if container.status != "running":
        raise Exception("Failed to start container")

async def listen_for_agent_messages():
    global agent_websocket
    global client_fast_websocket

    try:
        async with websockets.connect("ws://localhost:" + str(AGENT_BIND_PORT)) as ws:
            agent_websocket = ws
            await send_message_to_client(get_message_payload("Agent connected!"))
            await send_message_to_agent({"source": "server", "message": "Hello, agent!"})
            try:
                async for message in agent_websocket:
                    if client_fast_websocket is None:
                        print("Client websocket not connected")
                        await close_all_websockets(get_error_payload("Client not connected"))
                        break
                    try:
                        data = json.loads(message)
                    except Exception as e:
                        print("error parsing message from agent:", message)
                        print(e)
                        continue
                    if "source" not in data or data["source"] != "agent":
                        # TODO: remove this once we're not using echo server
                        print("echo server responded", data)
                        continue
                    await send_message_to_agent(data)
            except websockets.exceptions.ConnectionClosed:
                await send_message_to_client(get_error_payload("Agent disconnected"))
    except Exception as e:
        print("error connecting to agent:", e)
        payload = get_error_payload("Failed to connect to agent: " + str(e))
        await send_message_to_client(payload)
        await close_agent_websocket(payload)

async def send_message_to_client(data):
    print("to client:", data)
    if client_fast_websocket is None:
        return
    await client_fast_websocket.send_json(data)

async def send_message_to_agent(data):
    print("to agent:", data)
    if agent_websocket is None:
        return
    await agent_websocket.send(json.dumps(data))

async def close_agent_websocket(payload):
    global agent_websocket
    if agent_websocket is not None:
        if not agent_websocket.closed:
            await send_message_to_agent(payload)
            await agent_websocket.close()
        agent_websocket = None
    await stop_docker_container()

async def close_client_websocket(payload):
    global client_fast_websocket
    if client_fast_websocket is not None:
        if client_fast_websocket.client_state != WebSocketState.DISCONNECTED:
            await send_message_to_client(payload)
            await client_fast_websocket.close()
    client_fast_websocket = None

async def close_all_websockets(payload):
    await close_agent_websocket(payload)
    await close_client_websocket(payload)
