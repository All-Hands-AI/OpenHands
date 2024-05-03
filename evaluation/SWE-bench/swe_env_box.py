import sys

from opendevin.core.logger import opendevin_logger as logger
from opendevin.runtime.docker.ssh_box import DockerSSHBox


class SWEBenchSSHBox(DockerSSHBox):
    def __init__(
        self,
        container_image: str,
        timeout: int = 120,
        sid: str | None = None,
        swe_instance_id: str | None = None,
    ):
        assert (
            container_image is not None
        ), 'container_image is required for SWEBenchSSHBox!'
        # Need to run as root to use SWEBench container
        super().__init__(container_image, timeout, sid, run_as_devin=False)

        if swe_instance_id is None:
            raise ValueError('swe_instance_id must be provided!')
        self.swe_instance_id = swe_instance_id

        exit_code, output = self.execute('mv ~/.bashrc ~/.bashrc.bak')
        assert exit_code == 0, f'Failed to backup ~/.bashrc: {output}'
        exit_code, output = self.execute(
            f"echo 'export SWE_INSTANCE_ID={self.swe_instance_id}' >> ~/.bashrc"
        )
        assert exit_code == 0, f'Failed to set SWE_INSTANCE_ID in ~/.bashrc: {output}'

        logger.info('Sourcing swe_entry.sh to set up environment variables')
        exit_code, output = self.execute('source /swe_util/swe_entry.sh')
        logger.info('exit code: %d', exit_code)
        logger.info(output)
        assert exit_code == 0, f'Failed to source swe_entry.sh: {output}'
        logger.info('Sourced swe_entry.sh successfully')

    @property
    def volumes(self):
        return {**super().volumes}


if __name__ == '__main__':
    CONTAINER_IMAGE = 'ghcr.io/xingyaoww/eval-swe-bench-all:lite-v1.0'
    try:
        ssh_box = SWEBenchSSHBox(
            container_image=CONTAINER_IMAGE, swe_instance_id='django__django-11099'
        )
    except Exception as e:
        logger.exception('Failed to start Docker container: %s', e)
        sys.exit(1)
    # ssh_box.init_plugins([JupyterRequirement(), SWEAgentCommandsRequirement()])

    logger.info(
        "Interactive Docker container started. Type 'exit' or use Ctrl+C to exit."
    )

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
