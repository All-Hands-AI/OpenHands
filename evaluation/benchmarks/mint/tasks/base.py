import json
import logging
import os
from abc import ABC, abstractmethod

from utils import load_file

LOGGER = logging.getLogger('MINT')


class Task(ABC):
    """Base class for a task instance."""

    task_name: str = 'base'
    in_context_example_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'in_context_examples',
    )

    def __init__(self, **kwargs) -> None:
        if 'loaded_history' in kwargs:
            self.loaded_history = kwargs['loaded_history']
        else:
            self.loaded_history = None
        # pre-load the in-context example
        task_dir = os.path.join(self.in_context_example_dir, self.task_name)
        self._in_context_example = {
            'with_tool': load_file(os.path.join(task_dir, 'with_tool.txt')),
        }
        self.metadata = {}

    @property
    def task_id(self) -> str:
        """Return the task id."""
        assert hasattr(self, '_id'), 'Task does not have an id.'
        return self._id

    def in_context_example(
        self, use_tool: bool = True, with_feedback: bool = False
    ) -> str:
        """Return the in-context example for the task."""
        if use_tool and not with_feedback:
            return self._in_context_example['with_tool']
        else:
            raise NotImplementedError

    @property
    def prompt(self) -> str:
        """Return the task prompt."""
        assert hasattr(self, '_prompt'), 'Task does not have a prompt.'
        return self._prompt

    @property
    def reference(self) -> str:
        """Return the reference solution for the task."""
        assert hasattr(self, '_reference'), 'Task does not have a reference solution.'
        return self._reference

    @abstractmethod
    def extract_answer(self, solution: str) -> str | None:
        """Extract the answer from the given solution."""
        pass

    @abstractmethod
    def success(self, solution: str) -> bool:
        """This checks whether the given solution can complete the current task.

        Can be used to provide binary feedback.
        """
        answer = self.extract_answer(solution)
        return answer == self.reference

    @classmethod
    def load_tasks(cls, path: str) -> tuple[list['Task'], int]:
        """Load all the tasks from a given jsonl file."""
        assert path.endswith('.jsonl') or path.endswith('.json')
        with open(path, 'r') as f:
            tasks = [cls(**json.loads(line)) for line in f.readlines()]
        LOGGER.info(f'Loaded {len(tasks)} tasks from {path}')
        return tasks, len(tasks)

    def to_dict(self) -> dict:
        """Convert the task to a dictionary."""
        return {
            'task_name': self.task_name,
            'task_id': self.task_id,
            'prompt': self.prompt,
            'reference': self.reference,
            'metadata': self.metadata,
        }
