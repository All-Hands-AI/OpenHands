import json
import os
import re

from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.utils.obs import flatten_axtree_to_str
from PIL import Image

from openhands.agenthub.browsing_agent.response_parser import BrowsingResponseParser
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import ImageContent, Message, TextContent
from openhands.events.action import (
    Action,
    AgentFinishAction,
    BrowseInteractiveAction,
    MessageAction,
)
from openhands.events.event import EventSource
from openhands.events.observation import BrowserOutputObservation
from openhands.events.observation.observation import Observation
from openhands.llm.llm import LLM
from openhands.runtime.browser.browser_env import BrowserEnv
from openhands.runtime.plugins import (
    PluginRequirement,
)

USE_NAV = (
    os.environ.get('USE_NAV', 'true') == 'true'
)  # only disable NAV actions when running webarena and miniwob benchmarks
USE_CONCISE_ANSWER = (
    os.environ.get('USE_CONCISE_ANSWER', 'false') == 'true'
)  # only return concise answer when running webarena and miniwob benchmarks

if not USE_NAV and USE_CONCISE_ANSWER:
    EVAL_MODE = True  # disabled NAV actions and only return concise answer, for webarena and miniwob benchmarks\
else:
    EVAL_MODE = False


def get_error_prefix(last_browser_action: str) -> str:
    return f'IMPORTANT! Last action is incorrect:\n{last_browser_action}\nThink again with the current observation of the page.\n'


def get_system_message(goal: str, action_space: str) -> str:
    return f"""\
# Instructions
Review the current state of the page and all other information to find the best
possible next action to accomplish your goal. Your answer will be interpreted
and executed by a program, make sure to follow the formatting instructions.

# Goal:
{goal}

# Action Space
{action_space}
"""


CONCISE_INSTRUCTION = """\

Here is another example with chain of thought of a valid action when providing a concise answer to user:
"
In order to accomplish my goal I need to send the information asked back to the user. This page list the information of HP Inkjet Fax Machine, which is the product identified in the objective. Its price is $279.49. I will send a message back to user with the answer.
```send_msg_to_user("$279.49")```
"
"""


def get_prompt(
    error_prefix: str, cur_url: str, cur_axtree_txt: str, prev_action_str: str
) -> str:
    prompt = f"""\
{error_prefix}

# Current Page URL:
{cur_url}

# Current Accessibility Tree:
{cur_axtree_txt}

# Previous Actions
{prev_action_str}

Here is an example with chain of thought of a valid action when clicking on a button:
"
In order to accomplish my goal I need to click on the button with bid 12
```click("12")```
"
""".strip()
    if USE_CONCISE_ANSWER:
        prompt += CONCISE_INSTRUCTION
    return prompt


# class BrowsingAgent(Agent):
#     VERSION = '1.0'
#     """
#     An agent that interacts with the browser.
#     """

#     sandbox_plugins: list[PluginRequirement] = []
#     response_parser = BrowsingResponseParser()

#     def __init__(
#         self,
#         llm: LLM,
#         config: AgentConfig,
#     ) -> None:
#         """Initializes a new instance of the BrowsingAgent class.

#         Parameters:
#         - llm (LLM): The llm to be used by this agent
#         """
#         super().__init__(llm, config)
#         # define a configurable action space, with chat functionality, web navigation, and webpage grounding using accessibility tree and HTML.
#         # see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/action/highlevel.py for more details
#         action_subsets = ['chat', 'bid']
#         if USE_NAV:
#             action_subsets.append('nav')
#         self.action_space = HighLevelActionSet(
#             subsets=action_subsets,
#             strict=False,  # less strict on the parsing of the actions
#             multiaction=True,  # enable to agent to take multiple actions at once
#         )

#         self.reset()

#     def reset(self) -> None:
#         """Resets the Browsing Agent."""
#         super().reset()
#         self.cost_accumulator = 0
#         self.error_accumulator = 0

#     def step(self, state: State) -> Action:
#         """Performs one step using the Browsing Agent.
#         This includes gathering information on previous steps and prompting the model to make a browsing command to execute.

#         Parameters:
#         - state (State): used to get updated info

