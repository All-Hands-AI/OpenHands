import sys
from opendevin.logger import opendevin_logger as logger
from opendevin.sandbox.docker.ssh_box import DockerSSHBox, SANDBOX_WORKSPACE_DIR
from opendevin import config
from opendevin.logger import opendevin_logger as logger
from opendevin.sandbox.sandbox import Sandbox
from opendevin.sandbox.process import Process
from opendevin.sandbox.docker.process import DockerProcess
from opendevin.sandbox.plugins import JupyterRequirement, SWEAgentCommandsRequirement
from opendevin.schema import ConfigType
from opendevin.utils import find_available_tcp_port
from opendevin.exceptions import SandboxInvalidBackgroundCommandError

class SWEBenchSSHBox(DockerSSHBox):

    def __init__(
        self,
        container_image: str | None = None,
        timeout: int = 120,
        sid: str | None = None,
        swe_instance_id: str | None = None,
    ):
        if container_image is None:
            container_image = config.get(ConfigType.SWEBENCH_CONTAINER_IMAGE)
        super().__init__(container_image, timeout, sid)
        if swe_instance_id is None:
            raise ValueError('swe_instance_id must be provided!')
        self.swe_instance_id = swe_instance_id
        # self.eval_utils_dir = eval_utils_dir
        # self.eval_utils_read_only = eval_utils_read_only

        exit_code, output = self.execute(f"echo 'export SWE_INSTANCE_ID={self.swe_instance_id}' >> ~/.bashrc")
        logger.info('exit code: %d', exit_code)
        logger.info(output)

        exit_code, output = self.execute(f'{SANDBOX_WORKSPACE_DIR}/scripts/swe_entry.sh')
        logger.info('exit code: %d', exit_code)
        logger.info(output)

        # source the bashrc
        exit_code, output = self.execute('source ~/.bashrc')
        if exit_code != 0:
            raise RuntimeError(f'Failed to source ~/.bashrc with exit code {exit_code} and output {output}')
        logger.info('Sourced ~/.bashrc successfully')

    @property
    def volumes(self):
        return {
            **super().volumes,
            # self.eval_utils_dir: {'bind': '/swe_util', 'mode': 'ro' if self.eval_utils_read_only else 'rw'},
            '/shared/bowen/codellm/swe/OD-SWE-bench': {'bind': '/OD-SWE-bench', 'mode': 'rw'},
        }


if __name__ == '__main__':
    EVAL_WORKSPACE = '/home/xingyaow/OpenDevin/evaluation/SWE-bench/eval_workspace'
    od_swe_bench_dir = f'{EVAL_WORKSPACE}/OD-SWE-bench'
    conda_envs_dir = f'{EVAL_WORKSPACE}/conda_envs'

    try:
        ssh_box = SWEBenchSSHBox(
            swe_instance_id='django__django-11099',
            # od_swe_bench_dir='/shared/bowen/codellm/swe/OD-SWE-bench',
            # conda_envs_dir='/shared/bowen/codellm/swe/temp/conda_envs'
        )
    except Exception as e:
        logger.exception('Failed to start Docker container: %s', e)
        sys.exit(1)

    logger.info(
        "Interactive Docker container started. Type 'exit' or use Ctrl+C to exit.")

    bg_cmd = ssh_box.execute_in_background(
        "while true; do echo 'dot ' && sleep 10; done"
    )

    sys.stdout.flush()
    try:
        while True:
            try:
                user_input = input('>>> ')
            except EOFError:
                logger.info('Exiting...')
                break
            if user_input.lower() == 'exit':
                logger.info('Exiting...')
                break
            if user_input.lower() == 'kill':
                ssh_box.kill_background(bg_cmd.pid)
                logger.info('Background process killed')
                continue
            exit_code, output = ssh_box.execute(user_input)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            if bg_cmd.pid in ssh_box.background_commands:
                logs = ssh_box.read_logs(bg_cmd.pid)
                logger.info('background logs: %s', logs)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.info('Exiting...')
    ssh_box.close()
