import os
import unittest

from opendevin.indexing.repomap.repomap import RepoMap
from opendevin.indexing.repomap.utils import IgnorantTemporaryDirectory
from opendevin.llm.llm import LLM


class TestRepoMap(unittest.TestCase):
    def setUp(self):
        self.GPT35 = LLM('gpt-3.5-turbo')

    def test_get_repo_map(self):
        # Create a temporary directory with sample files for testing
        test_files = [
            'test_file1.py',
            'test_file2.py',
            'test_file3.md',
            'test_file4.json',
        ]

        with IgnorantTemporaryDirectory() as temp_dir:
            for file in test_files:
                with open(os.path.join(temp_dir, file), 'w') as f:
                    f.write('')

            repo_map = RepoMap(llm=self.GPT35, root=temp_dir)
            other_files = [os.path.join(temp_dir, file) for file in test_files]
            result = repo_map.get_repo_map([], other_files)

            # Check if the result contains the expected tags map
            self.assertIn('test_file1.py', result)
            self.assertIn('test_file2.py', result)
            self.assertIn('test_file3.md', result)
            self.assertIn('test_file4.json', result)

            # close the open cache files, so Windows won't error
            del repo_map

    def test_get_repo_map_with_identifiers(self):
        # Create a temporary directory with a sample Python file containing identifiers
        test_file1 = 'test_file_with_identifiers.py'
        file_content1 = """\
class MyClass:
    def my_method(self, arg1, arg2):
        return arg1 + arg2

def my_function(arg1, arg2):
    return arg1 * arg2
"""

        test_file2 = 'test_file_import.py'
        file_content2 = """\
from test_file_with_identifiers import MyClass

obj = MyClass()
print(obj.my_method(1, 2))
print(my_function(3, 4))
"""

        test_file3 = 'test_file_pass.py'
        file_content3 = 'pass'

        with IgnorantTemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, test_file1), 'w') as f:
                f.write(file_content1)

            with open(os.path.join(temp_dir, test_file2), 'w') as f:
                f.write(file_content2)

            with open(os.path.join(temp_dir, test_file3), 'w') as f:
                f.write(file_content3)

            repo_map = RepoMap(llm=self.GPT35, root=temp_dir)
            other_files = [
                os.path.join(temp_dir, test_file1),
                os.path.join(temp_dir, test_file2),
                os.path.join(temp_dir, test_file3),
            ]
            result = repo_map.get_repo_map([], other_files)

            # Check if the result contains the expected tags map with identifiers
            self.assertIn('test_file_with_identifiers.py', result)
            self.assertIn('MyClass', result)
            self.assertIn('my_method', result)
            self.assertIn('my_function', result)
            self.assertIn('test_file_pass.py', result)

            # close the open cache files, so Windows won't error
            del repo_map

    def test_get_repo_map_all_files(self):
        test_files = [
            'test_file0.py',
            'test_file1.txt',
            'test_file2.md',
            'test_file3.json',
            'test_file4.html',
            'test_file5.css',
            'test_file6.js',
        ]

        with IgnorantTemporaryDirectory() as temp_dir:
            for file in test_files:
                with open(os.path.join(temp_dir, file), 'w') as f:
                    f.write('')

            repo_map = RepoMap(llm=self.GPT35, root=temp_dir)

            other_files = [os.path.join(temp_dir, file) for file in test_files]
            result = repo_map.get_repo_map([], other_files)

            # Check if the result contains each specific file in the expected tags map without ctags
            for file in test_files:
                self.assertIn(file, result)

            # close the open cache files, so Windows won't error
            del repo_map

    def test_get_repo_map_excludes_added_files(self):
        # Create a temporary directory with sample files for testing
        test_files = [
            'test_file1.py',
            'test_file2.py',
            'test_file3.md',
            'test_file4.json',
        ]

        with IgnorantTemporaryDirectory() as temp_dir:
            for file in test_files:
                with open(os.path.join(temp_dir, file), 'w') as f:
                    f.write('def foo(): pass\n')

            repo_map = RepoMap(llm=self.GPT35, root=temp_dir)
            test_files = [os.path.join(temp_dir, file) for file in test_files]
            result = repo_map.get_repo_map(test_files[:2], test_files[2:])

            # Check if the result contains the expected tags map
            self.assertNotIn('test_file1.py', result)
            self.assertNotIn('test_file2.py', result)
            self.assertIn('test_file3.md', result)
            self.assertIn('test_file4.json', result)

            # close the open cache files, so Windows won't error
            del repo_map


class TestRepoMapTypescript(unittest.TestCase):
    def setUp(self):
        self.GPT35 = LLM('gpt-3.5-turbo')

    def test_get_repo_map_typescript(self):
        # Create a temporary directory with a sample TypeScript file
        test_file_ts = 'test_file.ts'
        file_content_ts = """\
interface IMyInterface {
    someMethod(): void;
}

type ExampleType = {
    key: string;
    value: number;
};

enum Status {
    New,
    InProgress,
    Completed,
}

export class MyClass {
    constructor(public value: number) {}

    add(input: number): number {
        return this.value + input;
        return this.value + input;
    }
}

export function myFunction(input: number): number {
    return input * 2;
}
"""

        with IgnorantTemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, test_file_ts), 'w') as f:
                f.write(file_content_ts)

            repo_map = RepoMap(llm=self.GPT35, root=temp_dir)
            other_files = [os.path.join(temp_dir, test_file_ts)]
            result = repo_map.get_repo_map([], other_files)

            # Check if the result contains the expected tags map with TypeScript identifiers
            self.assertIn('test_file.ts', result)
            self.assertIn('IMyInterface', result)
            self.assertIn('ExampleType', result)
            self.assertIn('Status', result)
            self.assertIn('MyClass', result)
            self.assertIn('add', result)
            self.assertIn('myFunction', result)

            # close the open cache files, so Windows won't error
            del repo_map


if __name__ == '__main__':
    unittest.main()
