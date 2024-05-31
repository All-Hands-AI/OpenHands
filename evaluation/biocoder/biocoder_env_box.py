import json
import os
import sys

from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.plugins import (
    JupyterRequirement,
    PluginRequirement,
    SWEAgentCommandsRequirement,
)

BIOCODER_BENCH_CONTAINER_IMAGE = 'public.ecr.aws/i5g0m1f6/eval_biocoder:v1.0'


class BiocoderSSHBox(DockerSSHBox):
    def __init__(
        self,
        container_image: str,
        timeout: int = 120,
        sid: str | None = None,
        biocoder_instance_id: str | None = None,
        biocoder_instance: dict | None = None,
        skip_workspace_mount: bool = True,
        sandbox_plugins: list[PluginRequirement] = [],  # noqa: B006
    ):
        if biocoder_instance_id is None:
            raise ValueError('biocoder_instance_id must be provided')
        self.biocoder_instance_id = biocoder_instance_id
        self.biocoder_instance = biocoder_instance
        self.skip_workspace_mount = skip_workspace_mount

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

    def get_changed_code(self):
        # use biocoder_instance to get all data
        pass

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
        n_tries=5,
        skip_workspace_mount: bool = False,
        workspace_mount_path: str | None = None,
        sandbox_plugins: list[PluginRequirement] = [],  # noqa: B006
    ) -> 'BiocoderSSHBox':
        """This method initializes a container image, then runs some initialization commands"""
        config.workspace_base = workspace_mount_path
        config.workspace_mount_path = workspace_mount_path

        workspace_test_folder = 'biocoder_cache'
        if not os.path.exists(
            os.path.join(workspace_mount_path, workspace_test_folder)
        ):
            os.makedirs(
                os.path.join(workspace_mount_path, workspace_test_folder), exist_ok=True
            )

        file_ext = {
            'python': 'py',
            'java': 'java',
            'c': 'c',
            'cpp': 'cpp',
            'javascript': 'js',
            'typescript': 'ts',
        }[instance['language'].lower()]

        context_path = os.path.join(
            workspace_mount_path, workspace_test_folder, 'context.' + file_ext
        )
        generated_path = os.path.join(
            workspace_mount_path, workspace_test_folder, 'generated.' + file_ext
        )
        golden_path = os.path.join(
            workspace_mount_path, workspace_test_folder, 'golden.' + file_ext
        )

        with open(context_path, 'w') as f:
            f.write(instance['contextCode'])
        with open(generated_path, 'w') as f:
            f.write(instance['goldenCode'])
        with open(golden_path, 'w') as f:
            f.write(instance['goldenCode'])

        testcase_json = {
            'test_case_id': instance['test_case_id'],
            'num_cases': 1000,
            'language': instance['language'].lower(),
        }

        with open(
            os.path.join(
                workspace_mount_path, workspace_test_folder, 'testcase_biocoder.json'
            ),
            'w',
        ) as f:
            f.write(json.dumps(testcase_json, indent=4))

        # linting python after editing helps LLM fix indentations
        config.enable_auto_lint = True

        sandbox = cls(
            container_image=BIOCODER_BENCH_CONTAINER_IMAGE,
            biocoder_instance_id=instance['test_case_id'],
            biocoder_instance=instance,
            skip_workspace_mount=skip_workspace_mount,
            sandbox_plugins=sandbox_plugins,
        )

        logger.info(f"SSH box started for instance {instance['test_case_id']}.")
        # cd to the workspace
        exit_code, output = sandbox.execute_and_check(
            'cd /workspace', 'Failed to cd to workspace'
        )
        logger.info(f'cd to workspace: {output}')

        # download repository archive
        repository_url = f"https://biocoder.lilbillbiscuit.com/repos/{instance['repository'].split('/')[1]}.zip"
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
            f'cp -r /workspace/{workspace_test_folder}/ /testing_files/',
            'Failed to copy the files',
        )

        return sandbox


