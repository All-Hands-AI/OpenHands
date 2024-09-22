import abc
import difflib
import logging
import platform
from copy import deepcopy
from dataclasses import asdict, dataclass
from textwrap import dedent
from typing import Literal, Union
from warnings import warn

from browsergym.core.action.base import AbstractActionSet
from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.core.action.python import PythonActionSet

from agenthub.browsing_agent.utils import (
    ParseError,
    parse_html_tags_raise,
)
from openhands.runtime.browser.browser_env import BrowserEnv


@dataclass
class Flags:
    use_html: bool = True
    use_ax_tree: bool = False
    drop_ax_tree_first: bool = True  # This flag is no longer active TODO delete
    use_thinking: bool = False
    use_error_logs: bool = False
    use_past_error_logs: bool = False
    use_history: bool = False
    use_action_history: bool = False
    use_memory: bool = False
    use_diff: bool = False
    html_type: str = 'pruned_html'
    use_concrete_example: bool = True
    use_abstract_example: bool = False
    multi_actions: bool = False
    action_space: Literal[
        'python', 'bid', 'coord', 'bid+coord', 'bid+nav', 'coord+nav', 'bid+coord+nav'
    ] = 'bid'
    is_strict: bool = False
    # This flag will be automatically disabled `if not chat_model_args.has_vision()`
    use_screenshot: bool = True
    enable_chat: bool = False
    max_prompt_tokens: int = 100_000
    extract_visible_tag: bool = False
    extract_coords: Literal['False', 'center', 'box'] = 'False'
    extract_visible_elements_only: bool = False
    demo_mode: Literal['off', 'default', 'only_visible_elements'] = 'off'

    def copy(self):
        return deepcopy(self)

    def asdict(self):
        """Helper for JSON serializble requirement."""
        return asdict(self)

    @classmethod
    def from_dict(self, flags_dict):
        """Helper for JSON serializable requirement."""
        if isinstance(flags_dict, Flags):
            return flags_dict

        if not isinstance(flags_dict, dict):
            raise ValueError(
                f'Unregcognized type for flags_dict of type {type(flags_dict)}.'
            )
        return Flags(**flags_dict)


class PromptElement:
    """Base class for all prompt elements. Prompt elements can be hidden.

    Prompt elements are used to build the prompt. Use flags to control which
    prompt elements are visible. We use class attributes as a convenient way
    to implement static prompts, but feel free to override them with instance
    attributes or @property decorator.
    """

    _prompt = ''
    _abstract_ex = ''
    _concrete_ex = ''

    def __init__(self, visible: bool = True) -> None:
        """Prompt element that can be hidden.

        Parameters
        ----------
        visible : bool, optional
            Whether the prompt element should be visible, by default True. Can
            be a callable that returns a bool. This is useful when a specific
            flag changes during a shrink iteration.
        """
        self._visible = visible

    @property
    def prompt(self):
        """Avoid overriding this method. Override _prompt instead."""
        return self._hide(self._prompt)

    @property
    def abstract_ex(self):
        """Useful when this prompt element is requesting an answer from the llm.
        Provide an abstract example of the answer here. See Memory for an
        example.

        Avoid overriding this method. Override _abstract_ex instead
        """
        return self._hide(self._abstract_ex)

    @property
    def concrete_ex(self):
        """Useful when this prompt element is requesting an answer from the llm.
        Provide a concrete example of the answer here. See Memory for an
        example.

        Avoid overriding this method. Override _concrete_ex instead
        """
        return self._hide(self._concrete_ex)

    @property
    def is_visible(self):
        """Handle the case where visible is a callable."""
        visible = self._visible
        if callable(visible):
            visible = visible()
        return visible

    def _hide(self, value):
        """Return value if visible is True, else return empty string."""
        if self.is_visible:
            return value
        else:
            return ''

    def _parse_answer(self, text_answer) -> dict:
        if self.is_visible:
            return self._parse_answer(text_answer)
        else:
            return {}


class Shrinkable(PromptElement, abc.ABC):
    @abc.abstractmethod
    def shrink(self) -> None:
        """Implement shrinking of this prompt element.

        You need to recursively call all shrinkable elements that are part of
        this prompt. You can also implement a shrinking strategy for this prompt.
        Shrinking is can be called multiple times to progressively shrink the
        prompt until it fits max_tokens. Default max shrink iterations is 20.
        """
        pass