#         Returns:
#         - BrowseInteractiveAction(browsergym_command) - BrowserGym commands to run
#         - MessageAction(content) - Message action to run (e.g. ask for clarification)
#         - AgentFinishAction() - end the interaction
#         """
#         messages: list[Message] = []
#         prev_actions = []
#         cur_url = ''
#         cur_axtree_txt = ''
#         error_prefix = ''
#         last_obs = None
#         last_action = None

#         if EVAL_MODE and len(state.history.get_events_as_list()) == 1:
#             # for webarena and miniwob++ eval, we need to retrieve the initial observation already in browser env
#             # initialize and retrieve the first observation by issuing an noop OP
#             # For non-benchmark browsing, the browser env starts with a blank page, and the agent is expected to first navigate to desired websites
#             return BrowseInteractiveAction(browser_actions='noop()')

#         for event in state.history.get_events():
#             if isinstance(event, BrowseInteractiveAction):
#                 prev_actions.append(event.browser_actions)
#                 last_action = event
#             elif isinstance(event, MessageAction) and event.source == EventSource.AGENT:
#                 # agent has responded, task finished.
#                 return AgentFinishAction(outputs={'content': event.content})
#             elif isinstance(event, Observation):
#                 last_obs = event

#         if EVAL_MODE:
#             prev_actions = prev_actions[1:]  # remove the first noop action

#         prev_action_str = '\n'.join(prev_actions)
#         # if the final BrowserInteractiveAction exec BrowserGym's send_msg_to_user,
#         # we should also send a message back to the user in OpenHands and call it a day
#         if (
#             isinstance(last_action, BrowseInteractiveAction)
#             and last_action.browsergym_send_msg_to_user
#         ):
#             return MessageAction(last_action.browsergym_send_msg_to_user)

#         if isinstance(last_obs, BrowserOutputObservation):
#             if last_obs.error:
#                 # add error recovery prompt prefix
#                 error_prefix = get_error_prefix(last_obs.last_browser_action)
#                 self.error_accumulator += 1
#                 if self.error_accumulator > 5:
#                     return MessageAction('Too many errors encountered. Task failed.')

#             cur_url = last_obs.url

#             try:
#                 cur_axtree_txt = flatten_axtree_to_str(
#                     last_obs.axtree_object,
#                     extra_properties=last_obs.extra_element_properties,
#                     with_clickable=True,
#                     filter_visible_only=True,
#                 )
#             except Exception as e:
#                 logger.error(
#                     'Error when trying to process the accessibility tree: %s', e
#                 )
#                 return MessageAction('Error encountered when browsing.')

#         goal, _ = state.get_current_user_intent()

#         if goal is None:
#             goal = state.inputs['task']

#         system_msg = get_system_message(
#             goal,
#             self.action_space.describe(with_long_description=False, with_examples=True),
#         )

#         messages.append(Message(role='system', content=[TextContent(text=system_msg)]))

#         prompt = get_prompt(error_prefix, cur_url, cur_axtree_txt, prev_action_str)
#         messages.append(Message(role='user', content=[TextContent(text=prompt)]))

#         response = self.llm.completion(
#             messages=self.llm.format_messages_for_llm(messages),
#             stop=[')```', ')\n```'],
#         )
#         return self.response_parser.parse(response)