if __name__ == '__main__':
    EXAMPLE_INSTANCE = {
        'signature': 'def sanitize_tex(original_text)',
        'numLines': 27,
        'repository': 'pgxcentre/genipe',
        'lineEnd': 84,
        'promptSummaryOnly': 'This is in python\nwrite a function that takes in a string as an argument and returns a sanitized version of the string suitable for LaTeX formatting. The function should follow these steps:\n\n1. Replace any occurrences of four backslashes (\\\\\\\\) with the string \\\\textbackslash.\n2. Escape certain characters, including $, %, _, }, {, &, and #, by adding a backslash before them.\n3. Replace special characters such as tilde (~) with the corresponding LaTeX equivalent (e.g. $\\\\sim$).\nThe function should be named sanitize_tex and should have one argument named original_text. It should return the sanitized version of the string.',
        'content': "def sanitize_tex(original_text):\n    \"\"\"Sanitize TeX text.\n\n    Args:\n        original_text (str): the text to sanitize for LaTeX\n\n    Text is sanitized by following these steps:\n\n    1. Replaces ``\\\\\\\\`` by ``\\\\textbackslash``\n    2. Escapes certain characters (such as ``$``, ``%``, ``_``, ``}``, ``{``,\n       ``&`` and ``#``) by adding a backslash (*e.g.* from ``&`` to ``\\\\&``).\n    3. Replaces special characters such as ``~`` by the LaTeX equivalent\n       (*e.g.* from ``~`` to ``$\\\\sim$``).\n\n    \"\"\"\n    sanitized_tex = original_text.replace(\\'\\\\\\', \\'\\\\textbackslash \\')\n    sanitized_tex = re.sub(\\'([{}])\\'.format(\\'\\'.join(_escaped_char)),\n        \\'\\\\\\\\\\\\g<1>\\', sanitized_tex)\n    for character, mod in _char_mod.items():\n        sanitized_tex = sanitized_tex.replace(character, mod)\n    return sanitized_tex\n",
        'comment': 'Sanitize TeX text.\n\nArgs:\n    original_text (str): the text to sanitize for LaTeX\n\nText is sanitized by following these steps:\n\n1. Replaces ``\\\\`` by ``\\textbackslash``\n2. Escapes certain characters (such as ``$``, ``%``, ``_``, ``}``, ``{``,\n   ``&`` and ``#``) by adding a backslash (*e.g.* from ``&`` to ``\\&``).\n3. Replaces special characters such as ``~`` by the LaTeX equivalent\n   (*e.g.* from ``~`` to ``$\\sim$``).',
        'filePath': 'genipe/reporting/utils.py',
        'contextCode': "import random\nimport hashlib\nimport numpy as np\nimport skimage\nimport skimage.measure\nimport scipy.ndimage\nimport os\nimport logging\nfrom functools import wraps\nfrom scipy import stats\nimport sys\nimport math\nimport subprocess\nfrom pathlib import PurePath\nfrom itertools import islice\nimport pysam\nimport pandas as pd\nfrom scipy.signal import savgol_coeffs, savgol_filter\nfrom scipy.stats import norm\nimport re\nimport fileinput\nimport warnings\nfrom scipy.stats import scoreatpercentile, chisquare\nfrom sklearn.preprocessing import scale\nfrom sklearn.cluster import KMeans, AgglomerativeClustering\n_char_mod = {\\'~\\': \\'$\\\\sim$\\'}\n_escaped_char = [\\'$\\', \\'%\\', \\'_\\', \\'}\\', \\'{\\', \\'&\\', \\'#\\']\ndef format_time(total_seconds, written_time=False):\n    \"\"\"Format time (either \"HH:MM:SS\" or \"H hours, M minutes and S seconds\".\n    Args:\n        total_seconds (int): the total number of seconds\n        written_time (bool): whether to write time in written language\n    Returns:\n        str: a string representation of the total time\n    If ``written_time`` is ``True``, time will be displayed as \"H hours, M\n    minutes and S seconds\". Otherwise, the time will be represented as\n    HH:MM:SS.\n    \"\"\"\n    time_fmt = \\'{hours:02d}:{minutes:02d}:{seconds:02d}\\'\n    minutes, seconds = divmod(total_seconds, 60)\n    hours, minutes = divmod(minutes, 60)\n    if not written_time:\n        return time_fmt.format(seconds=seconds, minutes=minutes, hours=hours)\n    written_time = []\n    if hours > 0:\n        written_time.append(\\'{} hour{}\\'.format(hours, \\'s\\' if hours > 1 else \\'\\')\n            )\n    if minutes > 0:\n        written_time.append(\\'{} minute{}\\'.format(minutes, \\'s\\' if minutes > \n            1 else \\'\\'))\n    if seconds > 0:\n        written_time.append(\\'{} second{}\\'.format(seconds, \\'s\\' if seconds > \n            1 else \\'\\'))\n    if len(written_time) == 0:\n        return \\'no time\\'\n    if len(written_time) == 1:\n        return written_time[0]\n    return \\', \\'.join(written_time[:-1]) + \\' and \\' + written_time[-1]\ndef colorize_time(total_seconds):\n    \"\"\"Colorize the time.\n    Args:\n        total_seconds (int): the total number of seconds\n    Returns:\n        str: a colorized LaTeX string representation of time\n    The time is displayed as ``HH:MM:SS``, but insignificant zeros are\n    grayed-out.\n    \"\"\"\n    formatted_time = format_time(total_seconds)\n    colored_time = formatted_time\n    to_color = re.match(\\'([0:]+)\\', formatted_time)\n    if to_color is not None:\n        colored_time = \\'{\\\\color{light_gray}\\'\n        colored_time += formatted_time[:to_color.end()]\n        colored_time += \\'}\\' + formatted_time[to_color.end():]\n    return colored_time\n<<insert solution here>>\ndef main():\n    random.seed(<|int;range=0,100|>)\n    argString = \\'\\'.join([random.choice(_escaped_char) for _ in range(100)])\n    print(sanitize_tex(argString))\nif __name__ == \"__main__\":\n    main()\n",
        'goldenCode': "def sanitize_tex(original_text):\n    \"\"\"Sanitize TeX text.\n\n    Args:\n        original_text (str): the text to sanitize for LaTeX\n\n    Text is sanitized by following these steps:\n\n    1. Replaces ``\\\\\\\\`` by ``\\\\textbackslash``\n    2. Escapes certain characters (such as ``$``, ``%``, ``_``, ``}``, ``{``,\n       ``&`` and ``#``) by adding a backslash (*e.g.* from ``&`` to ``\\\\&``).\n    3. Replaces special characters such as ``~`` by the LaTeX equivalent\n       (*e.g.* from ``~`` to ``$\\\\sim$``).\n\n    \"\"\"\n    sanitized_tex = original_text.replace(\\'\\\\\\', \\'\\\\textbackslash \\')\n    sanitized_tex = re.sub(\\'([{}])\\'.format(\\'\\'.join(_escaped_char)),\n        \\'\\\\\\\\\\\\g<1>\\', sanitized_tex)\n    for character, mod in _char_mod.items():\n        sanitized_tex = sanitized_tex.replace(character, mod)\n    return sanitized_tex",
        'test_case_id': '61beb3529846e024cdff01d3e2ba1a1ec4212dd64426028deb1065f1975bd376',
        'lineStart': 58,
        'language': 'Python',
    }

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
        '/home/devin/mambaforge/bin/mamba run -n base python3 /testing/start_test_opendevin.py'
    )
    assert exit_code == 0, 'Expected exit code 0 (this should have passed)'
    logger.info(f'$TEST_CMD:\n{output}')

    exit_code, output = sandbox.execute_and_check(
        'cat /testing/result_biocoder.json', 'Failed to read the result file'
    )

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
