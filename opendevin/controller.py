from opendevin.lib.event import Event

MAX_OUTPUT_LENGTH = 5000

def print_callback(event):
    print(event, flush=True)

class AgentController:
    def __init__(self, agent, max_iterations=100, callbacks=[]):
        self.agent = agent
        self.max_iterations = max_iterations
        self.callbacks = callbacks
        self.callbacks.append(self.agent.add_event)
        self.callbacks.append(print_callback)

    def get_background_logs(self):
        # TODO: move and implement
        return []

    def maybe_perform_action(self, event):
        if not (event and event.is_runnable()):
            return
        action = 'output'
        try:
            output = event.run(self)
        except Exception as e:
            output = 'Error: ' + str(e)
            action = 'error'
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH] + '...'
        out_event = Event(action, {'output': output})
        return out_event

    def start_loop(self):
        output = None
        for i in range(self.max_iterations):
            print("STEP", i, flush=True)
            log_events = self.get_background_logs()
            for event in log_events:
                for callback in self.callbacks:
                    callback(event)

            action_event = self.agent.step()
            for callback in self.callbacks:
                callback(action_event)
            if action_event.action == 'finish':
                break
            print("---", flush=True)

            output_event = self.maybe_perform_action(action_event)
            if output_event is not None:
                for callback in self.callbacks:
                    callback(output_event)
            print("==============", flush=True)

