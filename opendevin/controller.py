import select

from opendevin.lib.event import Event

MAX_OUTPUT_LENGTH = 5000

def print_callback(event):
    print(event, flush=True)

class AgentController:
    def __init__(self, agent, max_iterations=100, callbacks=[]):
        self.agent = agent
        self.max_iterations = max_iterations
        self.background_commands = []
        self.callbacks = callbacks
        self.callbacks.append(self.agent.add_event)
        self.callbacks.append(print_callback)

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

            action_event = self.agent.step(self)
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

    def get_background_log(self, idx, cmd, stream, name):
        logs = ""
        while True:
            readable, _, _ = select.select([stream], [], [], .1)
            if not readable:
                break
            next = stream.readline()
            if next == '':
                break
            logs += next
        if logs == "": return

        event = Event('output', {
            'output': logs,
            'stream':name,
            'id': idx,
            'command': cmd.args,
        })
        return event

    def get_background_logs(self):
        all_events = []
        for idx, cmd in enumerate(self.background_commands):
            stdout_event = self.get_background_log(idx, cmd, cmd.stdout, 'stdout')
            if stdout_event:
                all_events.append(stdout_event)
            stderr_event = self.get_background_log(idx, cmd, cmd.stderr, 'stderr')
            if stderr_event:
                all_events.append(stderr_event)

            exit_code = cmd.poll()
            if exit_code is not None:
                event = Event('output', {
                    'output': 'Background command %d exited with code %d' % (idx, exit_code),
                    'id': idx,
                    'command': cmd.args,
                })
                all_events.append(event)

        self.background_commands = [cmd for cmd in self.background_commands if cmd.poll() is None]
        return all_events
