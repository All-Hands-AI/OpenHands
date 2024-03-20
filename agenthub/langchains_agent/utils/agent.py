import select

from agenthub.langchains_agent.utils.monologue import Monologue
from agenthub.langchains_agent.utils.memory import LongTermMemory
from agenthub.langchains_agent.utils.event import Event
import agenthub.langchains_agent.utils.llm as llm

MAX_OUTPUT_LENGTH = 5000
MAX_MONOLOGUE_LENGTH = 20000

class Agent:
    def __init__(self, task):
        self.task = task
        self.monologue = Monologue()
        self.memory = LongTermMemory()
        self.background_commands = []

    def add_event(self, event):
        self.monologue.add_event(event)
        self.memory.add_event(event)
        if self.monologue.get_total_length() > MAX_MONOLOGUE_LENGTH:
            self.monologue.condense()

    def get_next_action(self):
        bg_commands = [cmd.args for cmd in self.background_commands]
        action_dict = llm.request_action(self.task, self.monologue.get_thoughts(), bg_commands)
        event = Event(action_dict['action'], action_dict['args'])
        self.latest_action = event
        self.add_event(event)
        return event

    def maybe_perform_latest_action(self):
        if not (self.latest_action and self.latest_action.is_runnable()):
            return
        action = 'output'
        try:
            output = self.latest_action.run(self)
        except Exception as e:
            output = 'Error: ' + str(e)
            action = 'error'
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH] + '...'
        out_event = Event(action, {'output': output})
        self.add_event(out_event)
        return out_event

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
        self.add_event(event)
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
                event = Event('output', {'output': 'Background command %d exited with code %d' % (idx, exit_code)})
                all_events.append(event)
                self.add_event(event)

        self.background_commands = [cmd for cmd in self.background_commands if cmd.poll() is None]
        return all_events
