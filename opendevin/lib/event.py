import os
import json
import opendevin.lib.actions as actions

ACTION_TYPES = ['run', 'kill', 'browse', 'read', 'write', 'recall', 'think', 'output', 'error', 'finish']
RUNNABLE_ACTIONS = ['run', 'kill', 'browse', 'read', 'write', 'recall']

class Event:
    def __init__(self, action, args):
        if action not in ACTION_TYPES:
            raise ValueError('Invalid action type: ' + action)
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
        return self.action in RUNNABLE_ACTIONS

    def run(self, agent_controller):
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
