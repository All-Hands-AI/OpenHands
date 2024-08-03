import json
import os
import sys
import tempfile
import uuid

from datasets import load_dataset
from swebench.harness.constants import MAP_REPO_TO_TEST_FRAMEWORK
from swebench.harness.utils import get_test_directives

from opendevin.core.config import AppConfig, SandboxConfig, load_app_config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)

SWE_BENCH_CONTAINER_IMAGE = 'ghcr.io/opendevin/eval-swe-bench:full-v1.2.1'


def get_image_name_from_instance_id(instance_id: str) -> str:
    return 'sweb.eval.x86_64.' + instance_id


class SWEBenchSSHBox(DockerSSHBox):
    def __init__(
        self,
        config: AppConfig,
        container_image: str,
        timeout: int = 120,
        sid: str | None = None,
        swe_instance_id: str | None = None,
        swe_instance: dict | None = None,
        skip_workspace_mount: bool = True,
        sandbox_plugins: list[PluginRequirement] = [],  # noqa: B006
        workspace_dir_name: str | None = None,
        use_instance_image: bool = False,
    ):
        if swe_instance_id is None:
            raise ValueError('swe_instance_id must be provided!')
        self.swe_instance_id = swe_instance_id
        self.swe_instance = swe_instance
        self.skip_workspace_mount = skip_workspace_mount
        self.workspace_dir_name = workspace_dir_name

        assert (
            container_image is not None
        ), 'container_image is required for SWEBenchSSHBox!'
        # Need to run as root to use SWEBench container
        sid = f'swe_bench_{swe_instance_id}_' + str(uuid.uuid4())
        logger.info(f'===Using container image: {container_image}')
        super().__init__(
            config=SandboxConfig(container_image=container_image, timeout=timeout),
            persist_sandbox=config.persist_sandbox,
            workspace_mount_path=config.workspace_mount_path,
            sandbox_workspace_dir=config.workspace_mount_path_in_sandbox,
            cache_dir=config.cache_dir,
            run_as_devin=config.run_as_devin,
            ssh_hostname=config.ssh_hostname,
            ssh_password=config.ssh_password,
            ssh_port=config.ssh_port,
            sid=sid,
        )
        self.init_plugins(sandbox_plugins)

        exit_code, output = self.execute('mv ~/.bashrc ~/.bashrc.bak')
        assert exit_code == 0, f'Failed to backup ~/.bashrc: {output}'

        exit_code, output = self.execute(
            f"echo 'export SWE_INSTANCE_ID={self.swe_instance_id}' >> ~/.bashrc && echo 'export PIP_CACHE_DIR=~/.cache/pip' >> ~/.bashrc && echo \"alias git='git --no-pager'\" >> ~/.bashrc"
        )
        assert exit_code == 0, f'Failed to set SWE_INSTANCE_ID in ~/.bashrc: {output}'

        logger.info('Sourcing swe_entry.sh to set up environment variables')
        logger.info(
            'Initialization of SWEBench may take approximately 10 minutes due to long-running installations, such as those requiring compilation.'
        )
        logger.info(f'Use instance image: {use_instance_image}')
        if use_instance_image:
            # we directly inject the instance info into the container and the init script
            script_dir = os.path.dirname(__file__)

            # inject test command
            test_type = MAP_REPO_TO_TEST_FRAMEWORK[swe_instance['repo']][
                swe_instance['version']
            ]
            swe_instance['test_directives'] = get_test_directives(swe_instance)
            swe_instance['test_cmd'] = (
                f"{test_type} {' '.join(swe_instance['test_directives'])}"
            )
            exit_code, output = self.execute(
                f"""echo "export TEST_CMD='{swe_instance["test_cmd"]}'" >> ~/.bashrc"""
            )
            # assert exit_code == 0, f'Failed to set TEST_CMD in ~/.bashrc: {output}'

            # inject the instance info
            self.execute('mkdir -p /swe_util/eval_data/instances')
            swe_instance_json_name = 'swe-bench-instance.json'
            with tempfile.TemporaryDirectory() as temp_dir:
                # Construct the full path for the desired file name within the temporary directory
                temp_file_path = os.path.join(temp_dir, swe_instance_json_name)
                # Write to the file with the desired name within the temporary directory
                with open(temp_file_path, 'w') as f:
                    if not isinstance(swe_instance, dict):
                        json.dump([swe_instance.to_dict()], f)
                    else:
                        json.dump([swe_instance], f)

                # Copy the file to the desired location
                self.copy_to(temp_file_path, '/swe_util/eval_data/instances/')

            # inject the init script
            self.copy_to(
                str(os.path.join(script_dir, 'scripts/setup/instance_swe_entry.sh')),
                '/swe_util/',
            )
            self.execute('cat ~/.bashrc')
            self.execute('source ~/.bashrc')

            self.execute('source /swe_util/instance_swe_entry.sh', timeout=600)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            assert exit_code == 0, f'Failed to source swe_entry.sh: {output}'
            logger.info('Sourced swe_entry.sh successfully')
        else:
            exit_code, output = self.execute(
                'source /swe_util/swe_entry.sh', timeout=600
            )
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
        config: AppConfig,
        instance,
        workspace_dir_name=None,
        skip_workspace_mount: bool = True,
        workspace_mount_path: str | None = None,
        sandbox_plugins: list[PluginRequirement] = [],  # noqa: B006
        use_instance_image: bool = False,
    ) -> 'SWEBenchSSHBox':
        if workspace_dir_name is None:
            workspace_dir_name = f"{instance['repo']}__{instance['version']}".replace(
                '/', '__'
            )
        old_workspace_base = config.workspace_base
        old_workspace_mount_path = config.workspace_mount_path

        try:
            config.workspace_base = workspace_mount_path
            config.workspace_mount_path = workspace_mount_path

            # linting python after editing helps LLM fix indentations
            config.sandbox.enable_auto_lint = True
            # Need to run as root to use SWEBench container
            config.run_as_devin = False
            if use_instance_image:
                container_image = get_image_name_from_instance_id(
                    instance['instance_id']
                )
            else:
                container_image = SWE_BENCH_CONTAINER_IMAGE
            sandbox = cls(
                container_image=container_image,
                config=config,
                swe_instance_id=instance['instance_id'],
                swe_instance=instance,
                skip_workspace_mount=skip_workspace_mount,
                sandbox_plugins=sandbox_plugins,
                workspace_dir_name=workspace_dir_name,
                use_instance_image=use_instance_image,
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
        except Exception:
            raise
        finally:
            # restore workspace_base and workspace_mount_path
            config.workspace_base = old_workspace_base
            config.workspace_mount_path = old_workspace_mount_path
        return sandbox

    def get_diff_patch(self):
        # add everything to the index
        exit_code, output = self.execute(f'cd /workspace/{self.workspace_dir_name}')
        if exit_code != 0:
            logger.error('Failed to cd to the repo')
            return ''

        exit_code, _output = self.execute('git config --global core.pager ""')
        if exit_code != 0:
            logger.error('Failed to change git config')
            return ''

        # add everything to the index
        exit_code, output = self.execute('git add -A')
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
    config = load_app_config()

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    dataset = load_dataset('princeton-nlp/SWE-bench_Lite')
    swe_bench_tests = dataset['test'].to_pandas()
    USE_INSTANCE_IMAGE = os.environ.get('USE_INSTANCE_IMAGE', 'false') == 'true'
    logger.info(f'USE_INSTANCE_IMAGE: {USE_INSTANCE_IMAGE}')

    # INSTANCE_ID = 'django__django-11099'
    INSTANCE_ID = 'astropy__astropy-12907'
    swe_bench_tests = swe_bench_tests[swe_bench_tests['instance_id'] == INSTANCE_ID]
    EXAMPLE_INSTANCE = swe_bench_tests.iloc[0].to_dict()

    sandbox = SWEBenchSSHBox.get_box_for_instance(
        config=config,
        instance=EXAMPLE_INSTANCE,
        sandbox_plugins=[AgentSkillsRequirement(), JupyterRequirement()],
        use_instance_image=USE_INSTANCE_IMAGE,
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
            exit_code, output = sandbox.execute(user_input)
            logger.info('exit code: %d', exit_code)
            logger.info(output)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.info('Exiting...')
    sandbox.close()
