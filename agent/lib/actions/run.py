import subprocess
import os

def run(cmd, agent, background=False):
    if background:
        return run_background(cmd, agent)
    result = subprocess.run(["/bin/bash", "-c", cmd], capture_output=True, text=True)
    output = result.stdout + result.stderr
    exit_code = result.returncode
    if exit_code != 0:
        raise ValueError('Command failed with exit code ' + str(exit_code) + ': ' + output)
    return output

def run_background(cmd, agent):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    agent.background_commands.append(process)
    return "Background command started. To stop it, send a `kill` action with id " + str(len(agent.background_commands) - 1)

