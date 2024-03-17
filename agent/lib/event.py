import os
import json
import lib.actions as actions

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
        return self.action in ['run', 'browse', 'read', 'write', 'recall']

    def run(self, memory):
        if self.action == 'run':
            cmd = self.args['command']
            return actions.run(cmd)
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
            return memory.search(self.args['query'])
        else:
            raise ValueError('Invalid action type')
