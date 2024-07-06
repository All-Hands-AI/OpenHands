import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass

from datasets import load_dataset

from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.plugins import (
    JupyterRequirement,
    PluginRequirement,
    SWEAgentCommandsRequirement,
)

BIOCODER_BENCH_CONTAINER_IMAGE = 'public.ecr.aws/i5g0m1f6/eval_biocoder:v1.0'


@dataclass
class BiocoderData:
    filePath: str
    numLines: int
    lineStart: int
    lineEnd: int
    signature: str
    comment: str
    content: str
    repository: str
    promptSummaryOnly: str
    contextCode: str
    goldenCode: str
    test_case_id: str
    language: str

    def to_dict(self):
        return {
            'filePath': self.filePath,
            'numLines': self.numLines,
            'lineStart': self.lineStart,
            'lineEnd': self.lineEnd,
            'signature': self.signature,
            'comment': self.comment,
            'content': self.content,
            'repository': self.repository,
            'promptSummaryOnly': self.promptSummaryOnly,
            'contextCode': self.contextCode,
            'goldenCode': self.goldenCode,
            'test_case_id': self.test_case_id,
            'language': self.language,
        }


def get_likely_indent_size(array_of_tabs) -> int:
    sizes = defaultdict(int)

    for i in range(len(array_of_tabs) - 1):
        diff = array_of_tabs[i + 1] - array_of_tabs[i]
        if diff > 0:
            sizes[diff] += 1
    if len(sizes) == 0:
        return 4
    return int(max(sizes, key=sizes.get))


