import logging

from utils import check_correctness

from evaluation.benchmarks.mint.tasks.base import Task

LOGGER = logging.getLogger('MINT')


class CodeGenTask(Task):
    """Generic code generation task instance."""

    def __init__(self, id: str, prompt: str, reference: str, **kwargs):
        super().__init__(**kwargs)
        self._id = id
        self._prompt = prompt
        self._reference = reference

    def success(self, solution: str) -> bool:
        """This checks whether the given solution can complete the current task.

        Can be used to provides binary feedback.
        """
        code_to_exec = self.extract_answer(solution)
        LOGGER.debug(f'CODE_TO_EXEC:\n{code_to_exec}')
        LOGGER.debug(f'TEST_CODE:\n{self._reference}')
        res = check_correctness(
            solution_code=code_to_exec, test_code=self._reference, timeout=10
        )
        return res['success']


class MBPPTask(CodeGenTask):
    task_name = 'mbpp'

    @property
    def prompt(self) -> str:
        """Return the prompt for this task.

        MBPP prompt contains \"\"\" enclosed at both ends. Need to remove it.
        """
        return self._prompt.replace('"""', '').strip()

    def extract_answer(self, solution: str) -> str | None:
        """Extract the answer from the given solution.

        Split off first block of code by scanning for class, def etc. on newlines.

        Modified from:
        https://github.com/bigcode-project/bigcode-evaluation-harness/blob/d61afde130005ecc65cf800ad8eca790a9bc2115/lm_eval/tasks/mbpp.py#L67
        """
        # STOP_WORDS = ["\nclass", "\nassert", '\n"""', "\nprint", "\nif", "\n<|/"]
        # return re.split("|".join(STOP_WORDS), solution)[0].rstrip()
        return solution


class HumanEvalTask(CodeGenTask):
    task_name = 'humaneval'

    @property
    def prompt(self) -> str:
        """Return the prompt for this task.

        MBPP prompt contains \"\"\" enclosed at both ends. Need to remove it.
        """
        return 'Complete the following code:\n\n' + self._prompt

    def extract_answer(self, solution: str) -> str | None:
        """Extract the answer from the given solution.

        Split off first block of code by scanning for class, def etc. on newlines.

        Modified from:
        https://github.com/bigcode-project/bigcode-evaluation-harness/blob/d61afde130005ecc65cf800ad8eca790a9bc2115/lm_eval/tasks/humaneval.py#L56
        """
        # STOP_WORDS = ["\nclass", "\ndef", "\n#", "\n@", "\nprint", "\nif"]
        # # Remove the last block of the code containing stop_words for HumanEval
        # string_list = re.split("(%s)" % "|".join(STOP_WORDS), solution)
        # # last string should be ""
        # return "".join(string_list[:-2])
        return solution
