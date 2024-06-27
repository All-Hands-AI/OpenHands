import abc
import platform

from browsergym.core.action.base import AbstractActionSet
from browsergym.core.action.highlevel import HighLevelActionSet

from .utils import (
    ParseError,
    parse_html_tags_raise,
)

# @dataclass
# class Flags:
#     use_html: bool = True
#     use_ax_tree: bool = False
#     drop_ax_tree_first: bool = True  # This flag is no longer active TODO delete
#     use_thinking: bool = False
#     use_error_logs: bool = False
#     use_past_error_logs: bool = False
#     use_history: bool = False
#     use_action_history: bool = False
#     use_memory: bool = False
#     use_diff: bool = False
#     html_type: str = 'pruned_html'
#     use_concrete_example: bool = True
#     use_abstract_example: bool = False
#     multi_actions: bool = False
#     action_space: Literal[
#         'python', 'bid', 'coord', 'bid+coord', 'bid+nav', 'coord+nav', 'bid+coord+nav'
#     ] = 'bid'
#     is_strict: bool = False
#     # This flag will be automatically disabled `if not chat_model_args.has_vision()`
#     use_screenshot: bool = True
#     enable_chat: bool = False
#     max_prompt_tokens: int = None
#     extract_visible_tag: bool = False
#     extract_coords: Literal['False', 'center', 'box'] = 'False'
#     extract_visible_elements_only: bool = False
#     demo_mode: Literal['off', 'default', 'only_visible_elements'] = 'off'

#     def copy(self):
#         return deepcopy(self)

#     def asdict(self):
#         """Helper for JSON serializble requirement."""
#         return asdict(self)

#     @classmethod
#     def from_dict(self, flags_dict):
#         """Helper for JSON serializble requirement."""
#         if isinstance(flags_dict, Flags):
#             return flags_dict

#         if not isinstance(flags_dict, dict):
#             raise ValueError(
#                 f'Unregcognized type for flags_dict of type {type(flags_dict)}.'
#             )
#         return Flags(**flags_dict)


class PromptElement:
    """Base class for all prompt elements. Prompt elements can be hidden.

    Prompt elements are used to build the prompt. Use flags to control which
    prompt elements are visible. We use class attributes as a convenient way
    to implement static prompts, but feel free to override them with instance
    attributes or @property decorator."""

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
        this prompt. You can also implement a shriking startegy for this prompt.
        Shrinking is can be called multiple times to progressively shrink the
        prompt until it fits max_tokens. Default max shrink iterations is 20.
        """
        pass


class Trunkater(Shrinkable):
    def __init__(self, visible, shrink_speed=0.3, start_trunkate_iteration=10):
        super().__init__(visible=visible)
        self.shrink_speed = shrink_speed
        self.start_trunkate_iteration = start_trunkate_iteration
        self.shrink_calls = 0
        self.deleted_lines = 0

    def shrink(self) -> None:
        if self.is_visible and self.shrink_calls >= self.start_trunkate_iteration:
            # remove the fraction of _prompt
            lines = self._prompt.splitlines()
            new_line_count = int(len(lines) * (1 - self.shrink_speed))
            self.deleted_lines += len(lines) - new_line_count
            self._prompt = '\n'.join(lines[:new_line_count])
            self._prompt += (
                f'\n... Deleted {self.deleted_lines} lines to reduce prompt size.'
            )

        self.shrink_calls += 1


# def fit_tokens(
#     shrinkable: Shrinkable,
#     max_prompt_tokens=None,
#     max_iterations=20,
#     model_name='openai/gpt-4',
# ):
#     """Shrink a prompt element until it fits max_tokens.

#     Parameters
#     ----------
#     shrinkable : Shrinkable
#         The prompt element to shrink.
#     max_tokens : int
#         The maximum number of tokens allowed.
#     max_iterations : int, optional
#         The maximum number of shrink iterations, by default 20.
#     model_name : str, optional
#         The name of the model used when tokenizing.

#     Returns
#     -------
#     str : the prompt after shrinking.
#     """

#     if max_prompt_tokens is None:
#         return shrinkable.prompt