class BiocoderSSHBox(DockerSSHBox):
    def __init__(
        self,
        container_image: str,
        timeout: int = 120,
        sid: str | None = None,
        biocoder_instance_id: str | None = None,
        biocoder_instance: BiocoderData | None = None,
        skip_workspace_mount: bool = True,
        sandbox_plugins: list[PluginRequirement] = [],  # noqa: B006
        biocoder_cache_folder: str = 'biocoder_cache',
        workspace_dir_name: str | None = None,
    ):
        if biocoder_instance_id is None:
            raise ValueError('biocoder_instance_id must be provided')
        self.biocoder_instance_id = biocoder_instance_id
        self.biocoder_instance = biocoder_instance
        self.skip_workspace_mount = skip_workspace_mount
        self.biocoder_cache_folder = biocoder_cache_folder
        self.first_line_after_removed = None
        self.workspace_dir_name = workspace_dir_name
        self.workspace_base = config.workspace_base
        self.workspace_mount_path = config.workspace_mount_path
        # self.workspace_dir_name_host = os.path.join(config.workspace_base, workspace_dir_name)

        self.context_path = None
        self.generated_path = None
        self.golden_path = None

        assert (
            container_image is not None
        ), 'container_image is required for BiocoderBenchSSHBox!'
        super().__init__(container_image, timeout, sid)
        self.init_plugins(sandbox_plugins)

    @property
    def volumes(self):
        if self.skip_workspace_mount:
            return {
                k: v
                for k, v in super().volumes.items()
                if not v['bind'] == self.sandbox_workspace_dir
            }
        return super().volumes

    def get_target_filepath(self):
        target_filepath = os.path.join(
            self.workspace_mount_path,
            self.biocoder_instance.repository.split('/')[1],
            self.biocoder_instance.filePath,
        )
        return target_filepath

    def get_changed_code(self, include_signature=False):
        # copies changed code into /testing_files/
        # Note that this does NOT copy the function signature
        target_filepath = self.get_target_filepath()
        selected_lines = []
        offset = 1 if include_signature else 0
        if self.first_line_after_removed is None:
            logger.warning('First line after removed is None')
        with open(target_filepath, 'r') as f:
            lines = f.read().split('\n')
            for i in range(self.biocoder_instance.lineStart - offset, len(lines)):
                if lines[i].strip() == self.first_line_after_removed.strip():
                    break
                selected_lines.append(lines[i])
        text = '\n'.join(selected_lines)
        return text

    def copy_changed_code(self):
        changed_code = self.get_changed_code(include_signature=True)
        with open(self.generated_path, 'w') as f:
            f.write(changed_code)
        exit_code, output = self.execute_and_check(
            f'cp -r /workspace/{self.biocoder_cache_folder}/* /testing_files',
            'Failed to copy the files',
        )

    def remove_code(self):
        comment_prefix = {'python': '#', 'java': '//'}

        target_filepath = self.get_target_filepath()
        line_start = self.biocoder_instance.lineStart
        line_end = self.biocoder_instance.lineEnd
        with open(target_filepath, 'r') as f:
            lines = f.read().split('\n')
            # print("="*10+"ORIGINAL"+"="*10)
            # print("\n".join(lines))
            signature_line = lines[line_start - 1]

            # get the number of tabs
            def get_indent_size(s: str):
                return len(re.match(r'\s*', s).group())

            indent_sizes = list(map(get_indent_size, lines))
            indent_size = get_likely_indent_size(indent_sizes)
            comment_indent_size = get_indent_size(signature_line) + indent_size
            lines = (
                lines[:line_start]
                + [
                    f"{' '*comment_indent_size+comment_prefix[self.biocoder_instance.language.lower()]}TODO: replace with your code here"
                ]
                + ([''] * 2)
                + lines[line_end:]
            )
        first_line_after_removed_index = line_start
        while len(
            lines[first_line_after_removed_index].strip()
        ) == 0 and first_line_after_removed_index < len(lines):
            first_line_after_removed_index += 1
        self.first_line_after_removed = lines[first_line_after_removed_index]
        # print("FIRST LINE AFTER REMOVED: ", self.first_line_after_removed)

        with open(target_filepath, 'w') as f:
            f.write('\n'.join(lines))

        # with open(target_filepath, 'r') as f:
        #     print("="*10+"MODIFIED"+"="*10)
        #     print(f.read())

    def execute_and_check(self, cmd: str, error_msg: str) -> tuple[int, str]:
        exit_code, output = self.execute(cmd)
        if exit_code != 0:
            logger.error(error_msg)
            sys.exit(1)
        return exit_code, output

    @classmethod
    def get_box_for_instance(
        cls,
        instance,
        workspace_dir_name=None,
        skip_workspace_mount: bool = False,
        workspace_mount_path: str | None = None,
        sandbox_plugins: list[PluginRequirement] = [],  # noqa: B006
    ) -> 'BiocoderSSHBox':
        """This method initializes a container image, then runs some initialization commands"""
        if workspace_dir_name is None:
            workspace_dir_name = f'{instance.repository}__{instance.test_case_id[:10]}__{os.getpid()}'.replace(
                '/', '__'
            )

        workspace_base = str(os.path.join(config.workspace_base, workspace_dir_name))
        old_workspace_base = config.workspace_base
        old_workspace_mount_path = config.workspace_mount_path

        try:
            config.workspace_base = workspace_base
            config.workspace_mount_path = workspace_base

            # linting python after editing helps LLM fix indentations
            config.enable_auto_lint = True

            # create folder for transferring files back/forth
            biocoder_cache_folder = 'biocoder_cache'
            if not os.path.exists(os.path.join(workspace_base, biocoder_cache_folder)):
                os.makedirs(
                    os.path.join(workspace_base, biocoder_cache_folder), exist_ok=True
                )

            file_ext = {
                'python': 'py',
                'java': 'java',
                'c': 'c',
                'cpp': 'cpp',
                'javascript': 'js',
                'typescript': 'ts',
            }[instance.language.lower()]

            context_path = os.path.join(
                workspace_base, biocoder_cache_folder, 'context.' + file_ext
            )
            generated_path = os.path.join(
                workspace_base, biocoder_cache_folder, 'generated.' + file_ext
            )
            golden_path = os.path.join(
                workspace_base, biocoder_cache_folder, 'golden.' + file_ext
            )

            # print(instance.contextCode)
            with open(context_path, 'w') as f:
                f.write(instance.contextCode)
            with open(generated_path, 'w') as f:
                f.write(instance.goldenCode)
            with open(golden_path, 'w') as f:
                f.write(instance.goldenCode)

            testcase_json = {
                'test_case_id': instance.test_case_id,
                'num_cases': 1000,
                'language': instance.language.lower(),
            }

            with open(
                os.path.join(
                    workspace_base, biocoder_cache_folder, 'testcase_biocoder.json'
                ),
                'w',
            ) as f:
                f.write(json.dumps(testcase_json, indent=4))

            # linting python after editing helps LLM fix indentations
            config.enable_auto_lint = True

            sandbox = cls(
                container_image=BIOCODER_BENCH_CONTAINER_IMAGE,
                biocoder_instance_id=instance.test_case_id,
                biocoder_instance=instance,
                skip_workspace_mount=skip_workspace_mount,
                sandbox_plugins=sandbox_plugins,
                biocoder_cache_folder=biocoder_cache_folder,
                workspace_dir_name=workspace_dir_name,
            )
        except Exception:
            raise
        finally:
            config.workspace_base = old_workspace_base
            config.workspace_mount_path = old_workspace_mount_path

        sandbox.context_path = context_path
        sandbox.generated_path = generated_path
        sandbox.golden_path = golden_path

        logger.info(f'SSH box started for instance {instance.test_case_id}.')
        # cd to the workspace
        exit_code, output = sandbox.execute_and_check(
            'cd /workspace', 'Failed to cd to workspace'
        )
        logger.info(f'cd to workspace: {output}')

        # download repository archive
        repository_url = f"https://biocoder.lilbillbiscuit.com/repos/{instance.repository.split('/')[1]}.zip"
        exit_code, output = sandbox.execute_and_check(
            'wget -O repo.zip ' + repository_url, 'Failed to download the repository'
        )
        logger.info(f'Downloaded the repository: {output}')
        exit_code, output = sandbox.execute_and_check(
            'unzip -o -q repo.zip', 'Failed to unzip the repository'
        )
        logger.info(f'Unzipped the repository: {output}')

        # copy the context, generated and golden files to the /testing_files folder
        exit_code, output = sandbox.execute_and_check(
            f'cp -r /workspace/{biocoder_cache_folder}/* /testing_files',
            'Failed to copy the files',
        )

        # chmod 777
        exit_code, output = sandbox.execute_and_check(
            'chmod -R 777 /workspace',
            'Failed to chmod the files',
        )

        return sandbox


