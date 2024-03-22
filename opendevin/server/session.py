import os
import asyncio

from fastapi import WebSocketDisconnect

import agenthub  # for the agent registry
from opendevin.agent import Agent
from opendevin.controller import AgentController

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
                if "action" not in data:
                    await self.send_error("No action specified")
                    continue
                action = data["action"]
                if action == "start":
                    await self.start_agent(data)
                elif action == "terminal":
                    await self.terminal_data(data)
                else:
                    await self.send_error("Invalid action")

        except WebSocketDisconnect as e:
            print("Client websocket disconnected", e)

    async def start_agent(self, data):
        await self.send_message("Starting new agent...")

        if "task" not in data:
            await self.send_error("No task specified")
            return

        task = data["task"]
        directory = os.getcwd()
        if "directory" in data:
            directory = data["directory"]
        agent_cls = "LangchainsAgent"
        if "agent_cls" in data:
            agent_cls = data["agent_cls"]
        model = "gpt-4-0125-preview"
        if "model" in data:
            model = data["model"]

        AgentCls: Agent = Agent.get_cls(agent_cls)
        self.agent = AgentCls(
            instruction=task,
            workspace_dir=directory,
            model_name=model,
        )
        self.controller = AgentController(self.agent, directory, callbacks=[self.on_agent_event])
        self.agent_task = asyncio.create_task(self.controller.start_loop())

    async def terminal_data(self, data):
        await self.send_error("Not implemented yet")

    def on_agent_event(self, event):
        # FIXME: messages aren't sent until the loop finishes...
        evt = {
            "action": event.action,
            "message": event.get_message(),
            "args": event.args,
        }
        asyncio.create_task(self.websocket.send_json(evt))
