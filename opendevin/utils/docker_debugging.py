
#!/usr/bin/env python3
import subprocess

def check_command_availability(image, command):
    try:
        result = subprocess.run(f"docker run --rm {image} {command} --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{command} is available: {result.stdout.strip()}")
        else:
            print(f"Error finding {command}: {result.stderr.strip()}")
    except Exception as e:
        print(f"Exception when checking {command}: {str(e)}")

if __name__ == "__main__":
    image = "node:21-bullseye"
    check_command_availability(image, "node")
    check_command_availability(image, "npm")
    check_command_availability(image, "sudo")
