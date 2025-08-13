import json
from pathlib import Path
from typing import cast

from datasets import Dataset, load_dataset

from evaluation.benchmarks.testgeneval.constants import (
    KEY_INSTANCE_ID,
    TestGenEvalInstance,
)


def get_test_directives(instance: TestGenEvalInstance) -> list:
    """Get test directives from the test_patch of a task instance.

    Args:
        instance (dict): task instance
    Returns:
        directives (list): List of test directives
    """
    # For seq2seq code repos, testing command is fixed
    if instance['repo'] == 'swe-bench/humaneval':
        return ['test.py']

    # Get test directives from test patch and remove non-test files
    directives = [f'/testbed/{instance["test_file"]}']

    # For Django tests, remove extension + "tests/" prefix and convert slashes to dots (module referencing)
    if instance['repo'] == 'django/django':
        directives = [instance['test_file']]
        directives_transformed = []
        for d in directives:
            d = d[: -len('.py')] if d.endswith('.py') else d
            d = d[len('tests/') :] if d.startswith('tests/') else d
            d = d.replace('/', '.')
            directives_transformed.append(d)
        directives = directives_transformed

    return directives


def load_testgeneval_dataset(
    name='kjain14/testgeneval', split='test', ids=None
) -> list[TestGenEvalInstance]:
    """Load SWE-bench dataset from Hugging Face Datasets or local .json/.jsonl file."""
    # check that all instance IDs are in the dataset
    if ids:
        ids = set(ids)
    # Load from local .json/.jsonl file
    if name.endswith('.json') or name.endswith('.jsonl'):
        dataset = json.loads(Path(name).read_text())
        dataset_ids = {instance[KEY_INSTANCE_ID] for instance in dataset}
    else:
        # Load from Hugging Face Datasets
        if name.lower() in {'testgeneval'}:
            name = 'kjain14/testgeneval'
        elif name.lower() in {'testgeneval-lite', 'testgenevallite', 'lite'}:
            name = 'kjain14/testgenevallite'
        dataset = cast(Dataset, load_dataset(name, split=split))
        dataset_ids = {instance['id'] for instance in dataset}
    if ids:
        if ids - dataset_ids:
            raise ValueError(
                (
                    'Some instance IDs not found in dataset!'
                    f'\nMissing IDs:\n{" ".join(ids - dataset_ids)}'
                )
            )
        dataset = [instance for instance in dataset if instance['id'] in ids]
    return [cast(TestGenEvalInstance, instance) for instance in dataset]
