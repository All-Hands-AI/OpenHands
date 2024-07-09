#######

from agenthub.codeact_agent.action_parser import CodeActResponseParser
from agenthub.codeact_agent.prompt import (
    COMMAND_DOCS,
    EXAMPLES,
    GITHUB_MESSAGE,
    SYSTEM_PREFIX,
    SYSTEM_SUFFIX,
)
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.exceptions import SummarizeError
from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
)
from opendevin.events.observation import (
    AgentDelegateObservation,
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from opendevin.events.serialization.event import truncate_content
from opendevin.llm.llm import LLM
from opendevin.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from opendevin.runtime.tools import RuntimeTool

#######

ENABLE_GITHUB = True


def action_to_str(action: Action) -> str:
    if isinstance(action, CmdRunAction):
        return f'{action.thought}\n<execute_bash>\n{action.command}\n</execute_bash>'
    elif isinstance(action, IPythonRunCellAction):
        return f'{action.thought}\n<execute_ipython>\n{action.code}\n</execute_ipython>'
    elif isinstance(action, AgentDelegateAction):
        return f'{action.thought}\n<execute_browse>\n{action.inputs["task"]}\n</execute_browse>'
    elif isinstance(action, MessageAction):
        return action.content
    return ''


def get_action_message(action: Action) -> dict[str, str] | None:
    if (
        isinstance(action, AgentDelegateAction)
        or isinstance(action, CmdRunAction)
        or isinstance(action, IPythonRunCellAction)
        or isinstance(action, MessageAction)
    ):
        return {
            'role': 'user' if action.source == 'user' else 'assistant',
            'content': action_to_str(action),
        }
    return None


def get_observation_message(obs) -> dict[str, str] | None:
    if isinstance(obs, CmdOutputObservation):
        content = 'OBSERVATION:\n' + truncate_content(obs.content)
        content += (
            f'\n[Command {obs.command_id} finished with exit code {obs.exit_code}]'
        )
        return {'role': 'user', 'content': content}
    elif isinstance(obs, IPythonRunCellObservation):
        content = 'OBSERVATION:\n' + obs.content
        # replace base64 images with a placeholder
        splitted = content.split('\n')
        for i, line in enumerate(splitted):
            if '![image](data:image/png;base64,' in line:
                splitted[i] = (
                    '![image](data:image/png;base64, ...) already displayed to user'
                )
        content = '\n'.join(splitted)
        content = truncate_content(content)
        return {'role': 'user', 'content': content}
    elif isinstance(obs, AgentDelegateObservation):
        content = 'OBSERVATION:\n' + truncate_content(str(obs.outputs))
        return {'role': 'user', 'content': content}
    return None


# FIXME: We can tweak these two settings to create MicroAgents specialized toward different area
def get_system_message() -> str:
    if ENABLE_GITHUB:
        return f'{SYSTEM_PREFIX}\n{GITHUB_MESSAGE}\n\n{COMMAND_DOCS}\n\n{SYSTEM_SUFFIX}'
    else:
        return f'{SYSTEM_PREFIX}\n\n{COMMAND_DOCS}\n\n{SYSTEM_SUFFIX}'


def get_in_context_example() -> str:
    return EXAMPLES


class CodeActAgent(Agent):
    VERSION = '1.7'
    """
    The Code Act Agent is a minimalist agent.
    The agent works by passing the model a list of action-observation pairs and prompting the model to take the next step.

    ### Overview

    This agent implements the CodeAct idea ([paper](https://arxiv.org/abs/2402.13463), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) that consolidates LLM agents’ **act**ions into a unified **code** action space for both *simplicity* and *performance* (see paper for more details).

    The conceptual idea is illustrated below. At each turn, the agent can:

    1. **Converse**: Communicate with humans in natural language to ask for clarification, confirmation, etc.
    2. **CodeAct**: Choose to perform the task by executing code
    - Execute any valid Linux `bash` command
    - Execute any valid `Python` code with [an interactive Python interpreter](https://ipython.org/). This is simulated through `bash` command, see plugin system below for more details.

    ![image](https://github.com/OpenDevin/OpenDevin/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

    ### Plugin System

    To make the CodeAct agent more powerful with only access to `bash` action space, CodeAct agent leverages OpenDevin's plugin system:
    - [Jupyter plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/jupyter): for IPython execution via bash command
    - [SWE-agent tool plugin](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/swe_agent_commands): Powerful bash command line tools for software development tasks introduced by [swe-agent](https://github.com/princeton-nlp/swe-agent).

    ### Demo

    https://github.com/OpenDevin/OpenDevin/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

    *Example of CodeActAgent with `gpt-4-turbo-2024-04-09` performing a data science task (linear regression)*

    ### Work-in-progress & Next step

    [] Support web-browsing
    [] Complete the workflow for CodeAct agent to submit Github PRs

    """

    sandbox_plugins: list[PluginRequirement] = [
        # NOTE: AgentSkillsRequirement need to go before JupyterRequirement, since
        # AgentSkillsRequirement provides a lot of Python functions,
        # and it needs to be initialized before Jupyter for Jupyter to use those functions.
        AgentSkillsRequirement(),
        JupyterRequirement(),
    ]
    runtime_tools: list[RuntimeTool] = [RuntimeTool.BROWSER]

    system_message: str = get_system_message()
    in_context_example: str = f"Here is an example of how you can interact with the environment for task solving:\n{get_in_context_example()}\n\nNOW, LET'S START!"

    action_parser = CodeActResponseParser()

    def __init__(
        self,
        llm: LLM,
    ) -> None:
        """
        Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)
        self.attempts_to_condense = 2
        self.reset()

    def reset(self) -> None:
        """
        Resets the CodeAct Agent.
        """
        super().reset()

    def step(self, state: State) -> Action:
        """
        Performs one step using the CodeAct Agent.
        This includes gathering info on previous steps and prompting the model to make a command to execute.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - CmdRunAction(command) - bash command to run
        - IPythonRunCellAction(code) - IPython code to run
        - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
        """
        messages: list[dict[str, str]] = [
            {'role': 'system', 'content': self.system_message},
            {'role': 'user', 'content': self.in_context_example},
        ]

        for prev_action, obs in state.history:
            action_message = get_action_message(prev_action)
            if action_message:
                messages.append(action_message)

            obs_message = get_observation_message(obs)
            if obs_message:
                messages.append(obs_message)

        latest_user_message = [m for m in messages if m['role'] == 'user'][-1]
        if latest_user_message:
            if latest_user_message['content'].strip() == '/exit':
                return AgentFinishAction()
            latest_user_message['content'] += (
                f'\n\nENVIRONMENT REMINDER: You have {state.max_iterations - state.iteration} turns left to complete the task. When finished reply with <finish></finish>.'
            )

        with open('output.txt', 'a') as file:
            file.write('Length of messsages' + str(len(messages)) + '\n')
            file.write(
                'No of tokens, ' + str(self.llm.get_token_count(messages)) + '\n'
            )
            for message in messages[max(len(messages) - 3, 0) :]:
                file.write('Role: ' + message['role'] + '\n')
                file.write('Content: ' + message['content'] + '\n\n')

        # TODO: Make function to count no of tokens , and define the exception

        response = None
        # give it multiple chances to get a response
        # if it fails, we'll try to condense memory
        attempt = 0
        while not response and attempt < self.attempts_to_condense:
            try:
                response = self.llm.completion(
                    messages=messages,
                    stop=[
                        '</execute_ipython>',
                        '</execute_bash>',
                        '</execute_browse>',
                    ],
                    temperature=0.0,
                )
                print('Response: ', response)
            # except:
            #     pass
            except Exception as e:
                # Handle the specific exception
                print(f'An error occurred: {e}')
            #     if is_context_overflow_error(e):
            #     # A separate API call to run a summarizer
            #     self.summarize_messages_inplace()

            #     # Try step again
            #     return self.step(user_message, first_message=first_message, return_dicts=return_dicts)
            # else:
            #     printd(f"step() failed with an unrecognized exception: '{str(e)}'")
            #     raise e
            # TODO: Manage the response for exception.

        return self.action_parser.parse(response)

    def summarize_messages_inplace(
        self,
        messages: list[dict],
        #    cutoff=None,
        #    preserve_last_N_messages=True,
        #    disallow_tool_as_first=True
    ):
        # assert self.messages[0]["role"] == "system", f"self.messages[0] should be system (instead got {self.messages[0]})"

        # Start at index 1 (past the system message),
        # and collect messages for summarization until we reach the desired truncation token fraction (eg 50%)
        # Do not allow truncation of the last N messages, since these are needed for in-context examples of function calling

        # TODO: Check the functioning of this get_token_count function.
        token_counts = [self.llm.get_token_count(message) for message in messages]

        message_buffer_token_count = sum(token_counts[1:])  # no system message
        MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC = 0.75
        desired_token_count_to_summarize = int(
            message_buffer_token_count * MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC
        )
        candidate_messages_to_summarize = messages[1:]
        token_counts = token_counts[1:]

        # TODO: Add functionality for preserving last N messages
        MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST = 3
        # if preserve_last_N_messages:
        #     candidate_messages_to_summarize = candidate_messages_to_summarize[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]
        #     token_counts = token_counts[:-MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST]

        print(f'MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC={MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC}')
        print(f'MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST={MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST}')
        print(f'token_counts={token_counts}')
        print(f'message_buffer_token_count={message_buffer_token_count}')
        print(f'desired_token_count_to_summarize={desired_token_count_to_summarize}')
        print(
            f'len(candidate_messages_to_summarize)={len(candidate_messages_to_summarize)}'
        )

        if len(candidate_messages_to_summarize) == 0:
            raise SummarizeError(
                f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(messages)}, preserve_N={MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST}]"
            )

        tokens_so_far = 0
        cutoff = 0
        for i, msg in enumerate(candidate_messages_to_summarize):
            cutoff = i
            tokens_so_far += token_counts[i]
            if tokens_so_far > desired_token_count_to_summarize:
                break
        # Account for system message
        cutoff += 1

        # Try to make an assistant message come after the cutoff
        try:
            print(f"Selected cutoff {cutoff} was a 'user', shifting one...")
            if messages[cutoff]['role'] == 'user':
                new_cutoff = cutoff + 1
                if messages[new_cutoff]['role'] == 'user':
                    print(f"Shifted cutoff {new_cutoff} is still a 'user', ignoring...")
                cutoff = new_cutoff
        except IndexError:
            pass

        # TODO: Customize this function to be used by OpenDevin.
        # # Make sure the cutoff isn't on a 'tool' or 'function'
        # if disallow_tool_as_first:
        #     while self.messages[cutoff]["role"] in ["tool", "function"] and cutoff < len(self.messages):
        #         printd(f"Selected cutoff {cutoff} was a 'tool', shifting one...")
        #         cutoff += 1

        message_sequence_to_summarize = messages[
            1:cutoff
        ]  # do NOT get rid of the system message
        if len(message_sequence_to_summarize) <= 1:
            # This prevents a potential infinite loop of summarizing the same message over and over
            raise SummarizeError(
                f"Summarize error: tried to run summarize, but couldn't find enough messages to compress [len={len(message_sequence_to_summarize)} <= 1]"
            )
        else:
            print(
                f'Attempting to summarize {len(message_sequence_to_summarize)} messages [1:{cutoff}] of {len(messages)}'
            )

        # TODO: (Check) I don't think this is needed because max_tokens is already define in opendevin.
        # We can't do summarize logic properly if max_input_tokens is undefined
        # if self.agent_state.llm_config.context_window is None:
        #     # Fallback if for some reason context_window is missing, just set to the default
        #     print(f"{CLI_WARNING_PREFIX}could not find context_window in config, setting to default {LLM_MAX_TOKENS['DEFAULT']}")
        #     print(f"{self.agent_state}")
        #     self.agent_state.llm_config.context_window = (
        #         LLM_MAX_TOKENS[self.model] if (self.model is not None and self.model in LLM_MAX_TOKENS) else LLM_MAX_TOKENS["DEFAULT"]
        #     )

        # TODO: Define summarize messages function
        # summary = summarize_messages(agent_state=self.agent_state, message_sequence_to_summarize=message_sequence_to_summarize)
        # print(f"Got summary: {summary}")

        # TODO: Look into this
        # # Metadata that's useful for the agent to see
        # all_time_message_count = self.messages_total
        # remaining_message_count = len(self.messages[cutoff:])
        # hidden_message_count = all_time_message_count - remaining_message_count
        # summary_message_count = len(message_sequence_to_summarize)
        # summary_message = package_summarize_message(summary, summary_message_count, hidden_message_count, all_time_message_count)
        # print(f"Packaged into message: {summary_message}")

        # prior_len = len(self.messages)
        # self._trim_messages(cutoff)
        # packed_summary_message = {"role": "user", "content": summary_message}
        # self._prepend_to_messages(
        #     [
        #         Message.dict_to_message(
        #             agent_id=self.agent_state.id,
        #             user_id=self.agent_state.user_id,
        #             model=self.model,
        #             openai_message_dict=packed_summary_message,
        #         )
        #     ]
        # )

        # # reset alert
        # self.agent_alerted_about_memory_pressure = False

        # print(f"Ran summarizer, messages length {prior_len} -> {len(self.messages)}")

        return messages

    def search_memory(self, query: str) -> list[str]:
        raise NotImplementedError('Implement this abstract method')
