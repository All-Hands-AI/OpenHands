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
from typing import List, Tuple
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
        if not hasattr(self, "log_generator"):
            return ""
        logs = ""
        while True:
            ready_to_read, _, _ = select.select([self.log_generator], [], [], .1)
            if ready_to_read:
                data = self.log_generator.read(4096)
                if not data:
                    break
                # FIXME: we're occasionally seeing some escape characters like `\x02` and `\x00` in the logs...
                chunk = data.decode('utf-8')
                logs += chunk
            else:
                break
        return logs

    def execute(self, cmd: str) -> Tuple[int, str]:
        exit_code, logs = self.container.exec_run(['/bin/bash', '-c', cmd], workdir="/workspace")
        return exit_code, logs.decode('utf-8')

    def execute_in_background(self, cmd: str) -> None:
        self.log_time = time.time()
        result = self.container.exec_run(['/bin/bash', '-c', cmd], socket=True, workdir="/workspace")
        self.log_generator = result.output # socket.SocketIO
        self.log_generator._sock.setblocking(0)

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
        # FIXME: this fails because python is already shutting down. How can we clean up?
        # self.container.remove(force=True)
        pass

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
    )
    print("Interactive Docker container started. Type 'exit' or use Ctrl+C to exit.")

    bg = DockerInteractive(
        workspace_dir=args.directory,
    )
    bg.execute_in_background("while true; do echo 'dot ' && sleep 1; done")

    sys.stdout.flush()
    try:
        while True:
            try:
                user_input = input(">>> ")
            except EOFError:
                print("\nExiting...")
                break
            if user_input.lower() == "exit":
                print(f"Exiting...")
                break
            exit_code, output = docker_interactive.execute(user_input)
            print("exit code:", exit_code)
            print(output + "\n", end="")
            logs = bg.read_logs()
            print("background logs:", logs, "\n")
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nExiting...")
    docker_interactive.close()
