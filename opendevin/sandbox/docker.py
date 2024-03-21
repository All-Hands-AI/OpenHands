import os
import pty
import sys
import uuid
import time
import shlex
import select
import subprocess
import docker
import time
from typing import List
from collections import namedtuple

InputType = namedtuple("InputDtype", ["content"])
OutputType = namedtuple("OutputDtype", ["content"])

CONTAINER_IMAGE = os.getenv("SANDBOX_CONTAINER_IMAGE", "opendevin/sandbox:latest")

class DockerInteractive:

    def __init__(
        self,
        workspace_dir: str = None,
        container_image: str = None,
        timeout: int = 120,
        id: str = None
    ):
        if id is not None:
            self.instance_id: str = id
        else:
            self.instance_id: str = uuid.uuid4()
        if workspace_dir is not None:
            assert os.path.exists(workspace_dir), f"Directory {workspace_dir} does not exist."
            # expand to absolute path
            self.workspace_dir = os.path.abspath(workspace_dir)
        else:
            self.workspace_dir = os.getcwd()
            print(f"workspace unspecified, using current directory: {workspace_dir}")

        # TODO: this timeout is actually essential - need a better way to set it
        # if it is too short, the container may still waiting for previous
        # command to finish (e.g. apt-get update)
        # if it is too long, the user may have to wait for a unnecessary long time
        self.timeout: int = timeout

        if container_image is None:
            self.container_image = CONTAINER_IMAGE
        else:
            self.container_image = container_image

        self.container_name = f"sandbox-{self.instance_id}"

        self.restart_docker_container()
        uid = os.getuid()
        self.execute('useradd --shell /bin/bash -u {uid} -o -c \"\" -m devin && su devin')

    def read_logs(self) -> str:
        if not hasattr(self, "logs"):
            return ""
        logs = self.container.logs(since=self.log_time).decode("utf-8")
        self.log_time = time.time()
        return logs

    def execute(self, cmd: str) -> (int, str):
        print("execute command: ", cmd)
        exit_code, logs = self.container.exec_run(['/bin/bash', '-c', cmd], workdir="/workspace")
        return exit_code, logs.decode('utf-8')

    def execute_in_background(self, cmd: str) -> None:
        self.log_time = time.time()
        exit_code, logs = self.container.exec_run(['/bin/bash', '-c', cmd], detach=True, workdir="/workspace")

    def close(self):
        self.stop_docker_container()

    def stop_docker_container(self):
        docker_client = docker.from_env()
        try:
            container = docker_client.containers.get(self.container_name)
            container.stop()
            container.remove()
            elapsed = 0
            while container.status != "exited":
                time.sleep(1)
                elapsed += 1
                if elapsed > self.timeout:
                    break
                container = docker_client.containers.get(self.container_name)
        except docker.errors.NotFound:
            pass

    def restart_docker_container(self):
        self.stop_docker_container()
        docker_client = docker.from_env()
        try:
            self.container = docker_client.containers.run(
                    self.container_image,
                    command="tail -f /dev/null",
                    network_mode='host',
                    working_dir="/workspace",
                    name=self.container_name,
                    detach=True,
                    volumes={self.workspace_dir: {"bind": "/workspace", "mode": "rw"}})
        except Exception as e:
            print(f"Failed to start container: {e}")
            raise e

        # wait for container to be ready
        elapsed = 0
        while self.container.status != "running":
            if self.container.status == "exited":
                print("container exited")
                print("container logs:")
                print(self.container.logs())
                break
            time.sleep(1)
            elapsed += 1
            self.container = docker_client.containers.get(self.container_name)
            if elapsed > self.timeout:
                break
        if self.container.status != "running":
            raise Exception("Failed to start container")


    def __del__(self):
        self.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Interactive Docker container")
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default=None,
        help="The directory to mount as the workspace in the Docker container.",
    )
    args = parser.parse_args()

    docker_interactive = DockerInteractive(
        workspace_dir=args.directory,
        container_image="opendevin/sandbox:latest",
    )
    print("Interactive Docker container started. Type 'exit' or use Ctrl+C to exit.")

    for item in docker_interactive.history:
        print(item.content, end="")
    sys.stdout.flush()
    try:
        while True:
            try:
                user_input = input()
            except EOFError:
                print("\nExiting...")
                break
            if user_input.lower() == "exit":
                print(f"Exiting...")
                break
            output = docker_interactive.execute(user_input)
            print(output, end="")
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nExiting...")
    docker_interactive.close()