class BrowsingAgent(Agent):
    VERSION = '1.0'
    """
    Re-implementing VisualWebArena Agent to integrate it into OpenHands repository
    """

    sandbox_plugins: list[PluginRequirement] = []
    response_parser = BrowsingResponseParser()

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initializes a new instance of the VWABrowsingAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm, config)
        # define a configurable action space, with chat functionality, web navigation, and webpage grounding using accessibility tree and HTML.
        # see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/action/highlevel.py for more details
        action_subsets = [
            'chat',
            'bid',
            'nav',
            'tab',
            'infeas',
        ]  # VWA Agent uses all 5 of these action types
        self.action_space = HighLevelActionSet(
            subsets=action_subsets,
            strict=False,  # less strict on the parsing of the actions
            multiaction=False,  # VWA Agent does not allow multi-action setting
        )
        self.reset()

    def reset(self) -> None:
        """Resets the VWABrowsing Agent."""
        super().reset()
        self.cost_accumulator = 0
        self.error_accumulator = 0

    def get_textual_som(self, accessibility_tree: str):
        """Get textual representation of Set-of-Marks annotation by processing accessibility tree."""
        accessibility_tree = accessibility_tree.replace('\t', '')
        elements = accessibility_tree.split('\n')
        text_som = []
        for element in elements:
            if 'clickable' in element:
                element = element.split(', clickable')[0]
                element_items = element.split(' ')
                bid = element_items[0]
                type_element = element_items[1]
                description = ' '.join(element_items[2:])
                description = description.encode('ascii', 'ignore').decode('ascii')
                description = re.sub(r'\\u[0-9a-fA-F]{4}', '', description)
                description = re.sub(r'\'', '', description)
                text_som.append(f'{bid} [{type_element}] [{description}]')
            elif 'StaticText' in element:
                description = element.split('StaticText ')[-1]
                description = description.encode('ascii', 'ignore').decode('ascii')
                description = re.sub(r'\\u[0-9a-fA-F]{4}', '', description)
                description = re.sub(r'\'', '', description)
                if len(description) > 0:
                    text_som.append(f'[] [StaticText] [{description}]')
            elif 'combobox' in element or 'button' in element or 'hasPopup' in element:
                element_items = element.split(' ')
                bid = element_items[0]
                type_element = element_items[1]
                description = ' '.join(element_items[2:])
                description = description.encode('ascii', 'ignore').decode('ascii')
                description = re.sub(r'\\u[0-9a-fA-F]{4}', '', description)
                description = re.sub(r'\'', '', description)
                text_som.append(f'{bid} [{type_element}] [{description}]')
        return '\n'.join(text_som)

    def step(self, state: State) -> Action:
        """Performs one step using the VWABrowsing Agent.
        This includes gathering information on previous steps and prompting the model to make a browsing command to execute.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - BrowseInteractiveAction(browsergym_command) - BrowserGym commands to run
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
        """
        messages: list[Message] = []
        prev_actions = []
        user_content = []
        cur_url = ''
        cur_axtree_txt = ''
        # error_prefix = '' #VWA Agent does not use error prefix
        last_obs = None
        last_action = None

        # TODO: EVAL_MODE must be set to true for VisualWebArena task as well, even when USE_NAV is true
        if len(state.history.get_events_as_list()) == 1:
            # for visualwebarena, webarena and miniwob++ eval, we need to retrieve the initial observation already in browser env
            # initialize and retrieve the first observation by issuing an noop OP
            # For non-benchmark browsing, the browser env starts with a blank page, and the agent is expected to first navigate to desired websites
            return BrowseInteractiveAction(browser_actions='noop()')

        for event in state.history.get_events():
            if isinstance(event, BrowseInteractiveAction):
                prev_actions.append(event.browser_actions)
                last_action = event
            elif isinstance(event, MessageAction) and event.source == EventSource.AGENT:
                # agent has responded, task finished.
                return AgentFinishAction(outputs={'content': event.content})
            elif isinstance(event, Observation):
                last_obs = event

        # VWA Agent only uses immediately previous action
        # if EVAL_MODE:
        prev_action_str = 'None'
        if len(prev_actions) > 1:  # ignore noop()
            prev_actions = prev_actions[1:]  # remove the first noop action
            prev_action_str = prev_actions[-1]

        # if the final BrowserInteractiveAction exec BrowserGym's send_msg_to_user,
        # we should also send a message back to the user in OpenHands and call it a day
        if (
            isinstance(last_action, BrowseInteractiveAction)
            and last_action.browsergym_send_msg_to_user
        ):
            return MessageAction(last_action.browsergym_send_msg_to_user)

        if isinstance(last_obs, BrowserOutputObservation):
            # VWA Agent does not add error recovery prompt prefix
            # if last_obs.error:
            #     # add error recovery prompt prefix
            #     error_prefix = get_error_prefix(last_obs.last_browser_action)
            #     self.error_accumulator += 1
            #     if self.error_accumulator > 5:
            #         return MessageAction('Too many errors encountered. Task failed.')

            cur_url = last_obs.url

            # screenshot + som: will be a non-empty string if present in observation
            if (last_obs.set_of_marks is not None) and (len(last_obs.set_of_marks) > 0):
                user_content.append(
                    TextContent(text='IMAGES: (1) current page screenshot')
                )
                user_content.append(ImageContent(image_urls=[last_obs.set_of_marks]))
            try:
                cur_axtree_txt = flatten_axtree_to_str(
                    last_obs.axtree_object,
                    extra_properties=last_obs.extra_element_properties,
                    with_clickable=True,
                    filter_visible_only=True,
                )
            except Exception as e:
                logger.error(
                    'Error when trying to process the accessibility tree: %s', e
                )
                return MessageAction('Error encountered when browsing.')

        goal, image_urls = state.get_current_user_intent()
        if image_urls is not None:
            for idx, url in enumerate(image_urls):
                user_content.append(
                    TextContent(text=f'({idx+2}) input image {idx+1}))')
                )
                user_content.append(ImageContent(image_urls=[url]))
        if goal is None:
            goal = state.inputs['task']
        text_som = self.get_textual_som(cur_axtree_txt)

        # currently keeping all prompts inside agent, can change once code evolves
        system_msg = f"""\
You are an autonomous intelligent agent tasked with navigating a web browser. You will be given web-based tasks. These tasks will be accomplished through the use of specific actions you can issue.

Here's the information you'll have:
The user's objective: This is the task you're trying to complete.
The observation: This text lists the IDs of all interactable elements on the current web page with their text content if any, in the format [id] [tagType] [description]. tagType is the type of the element, such as button, link, or textbox. description is the textual content describing the element and its properties. For example, [1234] [button] [Add to Cart] means that there is a button with id '1234' and text content 'Add to Cart' on the current web page. [] [StaticText] [text] means that the element is of some text that is not interactable.
The current web page screenshot: This is a screenshot of the webpage, with each interactable element assigned a unique id.
The current web page's URL: This is the page you're currently navigating.
The previous action: This is the action you just performed. It may be helpful to track your progress.
You will be given 3 example inputs and their corresponding example outputs and then finally you will get the user query.
The actions you can perform are described below:

{self.action_space.describe(with_long_description=True, with_examples=True)}

To be successful, it is very important to follow the following rules:
1. You should only issue an action that is valid given the current observation
2. You should only issue one action at a time.
3. You should follow the examples to reason step by step and then issue the next action.
4. Generate the action in the correct format. Start with a \"In summary, the next action I will perform is\" phrase, followed by action inside ``````. For example, \"In summary, the next action I will perform is ```fill('237', 'example value')```\".
5. The examples are given only for reference, and you must generate all actions to only solve the objective of the user query.
6. If you have completed the task, issue send_msg_to_user action. For example, if you are asked what is the color of the sky, return
"
```send_msg_to_user("blue")```
"
""".strip()
        # TODO: caching of prompt is not working right now
        messages.append(
            Message(
                role='system', content=[TextContent(text=system_msg, cache_prompt=True)]
            )
        )
        with open('openhands/agenthub/browsing_agent/few_shot_prompts.json', 'r') as f:
            few_shot_data = json.load(f)
        for i, example in enumerate(few_shot_data['examples']):
            example_img = Image.open(example[2])
            example_content = [
                TextContent(
                    text=f'EXAMPLE INPUT {i+1}\n\n' + example[0], cache_prompt=True
                ),
                TextContent(
                    text='IMAGES: (1) current page screenshot', cache_prompt=True
                ),
                ImageContent(
                    image_urls=[
                        BrowserEnv.image_to_png_base64_url(
                            image=example_img, add_data_prefix=True
                        )
                    ],
                    cache_prompt=True,
                ),
            ]
            messages.append(Message(role='user', content=example_content))
            messages.append(
                Message(
                    role='assistant',
                    content=[
                        TextContent(
                            text=f'EXAMPLE OUTPUT {i+1}\n\n' + example[1],
                            cache_prompt=True,
                        )
                    ],
                )
            )

        user_prompt = f"""\
USER QUERY\n\n
OBSERVATION:\n{text_som}
URL: {cur_url}
OBJECTIVE: {goal}
PREVIOUS ACTION: {prev_action_str}
""".strip()
        messages.append(
            Message(role='user', content=[TextContent(text=user_prompt)] + user_content)
        )

        flat_messages = self.llm.format_messages_for_llm(messages)

        response = self.llm.completion(
            messages=flat_messages,
            temperature=0.0,
            stop=[')```', ')\n```'],
        )

        return self.response_parser.parse(response)
