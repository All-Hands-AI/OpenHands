import copy
import os
import tarfile
from glob import glob

from e2b_code_interpreter import Sandbox
from e2b.exceptions import TimeoutException

from openhands.core.config import SandboxConfig
from openhands.core.logger import openhands_logger as logger


class E2BBox:
    closed = False
    _cwd: str = "/home/user"
    _env: dict[str, str] = {}
    is_initial_session: bool = True

    def __init__(
        self,
        config: SandboxConfig,
        sandbox_id: str | None = None,
    ):
        self.config = copy.deepcopy(config)
        self.initialize_plugins: bool = config.initialize_plugins

        # Read API key from environment variable
        e2b_api_key = os.getenv("E2B_API_KEY")
        if not e2b_api_key:
            raise ValueError(
                "E2B_API_KEY environment variable is required for E2B runtime"
            )
        
        # Read custom E2B domain if provided
        e2b_domain = os.getenv("E2B_DOMAIN")
        if e2b_domain:
            logger.info(f'Using custom E2B domain: {e2b_domain}')

        # E2B v2 requires using create() method or connect to existing
        try:
            # Configure E2B client with custom domain if provided
            create_kwargs = {}
            connect_kwargs = {}
            
            if e2b_domain:
                # Set up custom domain configuration
                # Note: This depends on E2B SDK version and may need adjustment
                os.environ['E2B_API_URL'] = f'https://{e2b_domain}'
                logger.info(f'Set E2B_API_URL to https://{e2b_domain}')
            
            if sandbox_id:
                # Connect to existing sandbox
                self.sandbox = Sandbox.connect(sandbox_id, **connect_kwargs)
                logger.info(f'Connected to existing E2B sandbox with ID "{sandbox_id}"')
            else:
                # Create new sandbox (e2b-code-interpreter doesn't need template)
                self.sandbox = Sandbox.create(**create_kwargs)
                sandbox_id = self.sandbox.sandbox_id
                logger.info(f'Created E2B sandbox with ID "{sandbox_id}"')
        except Exception as e:
            logger.error(f"Failed to create/connect E2B sandbox: {e}")
            raise

    @property
    def filesystem(self):
        # E2B v2 uses 'files' instead of 'filesystem'
        return getattr(self.sandbox, 'files', None) or getattr(self.sandbox, 'filesystem', None)

    def _archive(self, host_src: str, recursive: bool = False):
        if recursive:
            assert os.path.isdir(host_src), (
                "Source must be a directory when recursive is True"
            )
            files = glob(host_src + "/**/*", recursive=True)
            srcname = os.path.basename(host_src)
            tar_filename = os.path.join(os.path.dirname(host_src), srcname + ".tar")
            with tarfile.open(tar_filename, mode="w") as tar:
                for file in files:
                    tar.add(
                        file, arcname=os.path.relpath(file, os.path.dirname(host_src))
                    )
        else:
            assert os.path.isfile(host_src), (
                "Source must be a file when recursive is False"
            )
            srcname = os.path.basename(host_src)
            tar_filename = os.path.join(os.path.dirname(host_src), srcname + ".tar")
            with tarfile.open(tar_filename, mode="w") as tar:
                tar.add(host_src, arcname=srcname)
        return tar_filename

    def execute(self, cmd: str, timeout: int | None = None) -> tuple[int, str]:
        timeout = timeout if timeout is not None else self.config.timeout
        
        # E2B code-interpreter uses commands.run()
        try:
            result = self.sandbox.commands.run(cmd)
            output = ""
            if hasattr(result, 'stdout') and result.stdout:
                output += result.stdout
            if hasattr(result, 'stderr') and result.stderr:
                output += result.stderr
            exit_code = getattr(result, 'exit_code', 0) or 0
            return exit_code, output
        except TimeoutException:
            logger.debug("Command timed out")
            return -1, f'Command: "{cmd}" timed out'
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return -1, str(e)

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        """Copies a local file or directory to the sandbox."""
        tar_filename = self._archive(host_src, recursive)

        # Prepend the sandbox destination with our sandbox cwd
        sandbox_dest = os.path.join(self._cwd, sandbox_dest.removeprefix("/"))

        with open(tar_filename, "rb") as tar_file:
            # Upload the archive to /home/user (default destination that always exists)
            uploaded_path = self.sandbox.upload_file(tar_file)

            # Check if sandbox_dest exists. If not, create it.
            exit_code, _ = self.execute(f"test -d {sandbox_dest}")
            if exit_code != 0:
                self.execute(f"mkdir -p {sandbox_dest}")

            # Extract the archive into the destination and delete the archive
            exit_code, output = self.execute(
                f"sudo tar -xf {uploaded_path} -C {sandbox_dest} && sudo rm {uploaded_path}"
            )
            if exit_code != 0:
                raise Exception(
                    f"Failed to extract {uploaded_path} to {sandbox_dest}: {output}"
                )

        # Delete the local archive
        os.remove(tar_filename)

    def close(self):
        # E2B v2 uses kill() instead of close()
        if hasattr(self.sandbox, 'kill'):
            self.sandbox.kill()
        elif hasattr(self.sandbox, 'close'):
            self.sandbox.close()

    def get_working_directory(self):
        return self.sandbox.cwd


# Alias for backward compatibility
E2BSandbox = E2BBox