class Truncater(Shrinkable):
    """A prompt element that can be truncated to fit the context length of the LLM.
    Of course, it will be great that we never have to use the functionality here to `shrink()` the prompt.
    Extend this class for prompt elements that can be truncated. Usually long observations such as AxTree or HTML.
    """

    def __init__(self, visible, shrink_speed=0.3, start_truncate_iteration=10):
        super().__init__(visible=visible)
        self.shrink_speed = shrink_speed  # the percentage shrunk in each iteration
        self.start_truncate_iteration = (
            start_truncate_iteration  # the iteration to start truncating
        )
        self.shrink_calls = 0
        self.deleted_lines = 0

    def shrink(self) -> None:
        if self.is_visible and self.shrink_calls >= self.start_truncate_iteration:
            # remove the fraction of _prompt
            lines = self._prompt.splitlines()
            new_line_count = int(len(lines) * (1 - self.shrink_speed))
            self.deleted_lines += len(lines) - new_line_count
            self._prompt = '\n'.join(lines[:new_line_count])
            self._prompt += (
                f'\n... Deleted {self.deleted_lines} lines to reduce prompt size.'
            )

        self.shrink_calls += 1


def fit_tokens(
    shrinkable: Shrinkable,
    max_prompt_chars=None,
    max_iterations=20,
):
    """Shrink a prompt element until it fits max_tokens.

    Parameters
    ----------
    shrinkable : Shrinkable
        The prompt element to shrink.
    max_prompt_chars : int
        The maximum number of chars allowed.
    max_iterations : int, optional
        The maximum number of shrink iterations, by default 20.
    model_name : str, optional
        The name of the model used when tokenizing.

    Returns:
    -------
    str : the prompt after shrinking.
    """
    if max_prompt_chars is None:
        return shrinkable.prompt

    for _ in range(max_iterations):
        prompt = shrinkable.prompt
        if isinstance(prompt, str):
            prompt_str = prompt
        elif isinstance(prompt, list):
            prompt_str = '\n'.join([p['text'] for p in prompt if p['type'] == 'text'])
        else:
            raise ValueError(f'Unrecognized type for prompt: {type(prompt)}')
        n_chars = len(prompt_str)
        if n_chars <= max_prompt_chars:
            return prompt
        shrinkable.shrink()

    logging.info(
        dedent(
            f"""\
            After {max_iterations} shrink iterations, the prompt is still
            {len(prompt_str)} chars (greater than {max_prompt_chars}). Returning the prompt as is."""
        )
    )
    return prompt


class HTML(Truncater):
    def __init__(self, html, visible: bool = True, prefix='') -> None:
        super().__init__(visible=visible, start_truncate_iteration=5)
        self._prompt = f'\n{prefix}HTML:\n{html}\n'


class AXTree(Truncater):
    def __init__(
        self, ax_tree, visible: bool = True, coord_type=None, prefix=''
    ) -> None:
        super().__init__(visible=visible, start_truncate_iteration=10)
        if coord_type == 'center':
            coord_note = """\
Note: center coordinates are provided in parenthesis and are
  relative to the top left corner of the page.\n\n"""
        elif coord_type == 'box':
            coord_note = """\
Note: bounding box of each object are provided in parenthesis and are
  relative to the top left corner of the page.\n\n"""
        else:
            coord_note = ''
        self._prompt = f'\n{prefix}AXTree:\n{coord_note}{ax_tree}\n'


class Error(PromptElement):
    def __init__(self, error, visible: bool = True, prefix='') -> None:
        super().__init__(visible=visible)
        self._prompt = f'\n{prefix}Error from previous action:\n{error}\n'


class Observation(Shrinkable):
    """Observation of the current step.

    Contains the html, the accessibility tree and the error logs.
    """

    def __init__(self, obs, flags: Flags) -> None:
        super().__init__()
        self.flags = flags
        self.obs = obs
        self.html = HTML(obs[flags.html_type], visible=flags.use_html, prefix='## ')
        self.ax_tree = AXTree(
            obs['axtree_txt'],
            visible=flags.use_ax_tree,
            coord_type=flags.extract_coords,
            prefix='## ',
        )
        self.error = Error(
            obs['last_action_error'],
            visible=flags.use_error_logs and obs['last_action_error'],
            prefix='## ',
        )

    def shrink(self):
        self.ax_tree.shrink()
        self.html.shrink()

    @property
    def _prompt(self) -> str:  # type: ignore
        return f'\n# Observation of current step:\n{self.html.prompt}{self.ax_tree.prompt}{self.error.prompt}\n\n'

    def add_screenshot(self, prompt):
        if self.flags.use_screenshot:
            if isinstance(prompt, str):
                prompt = [{'type': 'text', 'text': prompt}]
            img_url = BrowserEnv.image_to_jpg_base64_url(
                self.obs['screenshot'], add_data_prefix=True
            )
            prompt.append({'type': 'image_url', 'image_url': img_url})

        return prompt


