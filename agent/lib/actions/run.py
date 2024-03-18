import subprocess

# TODO: don't hold this in global state
background_commands = []

def run(cmd, background=False):
    if background:
        process = subprocess.Popen(cmd, shell=True)
        background_commands.append(process)
        return "Background command started. To stop it, send a `kill` action with id " + str(len(background_commands) - 1)
    result = subprocess.run(["/bin/bash", "-c", cmd], capture_output=True, text=True)
    output = result.stdout + result.stderr
    exit_code = result.returncode
    if exit_code != 0:
        raise ValueError('Command failed with exit code ' + str(exit_code) + ': ' + output)
    return output

def kill(id):
    if id < 0 or id >= len(background_commands):
        return "No such background command"
    background_commands[id].kill()
    background_commands.pop(id)
    return "Background command killed"
