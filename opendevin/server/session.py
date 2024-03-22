import os
import asyncio

from fastapi import WebSocketDisconnect

import agenthub  # for the agent registry
from opendevin.agent import Agent
from opendevin.controller import AgentController
from opendevin.lib.event import Event

def parse_event(data):
    if "action" not in data:
        return None
    action = data["action"]
    args = {}
    if "args" in data:
        args = data["args"]
    message = None
    if "message" in data:
        message = data["message"]
    return Event(action, args, message)

class Session:
    def __init__(self, websocket):
        self.websocket = websocket

    async def send_error(self, message):
        await self.websocket.send_json({"error": True, "message": message})

    async def send_message(self, message):
        await self.websocket.send_json({"message": message})

    async def start_listening(self):
        try:
            while True:
                data = await self.websocket.receive_json()
                event = parse_event(data)
                if event is None:
                    await self.send_error("Invalid event")
                    continue
                print("got event", event)
                if event.action == "start":
                    await self.start_agent(event)
                else:
                    if self.controller is None:
                        await self.send_error("No agent started")
                    else:
                        await self.controller.add_user_event(event)

        except WebSocketDisconnect as e:
            print("Client websocket disconnected", e)

    async def start_agent(self, start_event):
        await self.send_message("Starting new agent...")

        if "task" not in start_event.args:
            await self.send_error("No task specified")
            return

        task = start_event.args["task"]
        directory = os.getcwd()
        if "directory" in start_event.args:
            directory = start_event.args["directory"]
        agent_cls = "LangchainsAgent"
        if "agent_cls" in start_event.args:
            agent_cls = start_event.args["agent_cls"]
        model = "gpt-4-0125-preview"
        if "model" in start_event.args:
            model = start_event.args["model"]

        AgentCls: Agent = Agent.get_cls(agent_cls)
        self.agent = AgentCls(
            instruction=task,
            workspace_dir=directory,
            model_name=model,
        )
        self.controller = AgentController(self.agent, directory, callbacks=[self.on_agent_event])
        self.agent_task = asyncio.create_task(self.controller.start_loop())

    def on_agent_event(self, event):
        evt = {
            "action": event.action,
            "message": event.get_message(),
            "args": event.args,
        }
        asyncio.create_task(self.websocket.send_json(evt))