if __name__ == '__main__':
    biocoder_dataset = load_dataset('Lilbillbiscuit/biocoder_public')
    EXAMPLE_INSTANCE = biocoder_dataset['test'][0]
    EXAMPLE_INSTANCE = BiocoderData(**EXAMPLE_INSTANCE)

    sandbox = BiocoderSSHBox.get_box_for_instance(
        instance=EXAMPLE_INSTANCE,
        workspace_mount_path='/home/ubuntu/OpenDevinBioCoder/workspace',
        skip_workspace_mount=False,
        sandbox_plugins=[JupyterRequirement(), SWEAgentCommandsRequirement()],
    )

    # PRE TEST
    exit_code, output = sandbox.execute_and_check(
        'cd /testing',
        'Failed to cd /testing',
    )
    logger.info(f'cd $REPO_PATH: {output}')

    exit_code, output = sandbox.execute_and_check(
        'whoami',
        'Failed to run whoami',
    )
    logger.info(f'whoami: {output}')

    # TEST
    exit_code, output = sandbox.execute(
        '/home/devin/mambaforge/bin/mamba run -n test python3 /testing/start_test_opendevin.py'
    )
    assert exit_code == 0, 'Expected exit code 0 (this should have passed)'
    logger.info(f'$TEST_CMD:\n{output}')

    exit_code, output = sandbox.execute_and_check(
        'cat /testing_files/results_biocoder.json', 'Failed to read the result file'
    )

    print(output)
    json_obj = json.loads(output)
    if json_obj['result'] == 'pass':
        print('PASS')
    else:
        print('FAIL')

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