class MacNote(PromptElement):
    def __init__(self) -> None:
        super().__init__(visible=platform.system() == 'Darwin')
        self._prompt = '\nNote: you are on mac so you should use Meta instead of Control for Control+C etc.\n'


class BeCautious(PromptElement):
    def __init__(self, visible: bool = True) -> None:
        super().__init__(visible=visible)
        self._prompt = """\
\nBe very cautious. Avoid submitting anything before verifying the effect of your
actions. Take the time to explore the effect of safe actions first. For example
you can fill a few elements of a form, but don't click submit before verifying
that everything was filled correctly.\n"""


class GoalInstructions(PromptElement):
    def __init__(self, goal, visible: bool = True) -> None:
        super().__init__(visible)
        self._prompt = f"""\
# Instructions
Review the current state of the page and all other information to find the best
possible next action to accomplish your goal. Your answer will be interpreted
and executed by a program, make sure to follow the formatting instructions.

## Goal:
{goal}
"""


class ChatInstructions(PromptElement):
    def __init__(self, chat_messages, visible: bool = True) -> None:
        super().__init__(visible)
        self._prompt = """\
# Instructions

You are a UI Assistant, your goal is to help the user perform tasks using a web browser. You can
communicate with the user via a chat, in which the user gives you instructions and in which you
can send back messages. You have access to a web browser that both you and the user can see,
and with which only you can interact via specific commands.

Review the instructions from the user, the current state of the page and all other information
to find the best possible next action to accomplish your goal. Your answer will be interpreted
and executed by a program, make sure to follow the formatting instructions.

## Chat messages:

"""
        self._prompt += '\n'.join(
            [
                f"""\
 - [{msg['role']}], {msg['message']}"""
                for msg in chat_messages
            ]
        )


class SystemPrompt(PromptElement):
    _prompt = """\
You are an agent trying to solve a web task based on the content of the page and
a user instructions. You can interact with the page and explore. Each time you
submit an action it will be sent to the browser and you will receive a new page."""


class MainPrompt(Shrinkable):
    def __init__(
        self,
        obs_history,
        actions,
        memories,
        thoughts,
        flags: Flags,
    ) -> None:
        super().__init__()
        self.flags = flags
        self.history = History(obs_history, actions, memories, thoughts, flags)
        if self.flags.enable_chat:
            self.instructions: Union[ChatInstructions, GoalInstructions] = (
                ChatInstructions(obs_history[-1]['chat_messages'])
            )
        else:
            if (
                'chat_messages' in obs_history[-1]
                and sum(
                    [msg['role'] == 'user' for msg in obs_history[-1]['chat_messages']]
                )
                > 1
            ):
                logging.warning(
                    'Agent is in goal mode, but multiple user messages are present in the chat. Consider switching to `enable_chat=True`.'
                )
            self.instructions = GoalInstructions(obs_history[-1]['goal'])

        self.obs = Observation(obs_history[-1], self.flags)
        self.action_space = ActionSpace(self.flags)

        self.think = Think(visible=flags.use_thinking)
        self.memory = Memory(visible=flags.use_memory)

    @property
    def _prompt(self) -> str:  # type: ignore
        prompt = f"""\
{self.instructions.prompt}\
{self.obs.prompt}\
{self.history.prompt}\
{self.action_space.prompt}\
{self.think.prompt}\
{self.memory.prompt}\
"""

        if self.flags.use_abstract_example:
            prompt += f"""
# Abstract Example

Here is an abstract version of the answer with description of the content of
each tag. Make sure you follow this structure, but replace the content with your
answer:
{self.think.abstract_ex}\
{self.memory.abstract_ex}\
{self.action_space.abstract_ex}\
"""

        if self.flags.use_concrete_example:
            prompt += f"""
# Concrete Example

Here is a concrete example of how to format your answer.
Make sure to follow the template with proper tags:
{self.think.concrete_ex}\
{self.memory.concrete_ex}\
{self.action_space.concrete_ex}\
"""
        return self.obs.add_screenshot(prompt)

    def shrink(self):
        self.history.shrink()
        self.obs.shrink()

    def _parse_answer(self, text_answer):
        ans_dict = {}
        ans_dict.update(self.think._parse_answer(text_answer))
        ans_dict.update(self.memory._parse_answer(text_answer))
        ans_dict.update(self.action_space._parse_answer(text_answer))
        return ans_dict


