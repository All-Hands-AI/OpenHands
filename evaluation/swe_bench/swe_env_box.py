import sys
import uuid

from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.plugins import JupyterRequirement, SWEAgentCommandsRequirement

SWE_BENCH_CONTAINER_IMAGE = 'ghcr.io/opendevin/eval-swe-bench:full-v1.0'


class SWEBenchSSHBox(DockerSSHBox):
    def __init__(
        self,
        container_image: str,
        timeout: int = 120,
        sid: str | None = None,
        swe_instance_id: str | None = None,
        swe_instance: dict | None = None,
        skip_workspace_mount: bool = True,
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
        n_tries=5,
        skip_workspace_mount: bool = True,
        workspace_mount_path: str | None = None,
    ) -> 'SWEBenchSSHBox':
        if workspace_dir_name is None:
            workspace_dir_name = f"{instance['repo']}__{instance['version']}".replace(
                '/', '__'
            )
        config.workspace_base = workspace_mount_path
        config.workspace_mount_path = workspace_mount_path
        sandbox = cls(
            container_image=SWE_BENCH_CONTAINER_IMAGE,
            swe_instance_id=instance['instance_id'],
            swe_instance=instance,
            skip_workspace_mount=skip_workspace_mount,
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
    EXAMPLE_INSTANCE = {
        'repo': 'django/django',
        'instance_id': 'django__django-11099',
        'base_commit': 'd26b2424437dabeeca94d7900b37d2df4410da0c',
        'patch': "diff --git a/django/contrib/auth/validators.py b/django/contrib/auth/validators.py\n--- a/django/contrib/auth/validators.py\n+++ b/django/contrib/auth/validators.py\n@@ -7,7 +7,7 @@\n \n @deconstructible\n class ASCIIUsernameValidator(validators.RegexValidator):\n-    regex = r'^[\\w.@+-]+$'\n+    regex = r'^[\\w.@+-]+\\Z'\n     message = _(\n         'Enter a valid username. This value may contain only English letters, '\n         'numbers, and @/./+/-/_ characters.'\n@@ -17,7 +17,7 @@ class ASCIIUsernameValidator(validators.RegexValidator):\n \n @deconstructible\n class UnicodeUsernameValidator(validators.RegexValidator):\n-    regex = r'^[\\w.@+-]+$'\n+    regex = r'^[\\w.@+-]+\\Z'\n     message = _(\n         'Enter a valid username. This value may contain only letters, '\n         'numbers, and @/./+/-/_ characters.'\n",
        'test_patch': "diff --git a/tests/auth_tests/test_validators.py b/tests/auth_tests/test_validators.py\n--- a/tests/auth_tests/test_validators.py\n+++ b/tests/auth_tests/test_validators.py\n@@ -237,7 +237,7 @@ def test_unicode_validator(self):\n         invalid_usernames = [\n             \"o'connell\", \"عبد ال\",\n             \"zerowidth\\u200Bspace\", \"nonbreaking\\u00A0space\",\n-            \"en\\u2013dash\",\n+            \"en\\u2013dash\", 'trailingnewline\\u000A',\n         ]\n         v = validators.UnicodeUsernameValidator()\n         for valid in valid_usernames:\n@@ -250,7 +250,7 @@ def test_unicode_validator(self):\n \n     def test_ascii_validator(self):\n         valid_usernames = ['glenn', 'GLEnN', 'jean-marc']\n-        invalid_usernames = [\"o'connell\", 'Éric', 'jean marc', \"أحمد\"]\n+        invalid_usernames = [\"o'connell\", 'Éric', 'jean marc', \"أحمد\", 'trailingnewline\\n']\n         v = validators.ASCIIUsernameValidator()\n         for valid in valid_usernames:\n             with self.subTest(valid=valid):\n",
        'problem_statement': "UsernameValidator allows trailing newline in usernames\nDescription\n\t\nASCIIUsernameValidator and UnicodeUsernameValidator use the regex \nr'^[\\w.@+-]+$'\nThe intent is to only allow alphanumeric characters as well as ., @, +, and -. However, a little known quirk of Python regexes is that $ will also match a trailing newline. Therefore, the user name validators will accept usernames which end with a newline. You can avoid this behavior by instead using \\A and \\Z to terminate regexes. For example, the validator regex could be changed to\nr'\\A[\\w.@+-]+\\Z'\nin order to reject usernames that end with a newline.\nI am not sure how to officially post a patch, but the required change is trivial - using the regex above in the two validators in contrib.auth.validators.\n",
        'hints_text': '',
        'created_at': '2019-03-20T03:46:18Z',
        'version': '3.0',
        'FAIL_TO_PASS': '["test_ascii_validator (auth_tests.test_validators.UsernameValidatorsTests)", "test_unicode_validator (auth_tests.test_validators.UsernameValidatorsTests)", "test_help_text (auth_tests.test_validators.UserAttributeSimilarityValidatorTest)"]',
        'PASS_TO_PASS': '["test_help_text (auth_tests.test_validators.MinimumLengthValidatorTest)", "test_validate (auth_tests.test_validators.MinimumLengthValidatorTest)", "test_help_text (auth_tests.test_validators.NumericPasswordValidatorTest)", "test_validate (auth_tests.test_validators.NumericPasswordValidatorTest)", "test_validate (auth_tests.test_validators.UserAttributeSimilarityValidatorTest)", "test_validate_property (auth_tests.test_validators.UserAttributeSimilarityValidatorTest)", "test_empty_password_validator_help_text_html (auth_tests.test_validators.PasswordValidationTest)", "test_get_default_password_validators (auth_tests.test_validators.PasswordValidationTest)", "test_get_password_validators_custom (auth_tests.test_validators.PasswordValidationTest)", "test_password_changed (auth_tests.test_validators.PasswordValidationTest)", "test_password_changed_with_custom_validator (auth_tests.test_validators.PasswordValidationTest)", "test_password_validators_help_text_html (auth_tests.test_validators.PasswordValidationTest)", "test_password_validators_help_text_html_escaping (auth_tests.test_validators.PasswordValidationTest)", "test_password_validators_help_texts (auth_tests.test_validators.PasswordValidationTest)", "test_validate_password (auth_tests.test_validators.PasswordValidationTest)", "test_help_text (auth_tests.test_validators.CommonPasswordValidatorTest)", "test_validate (auth_tests.test_validators.CommonPasswordValidatorTest)", "test_validate_custom_list (auth_tests.test_validators.CommonPasswordValidatorTest)", "test_validate_django_supplied_file (auth_tests.test_validators.CommonPasswordValidatorTest)"]',
        'environment_setup_commit': '419a78300f7cd27611196e1e464d50fd0385ff27',
    }

    sandbox = SWEBenchSSHBox.get_box_for_instance(instance=EXAMPLE_INSTANCE)

    # in actual eval, this will be initialized by the controller
    sandbox.init_plugins([JupyterRequirement(), SWEAgentCommandsRequirement()])

    # PRE TEST
    exit_code, output = sandbox.execute('cd $REPO_PATH')
    assert exit_code == 0, 'Failed to cd $REPO_PATH'
    logger.info(f'cd $REPO_PATH: {output}')

    # apply test patch
    exit_code, output = sandbox.execute('git apply $SWE_TASK_DIR/test.patch')
    assert exit_code == 0, 'Failed to apply test patch'
    logger.info(f'git apply $SWE_TASK_DIR/test.patch: {output}')

    # TEST
    exit_code, output = sandbox.execute(
        './tests/runtests.py --verbosity 2 auth_tests.test_validators'
    )
    assert exit_code == 1, 'Expected exit code 1 (since this is a FAIL_TO_PASS)'
    logger.info(f'$TEST_CMD:\n{output}')

    # apply gold patch
    exit_code, output = sandbox.execute('git apply $SWE_TASK_DIR/gold.patch')
    logger.info('exit code: %d', exit_code)
    logger.info(f'git apply $SWE_TASK_DIR/gold.patch: {output}')

    # TEST
    exit_code, output = sandbox.execute(
        './tests/runtests.py --verbosity 2 auth_tests.test_validators'
    )
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
