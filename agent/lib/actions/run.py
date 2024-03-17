import subprocess

def run(cmd):
    result = subprocess.run(["/bin/bash", "-c", cmd], capture_output=True, text=True)
    output = result.stdout + result.stderr
    exit_code = result.returncode
    if exit_code != 0:
        raise ValueError('Command failed with exit code ' + str(exit_code) + ': ' + output)
    return output

