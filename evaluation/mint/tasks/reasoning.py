import logging
from typing import Optional

from tasks.base import Task

LOGGER = logging.getLogger('MINT')


class ReasoningTask(Task):
    task_name = 'reasoning'

    def __init__(self, id: str, prompt: str, reference: str, **kwargs):
        super().__init__(**kwargs)
        self._id = id
        self._prompt = prompt.strip()
        self._reference = str(reference).strip().lower()

    def extract_answer(self, solution: str) -> Optional[str]:
        """Extract the answer from the given solution."""
        return solution.lower().strip()

    def compare_w_digits(self, reference: str, answer: str) -> bool:
        """Compare the reference and answer with digits."""
        # if reference can and answer can both be converted to floats by float()
        try:
            float(reference)
            float(answer)
            return abs(float(reference) - float(answer)) <= 0.05 * abs(float(reference))
        except ValueError:
            return reference in answer
        except Exception:
            raise ValueError(f'Cannot compare {reference} and {answer}')

    def success(self, solution: str) -> bool:
        answer = self.extract_answer(solution)
        return self.compare_w_digits(self._reference, answer)


class MultipleChoiceTask(Task):
    """Subclass of Task for multiple choice tasks."""

    task_name = 'reasoning'

    def __init__(self, id, prompt: str, reference: str, **kwargs):
        super().__init__(**kwargs)
        self._id = id
        self.hide_options = kwargs.get('hide_options', False)
        if self.hide_options:
            self._prompt = prompt.split('Options:')[0].strip()
        else:
            self._prompt = prompt
        self._reference = reference.strip().lower()
        self._options = self.extract_options(prompt)
        # if all options can be converted to float, strictly perform hide options
        try:
            for option in self._options.values():
                float(option)
            self.hide_options = True
        except ValueError:
            pass
        self.metadata.update({'options': self._options})

    def extract_answer(self, solution: str) -> Optional[str]:
        # Extract the selected option from the solution
        solution = solution.lower().strip()
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            if f'{letter})' in solution or f'{letter} )' in solution:
                print('SOLUTION', letter)
                return letter
            else:
                print('SOLUTION', solution)
                return solution

    def compare_w_digits(self, reference: str, answer: str) -> bool:
        if reference.isdigit() and answer.isdigit():
            return abs(float(reference) - float(answer)) <= 0.05 * float(reference)
        else:
            return reference in answer

    def success(self, solution: str) -> bool:
        answer = self.extract_answer(solution)
        if self.compare_w_digits(self._reference, answer):
            return True
        else:
            correct_option = self._options[self._reference]
            wrong_option_list = list(self._options.values())
            print('OPTIONS', correct_option, wrong_option_list)
            print('ANSWER', answer)
            for i in wrong_option_list:
                if i in correct_option:
                    wrong_option_list.remove(i)
            for i in wrong_option_list:
                if self.compare_w_digits(i, answer) or (i in answer):
                    return False
            if self.compare_w_digits(correct_option, answer) or (
                correct_option in answer
            ):
                return True
            else:
                return False

    def extract_options(self, prompt: str) -> dict:
        # Find the possible option separators (comma, semicolon, or parentheses)
        prompt = prompt.split('Options: ')[-1]
        # Extract the options using the delimiter
        options_match = prompt.split(' , ')
        options = {}
        for i in range(len(options_match)):
            option = options_match[i].strip("[]' ")
            option = option.split(')')
            letter = option[0].lower().strip()
            content = (
                option[1]
                .lower()
                .strip('.')
                .replace('. Which option is correct?', '')
                .replace('. Which one is correct?', '')
                .strip()
            )
            options.update({letter: content})
        return options
