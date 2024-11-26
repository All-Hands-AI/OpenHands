# This file was used to create the hugging face dataset from the exercism/python
# github repo.
# Refer to: https://github.com/exercism/python/tree/main/exercises/practice

import os
from pathlib import Path

from datasets import Dataset

tests = sorted(os.listdir('practice/'))
dataset = {
    'instance_id': [],
    'instance_name': [],
    'instruction': [],
    'signature': [],
    'test': [],
}

for i, test in enumerate(tests):
    testdir = Path(f'practice/{test}/')

    dataset['instance_id'].append(i)
    dataset['instance_name'].append(testdir.name.replace('-', '_'))

    # if len(glob.glob(f'practice/{testdir.name}/*.py')) != 2:
    #     print(testdir.name)

    instructions = ''
    introduction = testdir / '.docs/introduction.md'
    if introduction.exists():
        instructions += introduction.read_text()
    instructions += (testdir / '.docs/instructions.md').read_text()
    instructions_append = testdir / '.docs/instructions.append.md'
    if instructions_append.exists():
        instructions += instructions_append.read_text()

    dataset['instruction'].append(instructions)

    signature_file = testdir / (testdir.name + '.py').replace('-', '_')
    dataset['signature'].append(signature_file.read_text())

    test_file = testdir / (testdir.name + '_test.py').replace('-', '_')
    dataset['test'].append(test_file.read_text())

ds = Dataset.from_dict(dataset)

ds.push_to_hub('RajMaheshwari/Exercism-Python')