#     for _ in range(max_iterations):
#         prompt = shrinkable.prompt
#         if isinstance(prompt, str):
#             prompt_str = prompt
#         elif isinstance(prompt, list):
#             prompt_str = '\n'.join([p['text'] for p in prompt if p['type'] == 'text'])
#         else:
#             raise ValueError(f'Unrecognized type for prompt: {type(prompt)}')
#         n_token = count_tokens(prompt_str, model=model_name)
#         if n_token <= max_prompt_tokens:
#             return prompt
#         shrinkable.shrink()

#     logging.info(
#         dedent(
#             f"""\
#             After {max_iterations} shrink iterations, the prompt is still
#             {count_tokens(prompt_str)} tokens (greater than {max_prompt_tokens}). Returning the prompt as is."""
#         )
#     )
#     return prompt


# def _get_action_space(flags: Flags) -> AbstractActionSet:
#     match flags.action_space:
#         case 'python':
#             action_space = PythonActionSet(strict=flags.is_strict)
#             if flags.multi_actions:
#                 warn(
#                     f'Flag action_space={repr(flags.action_space)} incompatible with multi_actions={repr(flags.multi_actions)}.'
#                 )
#             if flags.demo_mode != 'off':
#                 warn(
#                     f'Flag action_space={repr(flags.action_space)} incompatible with demo_mode={repr(flags.demo_mode)}.'
#                 )
#             return action_space
#         case 'bid':
#             action_subsets = ['chat', 'bid']
#         case 'coord':
#             action_subsets = ['chat', 'coord']
#         case 'bid+coord':
#             action_subsets = ['chat', 'bid', 'coord']
#         case 'bid+nav':
#             action_subsets = ['chat', 'bid', 'nav']
#         case 'coord+nav':
#             action_subsets = ['chat', 'coord', 'nav']
#         case 'bid+coord+nav':
#             action_subsets = ['chat', 'bid', 'coord', 'nav']
#         case _:
#             raise NotImplementedError(
#                 f'Unknown action_space {repr(flags.action_space)}'
#             )

#     action_space = HighLevelActionSet(
#         subsets=action_subsets,
#         multiaction=flags.multi_actions,
#         strict=flags.is_strict,
#         demo_mode=flags.demo_mode,
#     )

#     return action_space


class HTML(Trunkater):
    def __init__(self, html, visible: bool = True, prefix='') -> None:
        super().__init__(visible=visible, start_trunkate_iteration=5)
        self._prompt = f'\n{prefix}HTML:\n{html}\n'


class AXTree(Trunkater):
    def __init__(
        self, ax_tree, visible: bool = True, coord_type=None, prefix=''
    ) -> None:
        super().__init__(visible=visible, start_trunkate_iteration=10)
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
        self._prompt = f'\n{prefix}AXTree (you may only interact with elements in this tree):\n{coord_note}{ax_tree}\n'


class Error(PromptElement):
    def __init__(self, error, visible: bool = True, prefix='') -> None:
        super().__init__(visible=visible)
        self._prompt = f'\n{prefix}Error from previous action:\n{error}\n'


# class Observation(Shrinkable):
#     """Observation of the current step.

#     Contains the html, the accessibility tree and the error logs.
#     """

#     def __init__(self, obs, flags: Flags) -> None:
#         super().__init__()
#         self.flags = flags
#         self.obs = obs
#         self.html = HTML(
#             obs[flags.html_type], visible=lambda: flags.use_html, prefix='## '
#         )
#         self.ax_tree = AXTree(
#             obs['axtree_txt'],
#             visible=lambda: flags.use_ax_tree,
#             coord_type=flags.extract_coords,
#             prefix='## ',
#         )
#         self.error = Error(
#             obs['last_action_error'],
#             visible=lambda: flags.use_error_logs and obs['last_action_error'],
#             prefix='## ',
#         )

#     def shrink(self):
#         self.ax_tree.shrink()
#         self.html.shrink()

#     @property
#     def _prompt(self) -> str:
#         return f'\n# Observation of current step:\n{self.html.prompt}{self.ax_tree.prompt}{self.error.prompt}\n\n'

#     def add_screenshot(self, prompt):
#         if self.flags.use_screenshot:
#             if isinstance(prompt, str):
#                 prompt = [{'type': 'text', 'text': prompt}]
#             img_url = BrowserEnv.image_to_jpg_base64_url(self.obs['screenshot'])
#             prompt.append({'type': 'image_url', 'image_url': img_url})

