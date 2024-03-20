import subprocess
import os

def run(cmd, cmd_mgr, background=False):
    if background:
        return run_background(cmd, cmd_mgr)
    result = subprocess.run(["/bin/bash", "-c", cmd], capture_output=True, text=True)
    output = result.stdout + result.stderr
    exit_code = result.returncode
    if exit_code != 0:
        raise ValueError('Command failed with exit code ' + str(exit_code) + ': ' + output)
    return output

def run_background(cmd, cmd_mgr):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    cmd_mgr.background_commands.append(process)
    return "Background command started. To stop it, send a `kill` action with id " + str(len(cmd_mgr.background_commands) - 1)

