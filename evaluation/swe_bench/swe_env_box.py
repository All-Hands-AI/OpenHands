import sys
import uuid

from datasets import load_dataset

from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)

SWE_BENCH_CONTAINER_IMAGE = 'ghcr.io/opendevin/eval-swe-bench:full-v1.2.1'


class SWEBenchSSHBox(DockerSSHBox):
    def __init__(
        self,
        container_image: str,
        timeout: int = 120,
        sid: str | None = None,
        swe_instance_id: str | None = None,
        swe_instance: dict | None = None,
        skip_workspace_mount: bool = True,
        sandbox_plugins: list[PluginRequirement] = [],  # noqa: B006
    ):
        if swe_instance_id is None:
            raise ValueError('swe_instance_id must be provided!')
        self.swe_instance_id = swe_instance_id
        self.swe_instance = swe_instance
        self.skip_workspace_mount = skip_workspace_mount

        assert (
            container_image is not None
        ), 'container_image is required for SWEBenchSSHBox!'
        # Need to run as root to use SWEBench container
        sid = f'swe_bench_{swe_instance_id}' + str(uuid.uuid4())
        super().__init__(container_image, timeout, sid)
        self.init_plugins(sandbox_plugins)

        exit_code, output = self.execute('mv ~/.bashrc ~/.bashrc.bak')
        assert exit_code == 0, f'Failed to backup ~/.bashrc: {output}'

        exit_code, output = self.execute(
            f"echo 'export SWE_INSTANCE_ID={self.swe_instance_id}' >> ~/.bashrc && echo 'export PIP_CACHE_DIR=~/.cache/pip' >> ~/.bashrc && echo \"alias git='git --no-pager'\" >> ~/.bashrc"
        )
        assert exit_code == 0, f'Failed to set SWE_INSTANCE_ID in ~/.bashrc: {output}'

        logger.info('Sourcing swe_entry.sh to set up environment variables')
        # larger timeout for SWEBench init to account for long-running installations (e.g., require compilation)
        exit_code, output = self.execute('source /swe_util/swe_entry.sh', timeout=600)
        logger.info('exit code: %d', exit_code)
        logger.info(output)
        assert exit_code == 0, f'Failed to source swe_entry.sh: {output}'
        logger.info('Sourced swe_entry.sh successfully')

    @property
    def volumes(self):
        if self.skip_workspace_mount:
            return {
                k: v
                for k, v in super().volumes.items()
                if not v['bind'] == self.sandbox_workspace_dir
            }
        return super().volumes

    @classmethod
    def get_box_for_instance(
        cls,
        instance,
        workspace_dir_name=None,
        skip_workspace_mount: bool = True,
        workspace_mount_path: str | None = None,
        sandbox_plugins: list[PluginRequirement] = [],  # noqa: B006
    ) -> 'SWEBenchSSHBox':
        if workspace_dir_name is None:
            workspace_dir_name = f"{instance['repo']}__{instance['version']}".replace(
                '/', '__'
            )
        old_workspace_base = config.workspace_base
        old_workspace_mount_path = config.workspace_mount_path
        config.workspace_base = workspace_mount_path
        config.workspace_mount_path = workspace_mount_path

        # linting python after editing helps LLM fix indentations
        config.enable_auto_lint = True
        # Need to run as root to use SWEBench container
        config.run_as_devin = False
        sandbox = cls(
            container_image=SWE_BENCH_CONTAINER_IMAGE,
            swe_instance_id=instance['instance_id'],
            swe_instance=instance,
            skip_workspace_mount=skip_workspace_mount,
            sandbox_plugins=sandbox_plugins,
        )
        logger.info(f"SSH box started for instance {instance['instance_id']}.")

        # cd to the repo
        exit_code, output = sandbox.execute(f'cd /workspace/{workspace_dir_name}')
        if exit_code != 0:
            logger.error(f'Failed to cd to the repo: {output}')
            sys.exit(1)

        # remove all future commits & remote following Devin
        # https://www.cognition-labs.com/post/swe-bench-technical-report
        exit_code, output = sandbox.execute('git reset --hard')
        if exit_code != 0:
            logger.error(f'Failed to reset the repo: {output}')
            sys.exit(1)
        exit_code, output = sandbox.execute(
            'for remote_name in $(git remote); do git remote remove "${remote_name}"; done'
        )
        if exit_code != 0:
            logger.error(f'Failed to remove remote: {output}')
            sys.exit(1)

        # restore workspace_base and workspace_mount_path
        config.workspace_base = old_workspace_base
        config.workspace_mount_path = old_workspace_mount_path
        return sandbox

    def get_diff_patch(self):
        # add everything to the index
        exit_code, output = self.execute('git add --all')
        if exit_code != 0:
            logger.error('Failed to add everything to the index')
            return ''

        # get the git diff
        exit_code, git_patch = self.execute(
            f'git diff --no-color --cached {self.swe_instance["base_commit"]}'
        )
        if exit_code != 0:
            logger.error('Failed to get git diff')
            return ''
        return git_patch


if __name__ == '__main__':
    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    dataset = load_dataset('princeton-nlp/SWE-bench_Lite')
    swe_bench_tests = dataset['test'].to_pandas()

    # INSTANCE_ID = 'django__django-11099'
    INSTANCE_ID = 'astropy__astropy-12907'
    swe_bench_tests = swe_bench_tests[swe_bench_tests['instance_id'] == INSTANCE_ID]
    EXAMPLE_INSTANCE = swe_bench_tests.iloc[0].to_dict()

    sandbox = SWEBenchSSHBox.get_box_for_instance(
        instance=EXAMPLE_INSTANCE,
        sandbox_plugins=[AgentSkillsRequirement(), JupyterRequirement()],
    )

    # PRE TEST
    exit_code, output = sandbox.execute('cd $REPO_PATH')
    assert exit_code == 0, 'Failed to cd $REPO_PATH'
    logger.info(f'cd $REPO_PATH: {output}')

    # apply test patch
    exit_code, output = sandbox.execute('git apply $SWE_TASK_DIR/test.patch')
    assert exit_code == 0, 'Failed to apply test patch'
    logger.info(f'git apply $SWE_TASK_DIR/test.patch: {output}')

    # TEST
    exit_code, output = sandbox.execute('$TEST_CMD')
    assert exit_code == 1, 'Expected exit code 1 (since this is a FAIL_TO_PASS)'
    logger.info(f'$TEST_CMD:\n{output}')

    # apply gold patch
    exit_code, output = sandbox.execute('git apply $SWE_TASK_DIR/gold.patch')
    logger.info('exit code: %d', exit_code)
    logger.info(f'git apply $SWE_TASK_DIR/gold.patch: {output}')

    # TEST
    exit_code, output = sandbox.execute('$TEST_CMD')
    assert exit_code == 0, 'Expected exit code 0 (since we applied the gold patch)'
    logger.info(f'$TEST_CMD:\n{output}')

    # Reset the repo
    exit_code, output = sandbox.execute('git reset --hard')
    assert exit_code == 0, 'Failed to reset the repo'
    logger.info(f'git reset --hard: {output}')

    bg_cmd = sandbox.execute_in_background(
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
                sandbox.kill_background(bg_cmd.pid)
                logger.info('Background process killed')
                continue
            exit_code, output = sandbox.execute(user_input)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            if bg_cmd.pid in sandbox.background_commands:
                logs = sandbox.read_logs(bg_cmd.pid)
                logger.info('background logs: %s', logs)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.info('Exiting...')
    sandbox.close()
