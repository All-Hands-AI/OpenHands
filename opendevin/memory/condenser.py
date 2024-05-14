from typing import Callable

from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.utils import json
from opendevin.llm.llm import LLM

MAX_TOKEN_COUNT_PADDING = 127000  # FIXME debug value


class MemoryCondenser:
    """
    Condenses the prompt with a call to the LLM.
    """

    def __init__(
        self,
        action_prompt: Callable[..., str],
        summarize_prompt: Callable[[list[dict], list[dict]], str],
    ):
        """
        Initialize the MemoryCondenser with the action and summarize prompts.

        action_prompt is a callable that returns the prompt that is about to be sent to the LLM.
        The prompt callable will be called with default events and recent events as arguments.
        summarize_prompt, which is optional, is a callable that returns a specific prompt to tell the LLM to summarize the recent events.
        The prompt callable will be called with default events and recent events as arguments.

        Parameters:
        - action_prompt (Callable): The function to generate an action prompt. The function should accept core events and recent events as arguments.
        - summarize_prompt (Callable): The function to generate a summarize prompt. The function should accept core events and recent events as arguments.
        """
        self.action_prompt = action_prompt
        self.summarize_prompt = summarize_prompt

    def condense(
        self,
        llm: LLM,
        default_events: list[dict],
        recent_events: list[dict],
        background_commands: list = None,
    ) -> list[dict] | bool:
        """
        Attempts to condense the recent events of the monologue by using the llm, if necessary. Returns the condensed recent events if successful, or False if not.

        It includes default events in the prompt for context, but does not alter them.
        Condenses the monologue using a summary prompt.
        Checks if the action_prompt (including events) needs condensation based on token count, and doesn't attempt condensing if not.
        Returns unmodified list of recent events if it is already short enough.

        Parameters:
        - llm (LLM): LLM to be used for summarization.
        - default_events (list[dict]): List of default events that should remain unchanged.
        - recent_events (list[dict]): List of recent events that may be condensed.
        - background_commands (list): List of background commands to be included in the prompt.

        Returns:
        - list[dict] | bool: The condensed recent events if successful, unmodified list if unnecessary, or False if condensation failed.
        """

        if not background_commands:
            background_commands = []

        # generate the action prompt with the default and recent events
        action_prompt = self.action_prompt(
            '', default_events, recent_events, background_commands
        )

        # test prompt token length
        if not self.needs_condense(llm, action_prompt):
            return recent_events

        try:
            # try 3 times to condense
            attempt_count = 0
            failed = False

            while attempt_count < 3 and not failed:
                # attempt to condense the recent events
                new_recent_events = self.attempt_condense(
                    llm, default_events, recent_events
                )

                if not new_recent_events:
                    logger.debug('Condensation failed: new_recent_events is empty')
                    return False

                # re-generate the action prompt with the condensed events
                new_action_prompt = self.action_prompt(
                    '', default_events, new_recent_events, background_commands
                )

                # check if the new prompt still needs to be condensed
                if self.needs_condense(llm, new_action_prompt):
                    attempt_count += 1
                    continue

                # the new prompt is within the token limit
                return new_recent_events

        except Exception as e:
            logger.error('Condensation failed: %s', str(e), exc_info=False)
            return False
        return False

    def attempt_condense(
        self,
        llm: LLM,
        default_events: list[dict],
        recent_events: list[dict],
    ) -> list[dict] | None:
        # Split events
        midpoint = len(recent_events) // 2
        first_half = recent_events[:midpoint]
        second_half = recent_events[midpoint:]

        # attempt to condense the first half of the recent events
        summarize_prompt = self.summarize_prompt(default_events, first_half)

        # send the summarize prompt to the LLM
        messages = [{'content': summarize_prompt, 'role': 'user'}]
        response = llm.completion(messages=messages)
        response_content = response['choices'][0]['message']['content']
        parsed_summary = json.loads(response_content)

        # the new list of recent events will be source events or summarize actions
        # in the 'new_monologue' key
        condensed_events = parsed_summary['new_monologue']

        # new recent events list
        if (
            not condensed_events
            or not isinstance(condensed_events, list)
            or len(condensed_events) == 0
        ):
            return None

        condensed_events.extend(second_half)
        return condensed_events

    def needs_condense(self, llm: LLM, action_prompt: str) -> bool:
        """
        Checks if the prompt needs to be condensed based on the token count against the limits of the llm passed in the call.

        Parameters:
        - llm (LLM): The llm to use for checking the token count.
        - action_prompt (str): The prompt to check for token count.

        Returns:
        - bool: True if the prompt needs to be condensed, False otherwise.
        """

        token_count = llm.get_token_count([{'content': action_prompt, 'role': 'user'}])
        return token_count >= self.get_token_limit(llm)

    def get_token_limit(self, llm: LLM) -> int:
        """
        Returns the token limit to use for the llm passed in the call.

        Parameters:
        - llm (LLM): The llm to get the token limit from.

        Returns:
        - int: The token limit of the llm.
        """
        return llm.max_input_tokens - MAX_TOKEN_COUNT_PADDING