class ActionSpace(PromptElement):
    def __init__(self, flags: Flags) -> None:
        super().__init__()
        self.flags = flags
        self.action_space = _get_action_space(flags)

        self._prompt = (
            f'# Action space:\n{self.action_space.describe()}{MacNote().prompt}\n'
        )
        self._abstract_ex = f"""
<action>
{self.action_space.example_action(abstract=True)}
</action>
"""
        self._concrete_ex = f"""
<action>
{self.action_space.example_action(abstract=False)}
</action>
"""

    def _parse_answer(self, text_answer):
        ans_dict = parse_html_tags_raise(
            text_answer, keys=['action'], merge_multiple=True
        )

        try:
            # just check if action can be mapped to python code but keep action as is
            # the environment will be responsible for mapping it to python
            self.action_space.to_python_code(ans_dict['action'])
        except Exception as e:
            raise ParseError(
                f'Error while parsing action\n: {e}\n'
                'Make sure your answer is restricted to the allowed actions.'
            )

        return ans_dict


def _get_action_space(flags: Flags) -> AbstractActionSet:
    match flags.action_space:
        case 'python':
            action_space = PythonActionSet(strict=flags.is_strict)
            if flags.multi_actions:
                warn(
                    f'Flag action_space={repr(flags.action_space)} incompatible with multi_actions={repr(flags.multi_actions)}.',
                    stacklevel=2,
                )
            if flags.demo_mode != 'off':
                warn(
                    f'Flag action_space={repr(flags.action_space)} incompatible with demo_mode={repr(flags.demo_mode)}.',
                    stacklevel=2,
                )
            return action_space
        case 'bid':
            action_subsets = ['chat', 'bid']
        case 'coord':
            action_subsets = ['chat', 'coord']
        case 'bid+coord':
            action_subsets = ['chat', 'bid', 'coord']
        case 'bid+nav':
            action_subsets = ['chat', 'bid', 'nav']
        case 'coord+nav':
            action_subsets = ['chat', 'coord', 'nav']
        case 'bid+coord+nav':
            action_subsets = ['chat', 'bid', 'coord', 'nav']
        case _:
            raise NotImplementedError(
                f'Unknown action_space {repr(flags.action_space)}'
            )

    action_space = HighLevelActionSet(
        subsets=action_subsets,
        multiaction=flags.multi_actions,
        strict=flags.is_strict,
        demo_mode=flags.demo_mode,
    )

    return action_space


class Memory(PromptElement):
    _prompt = ''  # provided in the abstract and concrete examples

    _abstract_ex = """
<memory>
Write down anything you need to remember for next steps. You will be presented
with the list of previous memories and past actions.
</memory>
"""

    _concrete_ex = """
<memory>
I clicked on bid 32 to activate tab 2. The accessibility tree should mention
focusable for elements of the form at next step.
</memory>
"""

    def _parse_answer(self, text_answer):
        return parse_html_tags_raise(
            text_answer, optional_keys=['memory'], merge_multiple=True
        )


class Think(PromptElement):
    _prompt = ''

    _abstract_ex = """
<think>
Think step by step. If you need to make calculations such as coordinates, write them here. Describe the effect
that your previous action had on the current content of the page.
</think>
"""
    _concrete_ex = """
<think>
My memory says that I filled the first name and last name, but I can't see any
content in the form. I need to explore different ways to fill the form. Perhaps
the form is not visible yet or some fields are disabled. I need to replan.
</think>
"""

    def _parse_answer(self, text_answer):
        return parse_html_tags_raise(
            text_answer, optional_keys=['think'], merge_multiple=True
        )


def diff(previous, new):
    """Return a string showing the difference between original and new.

    If the difference is above diff_threshold, return the diff string.
    """
    if previous == new:
        return 'Identical', []

    if len(previous) == 0 or previous is None:
        return 'previous is empty', []

    diff_gen = difflib.ndiff(previous.splitlines(), new.splitlines())

    diff_lines = []
    plus_count = 0
    minus_count = 0
    for line in diff_gen:
        if line.strip().startswith('+'):
            diff_lines.append(line)
            plus_count += 1
        elif line.strip().startswith('-'):
            diff_lines.append(line)
            minus_count += 1
        else:
            continue

    header = f'{plus_count} lines added and {minus_count} lines removed:'

    return header, diff_lines


class Diff(Shrinkable):
    def __init__(
        self, previous, new, prefix='', max_line_diff=20, shrink_speed=2, visible=True
    ) -> None:
        super().__init__(visible=visible)
        self.max_line_diff = max_line_diff
        self.header, self.diff_lines = diff(previous, new)
        self.shrink_speed = shrink_speed
        self.prefix = prefix

    def shrink(self):
        self.max_line_diff -= self.shrink_speed
        self.max_line_diff = max(1, self.max_line_diff)

    @property
    def _prompt(self) -> str:  # type: ignore
        diff_str = '\n'.join(self.diff_lines[: self.max_line_diff])
        if len(self.diff_lines) > self.max_line_diff:
            original_count = len(self.diff_lines)
            diff_str = f'{diff_str}\nDiff truncated, {original_count - self.max_line_diff} changes now shown.'
        return f'{self.prefix}{self.header}\n{diff_str}\n'


