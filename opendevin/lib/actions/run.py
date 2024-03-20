import subprocess
import os

# TODO: put this somewhere better
background_commands = []

def run(cmd, background=False):
    if background:
        return run_background(cmd)
    result = subprocess.run(["/bin/bash", "-c", cmd], capture_output=True, text=True)
    output = result.stdout + result.stderr
    exit_code = result.returncode
    if exit_code != 0:
        raise ValueError('Command failed with exit code ' + str(exit_code) + ': ' + output)
    return output

def run_background(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    background_commands.append(process)
    return "Background command started. To stop it, send a `kill` action with id " + str(len(agent.background_commands) - 1)

def kill(id, agent):
    if id < 0 or id >= len(background_commands):
        raise ValueError('Invalid command id to kill')
    background_commands[id].kill()
    background_commands.pop(id)
    return "Background command %d killed" % id

