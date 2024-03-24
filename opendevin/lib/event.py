import opendevin.lib.actions as actions

ACTION_TYPES = ['initialize', 'start', 'summarize', 'run', 'kill', 'browse', 'read', 'write', 'recall', 'think', 'output', 'error', 'finish']
RUNNABLE_ACTIONS = ['run', 'kill', 'browse', 'read', 'write', 'recall']

class Event:
    def __init__(self, action, args, message=None):
        if action not in ACTION_TYPES:
            raise ValueError('Invalid action type: ' + action)
        self.action = action
        self.args = args
        self.message = message

    def __str__(self):
        return self.action + " " + str(self.args)

    def str_truncated(self, max_len=1000):
        s = str(self)
        if len(s) > max_len:
            s = s[:max_len] + '...'
        return s

    def to_dict(self):
        return {
            'action': self.action,
            'args': self.args
        }

    def get_message(self) -> str:
        if self.message is not None:
            return self.message
        if self.action == 'run':
            return 'Running command: ' + self.args['command']
        elif self.action == 'kill':
            return 'Killing command: ' + self.args['id']
        elif self.action == 'browse':
            return 'Browsing: ' + self.args['url']
        elif self.action == 'read':
            return 'Reading file: ' + self.args['path']
        elif self.action == 'write':
            return 'Writing to file: ' + self.args['path']
        elif self.action == 'recall':
            return 'Recalling memory: ' + self.args['query']
        elif self.action == 'think':
            return self.args['thought']
        elif self.action == 'output':
            return "Got output."
        elif self.action == 'error':
            return "Got an error: " + self.args['output']
        elif self.action == 'finish':
            return "Finished!"
        else:
            return ""

    def is_runnable(self):
        return self.action in RUNNABLE_ACTIONS

    def run(self, agent_controller):
        if not self.is_runnable():
            return None
        action = 'output'
        try:
            output = self._run_and_get_output(agent_controller)
        except Exception as e:
            output = 'Error: ' + str(e)
            action = 'error'
        out_event = Event(action, {'output': output})
        return out_event

    def _run_and_get_output(self, agent_controller) -> str:
        if self.action == 'run':
            cmd = self.args['command']
            background = False
            if 'background' in self.args and self.args['background']:
                background = True
            return agent_controller.command_manager.run_command(cmd, background)
        if self.action == 'kill':
            id = self.args['id']
            return agent_controller.command_manager.kill_command(id)
        elif self.action == 'browse':
            url = self.args['url']
            return actions.browse(url)
        elif self.action == 'read':
            path = self.args['path']
            return actions.read(agent_controller.command_manager.directory, path)
        elif self.action == 'write':
            path = self.args['path']
            contents = self.args['contents']
            return actions.write(agent_controller.command_manager.directory, path, contents)
        elif self.action == 'recall':
            return agent_controller.agent.search_memory(self.args['query'])
        else:
            raise ValueError('Invalid action type')