class HistoryStep(Shrinkable):
    def __init__(
        self, previous_obs, current_obs, action, memory, flags: Flags, shrink_speed=1
    ) -> None:
        super().__init__()
        self.html_diff = Diff(
            previous_obs[flags.html_type],
            current_obs[flags.html_type],
            prefix='\n### HTML diff:\n',
            shrink_speed=shrink_speed,
            visible=lambda: flags.use_html and flags.use_diff,
        )
        self.ax_tree_diff = Diff(
            previous_obs['axtree_txt'],
            current_obs['axtree_txt'],
            prefix='\n### Accessibility tree diff:\n',
            shrink_speed=shrink_speed,
            visible=lambda: flags.use_ax_tree and flags.use_diff,
        )
        self.error = Error(
            current_obs['last_action_error'],
            visible=(
                flags.use_error_logs
                and current_obs['last_action_error']
                and flags.use_past_error_logs
            ),
            prefix='### ',
        )
        self.shrink_speed = shrink_speed
        self.action = action
        self.memory = memory
        self.flags = flags

    def shrink(self):
        super().shrink()
        self.html_diff.shrink()
        self.ax_tree_diff.shrink()

    @property
    def _prompt(self) -> str:  # type: ignore
        prompt = ''

        if self.flags.use_action_history:
            prompt += f'\n### Action:\n{self.action}\n'

        prompt += (
            f'{self.error.prompt}{self.html_diff.prompt}{self.ax_tree_diff.prompt}'
        )

        if self.flags.use_memory and self.memory is not None:
            prompt += f'\n### Memory:\n{self.memory}\n'

        return prompt


class History(Shrinkable):
    def __init__(
        self, history_obs, actions, memories, thoughts, flags: Flags, shrink_speed=1
    ) -> None:
        super().__init__(visible=flags.use_history)
        assert len(history_obs) == len(actions) + 1
        assert len(history_obs) == len(memories) + 1

        self.shrink_speed = shrink_speed
        self.history_steps: list[HistoryStep] = []

        for i in range(1, len(history_obs)):
            self.history_steps.append(
                HistoryStep(
                    history_obs[i - 1],
                    history_obs[i],
                    actions[i - 1],
                    memories[i - 1],
                    flags,
                )
            )

    def shrink(self):
        """Shrink individual steps"""
        # TODO set the shrink speed of older steps to be higher
        super().shrink()
        for step in self.history_steps:
            step.shrink()

    @property
    def _prompt(self):
        prompts = ['# History of interaction with the task:\n']
        for i, step in enumerate(self.history_steps):
            prompts.append(f'## step {i}')
            prompts.append(step.prompt)
        return '\n'.join(prompts) + '\n'


if __name__ == '__main__':
    html_template = """
    <html>
    <body>
    <div>
    Hello World.
    Step {}.
    </div>
    </body>
    </html>
    """

    OBS_HISTORY = [
        {
            'goal': 'do this and that',
            'pruned_html': html_template.format(1),
            'axtree_txt': '[1] Click me',
            'last_action_error': '',
        },
        {
            'goal': 'do this and that',
            'pruned_html': html_template.format(2),
            'axtree_txt': '[1] Click me',
            'last_action_error': '',
        },
        {
            'goal': 'do this and that',
            'pruned_html': html_template.format(3),
            'axtree_txt': '[1] Click me',
            'last_action_error': 'Hey, there is an error now',
        },
    ]
    ACTIONS = ["click('41')", "click('42')"]
    MEMORIES = ['memory A', 'memory B']
    THOUGHTS = ['thought A', 'thought B']

    flags = Flags(
        use_html=True,
        use_ax_tree=True,
        use_thinking=True,
        use_error_logs=True,
        use_past_error_logs=True,
        use_history=True,
        use_action_history=True,
        use_memory=True,
        use_diff=True,
        html_type='pruned_html',
        use_concrete_example=True,
        use_abstract_example=True,
        use_screenshot=False,
        multi_actions=True,
    )

    print(
        MainPrompt(
            obs_history=OBS_HISTORY,
            actions=ACTIONS,
            memories=MEMORIES,
            thoughts=THOUGHTS,
            flags=flags,
        ).prompt
    )