#         return prompt


class MacNote(PromptElement):
    def __init__(self) -> None:
        super().__init__(visible=platform.system() == 'Darwin')
        self._prompt = '\nNote: you are on mac so you should use Meta instead of Control for Control+C etc.\n'


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
 - [{msg['role']}] {msg['message']}"""
                for msg in chat_messages
            ]
        )


class SystemPrompt(PromptElement):
    _prompt = """\
You are an agent trying to solve a web task based on the content of the page and
a user instructions. You can interact with the page and explore. Each time you
submit an action it will be sent to the browser and you will receive a new page."""


def _get_my_action_space() -> AbstractActionSet:
    # Assume action space type is bid
    action_space = 'bid'
    action_subsets = ['chat', 'nav', 'bid']

    action_space = HighLevelActionSet(
        subsets=action_subsets,
        multiaction=False,
        strict=False,
        demo_mode=True,
    )

    return action_space


class MyActionSpace(PromptElement):
    def __init__(self) -> None:
        super().__init__()
        # self.flags = flags
        self.action_space = _get_my_action_space()

        # self._prompt = f"# Action space:\n{self.action_space.describe()}{MacNote().prompt}\n"
        self._prompt = f'# Action space:\n{self.action_space.describe(with_long_description=False, with_examples=True)}\n'
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


class MyMainPrompt(PromptElement):
    def __init__(
        self,
        obs_history,
        states,
        strategies,
        actions,
        active_strategy=None,
        action_space=None,
    ):
        super().__init__()
        # Include all states + actions from the history. Ignore obs_history for now
        self.obs_history = obs_history
        self.states = states
        self.strategies = strategies
        self.actions = actions
        self.active_strategy = active_strategy
        self.action_space = action_space

        self.history = self.get_history(obs_history, states, strategies, actions)
        # self.instructions = self.get_goal_instruction(obs_history[-1]["goal"])

        # Several modes
        # 1. len(obs_history) == len(states) + 1 == len(actions) + 1: encoding, use just the obs
        # 2. len(obs_history) == len(states) == len(actions) + 1: policy, use obs + state
        # 3. len(obs_history) == len(states) == len(actions): first forward dynamics, use obs + state + action
        # 4. len(states) == len(actions) > len(obs_history): other forward dynamics, use state + action
        # 4. len(states) == len(actions) > len(obs_history): action value, use state + action
        # 4. len(states) == len(actions) + 1 > len(obs_history): critic, use state
        # 5. len(states) == len(actions) + 1 > len(obs_history): rollout policy, use state

        if len(obs_history) == len(states) + 1 and len(states) == len(strategies):
            # encoding, use just the obs
            self.obs = self.get_obs(obs_history[-1])
        elif (
            len(obs_history) == len(states)
            and len(states) == len(strategies) + 1
            and len(strategies) == len(actions)
        ):
            # strategy, use the obs and the state
            self.obs = self.get_obs_state(obs_history[-1], states[-1])
        elif (
            len(obs_history) == len(states)
            and len(states) == len(strategies)
            and len(strategies) == len(actions) + 1
        ):
            # policy, use obs, state, and strategy
            self.obs = self.get_obs_state_strat(
                obs_history[-1], states[-1], active_strategy
            )
        elif (
            len(obs_history) <= len(states)
            and len(states) == len(strategies)
            and len(strategies) >= len(actions) + 1
        ):
            # forward dynamics, use state + strat
            # action value, use state + strat
            self.obs = self.get_state_strat(states[-1], strategies[-1])
        elif len(obs_history) < len(states) and len(states) == len(strategies) + 1:
            # rollout strategy, use state
            self.obs = self.get_state(states[-1])

        # self.action_space = MyActionSpace()

    #     def get_goal_instruction(self, goal):
    #         prompt = f"""\
    # # Instructions
    # Review the current state of the page and all other information to find the best
    # possible next action to accomplish your goal. Your answer will be interpreted
    # and executed by a program, make sure to follow the formatting instructions.

    # ## Goal:
    # {goal}
    # """
    #         return prompt

    def get_history(self, obs_history, states, strategies, actions):
        # assert len(obs_history) == len(states) or len(obs_history) == len(states) + 1
        # assert len(obs_history) == len(actions) + 1
        # assert len(states) == len(actions) or len(states) == len(actions) + 1
        assert len(states) == len(strategies) or len(states) == len(strategies) + 1

        self.history_steps = []

        for i in range(1, len(states)):
            history_step = self.get_history_step(
                None,
                states[i - 1],
                strategies[i - 1],
                actions[i - 1] if i <= len(actions) else None,
            )

            self.history_steps.append(history_step)

        prompts = ['\n# History of interaction with the task:\n']
        for i, step in enumerate(self.history_steps):
            prompts.append(f'## Step {i}')
            prompts.append(step)
        return '\n'.join(prompts) + '\n'

    def get_history_step(self, current_obs, state, strategy, action):
        if current_obs is not None:
            self.ax_tree = AXTree(
                current_obs['axtree_txt'],
                visible=True,
                coord_type=False,
                prefix='\n#### Accessibility tree:\n',
            )
            self.error = Error(
                current_obs['last_action_error'],
                visible=current_obs['last_action_error'],
                prefix='#### ',
            )
            # # self.observation = f"{self.ax_tree.prompt}{self.error.prompt}"
            self.observation = f'{self.error.prompt}{self.ax_tree.prompt}'
        self.state = state
        self.strategy = strategy
        self.action = action

        prompt = ''
        if current_obs is not None:
            prompt += f'\n### Observation:\n{self.observation}\n\n'
        else:
            prompt += f'\n### State:\n{self.state}\n'

        if strategy is not None:
            prompt += f'\n### Strategy:\n{self.strategy}\n'

        if action is not None:
            prompt += f'\n### Action:\n{self.action}\n'

        return prompt

    def get_obs(self, obs):
        # self.html = HTML(obs["pruned_html"],
        #                  visible=True,
        #                  prefix="## ")
        self.ax_tree = AXTree(
            obs['axtree_txt'],
            visible=True,
            coord_type=False,
            prefix='## ',
        )
        self.error = Error(
            obs['last_action_error'],
            visible=obs['last_action_error'],
            prefix='## ',
        )
        # self.screenshot = obs["screenshot"]

        # return f"\n# Observation of current step:\n{self.error.prompt}{self.ax_tree.prompt}\n"
        # return f"\n# Observation of current step:\n{self.html.prompt}{self.ax_tree.prompt}{self.error.prompt}\n\n"
        return f'\n# Observation of current step:\nAXSTART{self.ax_tree.prompt}AXEND{self.error.prompt}\n\n'

    def get_obs_state(self, obs, state):
        return self.get_obs(obs) + f'\n## Current State:\n{state}\n'

    def get_obs_state_strat(self, obs, state, strategy):
        return self.get_obs_state(obs, state) + f'\n## Current Strategy:\n{strategy}\n'

    def get_state(self, state):
        return f'\n## Current State:\n{state}\n\n'

    def get_state_strat(self, state, strategy):
        return self.get_state(state) + f'\n## Current Strategy:\n{strategy}\n'

    # def add_screenshot(self, prompt):
    #     if isinstance(prompt, str):
    #         prompt = [{'type': 'text', 'text': prompt}]
    #     img_url = BrowserEnv.image_to_jpg_base64_url(self.screenshot)
    #     prompt.append({'type': 'image_url', 'image_url': img_url})

    #     return prompt

    def get_effectuator_prompt(self) -> str:
        prompt = f"""\
{self.history}\
{self.obs}\
"""

        prompt += """
# Abstract Example

Here is an abstract version of the answer with description of the content of
each tag. Make sure you follow this structure, but replace the content with your
answer:
<action>
Based on the current observation, state and active strategy, select one single
action to be executed. You can only use one action at a time.
</action>\
"""

        prompt += """
# Concrete Example

Here is a concrete example of how to format your answer.
Make sure to follow the template with proper tags:
<action>
fill('32-12', 'example with "quotes"')
</action>\
"""

        # prompt = self.add_screenshot(prompt)

        return prompt

    def get_encoder_prompt(self) -> str:
        prompt = f"""\
{self.history}\
{self.obs}\
## Active Strategy:
{self.active_strategy}\
"""

        prompt += """
# Abstract Example

Here is an abstract version of the answer with description of the content of
each tag. Make sure you follow this structure, but replace the content with your
answer:
<state>
Summarize the observation of the current step and last error you encountered. Include
details such as accessibility tree id when describing elements on the page. Describe
the effect that your previous action had, as well as elements you can interact with.
Infer any information relevant to achieving your goal. No need to describe what you
plan to do, just focus on giving an objective description.
</state>\


<status>
Observe your previous action, current state, and active strategy. Classify the situation into
one of four categories based on the progress of your strategy. The categories are:

1. "finished" - Your strategy has been successfully executed and you will plan for the next step.
2. "in-progress" - Your strategy is still ongoing and you need to take some more actions.
3. "not-sure" - It's unclear if your strategy has been carried out and you need to reassess your plan.
4. "failed" - Your strategy was not successful and you need to replan.

You should be extra careful when assigning "in-progress" labels. If you are unsure,
please select "not-sure" instead.
</status>\
"""

        prompt += """
# Concrete Example

Here is a concrete example of how to format your answer.
Make sure to follow the template with proper tags:
<state>
The previous action yielded a timeout error, suggesting it had no effect on the page.
The page shows:
- An empty textbox with id 123, which can be clicked or filled. Text "Date" is on top,
suggesting the textbox may be for entering dates.
- A button with id 456 and text "Submit" below textbox 123, suggesting that when clicked,
it will submit the textbox's content to the website backend.
</state>\

<status>
not-sure
</status>\
"""

        # prompt = self.add_screenshot(prompt)

        return prompt

    def get_policy_prompt(self) -> str:
        prompt = f"""\
{self.history}\
{self.obs}\
"""

        prompt += """
# Abstract Example

Here is an abstract version of the answer with description of the content of
each tag. Make sure you follow this structure, but replace the content with your
answer:
<strategy>
Assume the previous actions have been carried out and the environment has
transitioned to the current inferred state. Describe your next action to
achieve the goal. Avoid starting phrases like "To accomplish the goal", "I will",
"To proceed", or "Assume the previous strategies have been carried out". Do not
mention specific element ids as they may change during the execution.
Limit your answer to one sentence. Include any details that make it easier
for someone else to select the right action. Be creative, and try to come
up with many different ways to reach the goal.
</strategy>\
"""

        prompt += """
# Concrete Example

Here is a concrete example of how to format your answer.
Make sure to follow the template with proper tags:
<strategy>
Explore different ways to fill the form, such as clicking its elements to explore
options or filling parts of it with text.
</strategy>\
"""

        # prompt = self.add_screenshot(prompt)

        return prompt

    def get_dynamics_prompt(self) -> str:
        prompt = f"""\
{self.obs}\
"""

        prompt += """
# Abstract Example

Here is an abstract version of the answer with description of the content of
each tag. Make sure you follow this structure, but replace the content with your
answer:
<next_state>
Assume the environment is at the current inferred state and your proposed strategy has
been applied. Predict the new state of the webpage after executing each part of the
proposed strategy, such as page content you will observe and any possible information
you will gain that is relevant to your goal. Pay attention to how the element details
will change. Describe the elements you can interact with on the changed webpage.
</next_state>\

<status>
Observe your previous and current states of the browser environment. Classify
your status into one of three categories based on your progress towards the goal.
The categories are:

1. "in-progress" - You are still in progress to achieving the goal.
2. "not-sure" - It’s unclear if you have achieved the goal.
3. "goal-reached" - You have successfully completed the goal.
</status>\
"""

        prompt += """
# Concrete Example

Here is a concrete example of how to format your answer.
Make sure to follow the template with proper tags:
<next_state>
A new list of text items have appeared below textbox 123, which may be autocomplete.

The page shows:
- A textbox with id 123 filled with text "quote", which can be clicked or filled again.
- A list with id 456 under textbox 123. It contains items with ids 789 and 012, each of
which can be clicked on. Item 789 has text "quote on" which matches what we want.
- A button with id 345 and text "Submit" below textbox 123, suggesting that when clicked,
it will submit the textbox's content to the website backend.
</next_state>\

<status>
in-progress
</status>\
"""

        # prompt = self.add_screenshot(prompt)

        return prompt

    def get_action_reward_prompt(self) -> str:
        prompt = f"""\
{self.obs}\
"""

        prompt += """
# Abstract Example

Here is an abstract version of the answer with description of the content of
each tag. Make sure you follow this structure, but replace the content with your
answer:
<think>
Observe your current state and proposed strategy in the browser environment,
classify the proposed strategy into one of four categories
based on progress towards your goal. The categories are:

1. "towards-the-goal" - You are moving closer to achieving the goal.
2. "not-sure" - It’s unclear if the action are helping reach the goal.
3. "away-from-the-goal" - Your actions are diverting from the goal.

Explain your reasoning here.
</think>\

<response>
"towards-the-goal", "not-sure", or "away-from-the-goal"
You should be extra-careful when assigning "towards-the-goal" labels. If you are unsure, please
select "not-sure" instead.
</response>\
"""

        prompt += """
# Concrete Example

Here is a concrete example of how to format your answer.
Make sure to follow the template with proper tags:
<think>
The proposed action clicks the "Submit" button with 123 without filling out the
form above it. It will likely encounter an error, moving away from the goal.
</think>\

<response>
away-from-the-goal
</response>\
"""

        return prompt

    def _parse_effectuator_answer(self, text_answer):
        ans_dict = {}
        ans_dict.update(
            parse_html_tags_raise(text_answer, keys=['action'], merge_multiple=True)
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

    def _parse_encoder_answer(self, text_answer):
        ans_dict = {}
        ans_dict.update(
            parse_html_tags_raise(
                text_answer, optional_keys=['think'], merge_multiple=True
            )
        )
        ans_dict.update(
            parse_html_tags_raise(
                text_answer, keys=['state', 'status'], merge_multiple=True
            )
        )
        return ans_dict

    def _parse_policy_answer(self, text_answer):
        ans_dict = {}
        ans_dict.update(
            parse_html_tags_raise(text_answer, keys=['strategy'], merge_multiple=True)
        )
        return ans_dict

    def _parse_dynamics_answer(self, text_answer):
        ans_dict = {}
        ans_dict.update(
            parse_html_tags_raise(
                text_answer, keys=['next_state', 'status'], merge_multiple=True
            )
        )
        return ans_dict

    def _parse_action_reward_answer(self, text_answer):
        ans_dict = {}
        ans_dict.update(
            parse_html_tags_raise(
                text_answer, optional_keys=['think'], merge_multiple=True
            )
        )
        ans_dict.update(
            parse_html_tags_raise(text_answer, keys=['response'], merge_multiple=True)
        )
        return ans_dict


if __name__ == '__main__':
    pass
    # html_template = """
    # <html>
    # <body>
    # <div>
    # Hello World.
    # Step {}.
    # </div>
    # </body>
    # </html>
    # """

    # OBS_HISTORY = [
    #     {
    #         'goal': 'do this and that',
    #         'pruned_html': html_template.format(1),
    #         'axtree_txt': '[1] Click me',
    #         'last_action_error': '',
    #     },
    #     {
    #         'goal': 'do this and that',
    #         'pruned_html': html_template.format(2),
    #         'axtree_txt': '[1] Click me',
    #         'last_action_error': '',
    #     },
    #     {
    #         'goal': 'do this and that',
    #         'pruned_html': html_template.format(3),
    #         'axtree_txt': '[1] Click me',
    #         'last_action_error': 'Hey, there is an error now',
    #     },
    # ]
    # ACTIONS = ["click('41')", "click('42')"]
    # MEMORIES = ['memory A', 'memory B']
    # THOUGHTS = ['thought A', 'thought B']

    # flags = Flags(
    #     use_html=True,
    #     use_ax_tree=True,
    #     use_thinking=True,
    #     use_error_logs=True,
    #     use_past_error_logs=True,
    #     use_history=True,
    #     use_action_history=True,
    #     use_memory=True,
    #     use_diff=True,
    #     html_type='pruned_html',
    #     use_concrete_example=True,
    #     use_abstract_example=True,
    #     multi_actions=True,
    # )

    # print(
    #     MainPrompt(
    #         obs_history=OBS_HISTORY,
    #         actions=ACTIONS,
    #         memories=MEMORIES,
    #         thoughts=THOUGHTS,
    #         step=0,
    #         flags=flags,
    #     ).prompt
    # )
