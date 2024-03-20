import os
import json
import agenthub.langchains_agent.utils.actions as actions

class Event:
    def __init__(self, action, args):
        self.action = action
        self.args = args

    def __str__(self):
        return self.action + " " + str(self.args)

    def to_dict(self):
        return {
            'action': self.action,
            'args': self.args
        }

    def is_runnable(self):
        return self.action in ['run', 'kill', 'browse', 'read', 'write', 'recall']

    def run(self, agent):
        if self.action == 'run':
            cmd = self.args['command']
            background = False
            if 'background' in self.args and self.args['background']:
                background = True
            return actions.run(cmd, agent, background)
        if self.action == 'kill':
            id = self.args['id']
            return actions.kill(id, agent)
        elif self.action == 'browse':
            url = self.args['url']
            return actions.browse(url)
        elif self.action == 'read':
            path = self.args['path']
            return actions.read(path)
        elif self.action == 'write':
            path = self.args['path']
            contents = self.args['contents']
            return actions.write(path, contents)
        elif self.action == 'recall':
            return agent.memory.search(self.args['query'])
        else:
            raise ValueError('Invalid action type')
