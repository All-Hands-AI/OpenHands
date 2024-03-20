class AgentController:
    def __init__(self, agent, max_iterations=100, callbacks=[]):
        self.agent = agent
        self.callbacks = callbacks

    async def start_loop(self):
        output = None
        for i in range(self.max_iterations):
            action_event = await self.agent.step(output)
            for callback in self.callbacks:
                callback(action_event)
            if action.type == 'finish':
                break
            output_event = await event.execute()
            for callback in self.callbacks:
                callback(output_event)

