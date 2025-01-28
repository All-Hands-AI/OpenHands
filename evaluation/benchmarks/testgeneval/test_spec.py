from __future__ import annotations

from dataclasses import dataclass

from evaluation.benchmarks.testgeneval.constants import (
    COVERAGE_PREFIX,
    KEY_INSTANCE_ID,
    MAP_REPO_VERSION_TO_SPECS,
    TESTS_FAILED,
    TESTS_SUFFIX,
    UPDATE_TOX,
    TestGenEvalInstance,
)
from evaluation.benchmarks.testgeneval.utils import (
    get_test_directives,
)

DIFF_MODIFIED_FILE_REGEX = r'--- a/(.*)'


@dataclass
class TestSpec:
    """
    A dataclass that represents a test specification for a single instance of SWE-bench.
    """

    instance_id: str
    id: str
    repo: str
    version: str
    test_cmd: str
    code_file: str
    test_file: str
    baseline_covs: dict
    local_imports: list[str]
    test_script_list: list[str]
    mutation_script_list: list[str]

    @property
    def test_script(self):
        return (
            '\n'.join(['#!/bin/bash', 'set -uo pipefail'] + self.test_script_list)
            + '\n'
        )
        # Don't exit early because we need to revert tests at the end

    @property
    def mutation_script(self):
        return (
            '\n'.join(['#!/bin/bash', 'set -uo pipefail'] + self.mutation_script_list)
            + '\n'
        )
        # Don't exit early because we need to revert tests at the end


def make_test_setup(specs, env_name, repo_directory, includes_tox=False):
    eval_commands = []

    if includes_tox:
        eval_commands.append(UPDATE_TOX)

    eval_commands += [
        'source /opt/miniconda3/bin/activate',
        f'conda activate {env_name}',
        f'cd {repo_directory}',
    ]
    if 'eval_commands' in specs:
        eval_commands += specs['eval_commands']
    eval_commands += [
        f'git config --global --add safe.directory {repo_directory}',  # for nonroot user
        f'cd {repo_directory}',
        # This is just informational, so we have a record
        'git status',
        'git show',
        'source /opt/miniconda3/bin/activate',
        f'conda activate {env_name}',
    ]
    if 'install' in specs:
        eval_commands.append(specs['install'])

    if includes_tox:
        eval_commands.append('add_coverage_tox "tox.ini"')

    eval_commands.append('[ -f ".coveragerc" ] && rm ".coveragerc"')
    return eval_commands


def make_test_script_list(test_cmd, specs, env_name, repo_directory):
    """
    Runs the tests.
    """

    includes_tox = 'tox' in test_cmd
    eval_commands = make_test_setup(specs, env_name, repo_directory, includes_tox)
    eval_commands += [
        f'{test_cmd} || {{ echo "{TESTS_FAILED}\n{TESTS_SUFFIX}\n" && exit 1; }}',
        f'echo "{TESTS_SUFFIX}"\n',
        'coverage json -o coverage.json',
        f'echo "{COVERAGE_PREFIX}"\n',
        'cat coverage.json',
    ]

    return eval_commands


def make_mutation_script_list(specs, env_name, repo_directory, mutation_timeout):
    """
    Runs the tests.
    """

    eval_commands = make_test_setup(specs, env_name, repo_directory)
    eval_commands += [
        'cosmic-ray init mutation.toml mutation.sqlite',
        f'timeout {mutation_timeout}s cosmic-ray exec mutation.toml mutation.sqlite',
        'cr-report mutation.sqlite',
        'cr-rate mutation.sqlite  --estimate --confidence 95.0',
    ]
    return eval_commands


def make_test_spec(
    instance: TestGenEvalInstance, mutation_timeout: int, buffer: int
) -> TestSpec:
    if isinstance(instance, TestSpec):
        return instance
    instance_id = instance[KEY_INSTANCE_ID]
    id = instance['id']
    repo = instance['repo']
    version = instance['version']
    baseline_covs = instance['baseline_covs']
    code_file = instance['code_file']
    test_file = instance['test_file']
    local_imports = instance['local_imports']

    env_name = 'testbed'
    repo_directory = f'/{env_name}'
    specs = MAP_REPO_VERSION_TO_SPECS[repo][version]

    test_cmd = ' '.join(
        [
            MAP_REPO_VERSION_TO_SPECS[instance['repo']][instance['version']][
                'test_cmd'
            ],
            *get_test_directives(instance),
        ]
    )

    test_script_list = make_test_script_list(test_cmd, specs, env_name, repo_directory)

    mutation_script_list = make_mutation_script_list(
        specs, env_name, repo_directory, mutation_timeout - buffer
    )

    return TestSpec(
        instance_id=instance_id,
        id=id,
        repo=repo,
        test_script_list=test_script_list,
        test_cmd=test_cmd,
        local_imports=local_imports,
        mutation_script_list=mutation_script_list,
        code_file=code_file,
        test_file=test_file,
        baseline_covs=baseline_covs,
        version=version,
    )
