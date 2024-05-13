from typing import Callable

from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.utils import json
from opendevin.llm.llm import LLM

MAX_TOKEN_COUNT_PADDING = 16000


class MemoryCondenser:
    """
    Condenses the prompt with a call to the LLM.
    """

    def __init__(
        self,
        action_prompt: Callable[..., str],
        action_prompt_with_defaults: Callable[..., str],
        summarize_prompt: Callable[[list[dict], list[dict]], str],
    ):
        """
        Initialize the MemoryCondenser with the action and summarize prompts.

        Parameters:
        - action_prompt (Callable): The function to generate an action prompt. The function should accept core events and recent events as arguments.
        - summarize_prompt (Callable): The function to generate a summarize prompt. The function should accept core events and recent events as arguments.
        """
        self.action_prompt = action_prompt
        self.action_prompt_with_defaults = action_prompt_with_defaults
        self.summarize_prompt = summarize_prompt

    def condense(
        self,
        llm: LLM,
        default_events: list[dict],
        recent_events: list[dict],
        background_commands: list,
    ) -> tuple[str, bool]:
        """
        Attempts to condense the recent events of the monologue by using the llm, if necessary. Returns unmodified prompt if it is already short enough.

        It includes default events for context, but does not alter them.
        Condenses the monologue with action and summary prompts using the llm when necessary.
        Checks if the action_prompt (including events) needs condensation based on token count, and doesn't attempt condensing if not.

        Parameters:
        - llm (LLM): LLM to be used for summarization.
        - default_events (list[dict]): List of default events that should remain unchanged.
        - recent_events (list[dict]): List of recent events that may be condensed.

        Returns:
        - tuple: A tuple containing the condensed string, or the unmodified string if it wasn't performed, and a boolean indicating if condensation was performed.
        """

        action_prompt = self.action_prompt(
            'task', default_events, recent_events, background_commands
        )
        summarize_prompt = self.summarize_prompt(default_events, recent_events)

        # test prompt token length
        if not self.needs_condense(llm, default_events, recent_events):
            return action_prompt, False

        try:
            return self.process_in_chunks(llm, default_events, recent_events), True
        except Exception as e:
            logger.error('Condensation failed: %s', str(e), exc_info=False)
            return action_prompt, False

    def needs_condense(
        self, llm: LLM, default_events: list[dict], recent_events: list[dict]
    ) -> bool:
        """
        Checks if the prompt needs to be condensed based on the token count against the limits of the llm passed in the call.

        Parameters:
        - llm (LLM): The llm to use for checking the token count.
        - default_events (list[dict]): List of core events that should remain unchanged.
        - recent_events (list[dict]): List of recent events that may be condensed.

        Returns:
        - bool: True if the prompt needs to be condensed, False otherwise.
        """
        action_prompt = self.action_prompt(default_events, recent_events)
        combined_prompt = (
            action_prompt
            + ' '
            + json.dumps(default_events)
            + ' '
            + json.dumps(recent_events)
        )
        token_count = llm.get_token_count(
            [{'content': combined_prompt, 'role': 'user'}]
        )
        return token_count >= self.get_token_limit(llm)

    def process_in_chunks(
        self,
        llm: LLM,
        default_events: list[dict],
        recent_events: list[dict],
    ) -> str:
        """
        Condenses recent events in chunks, while preserving core events for context.
        """
        # Initial part of the prompt includes default memories for context
        initial_prompt = self.action_prompt_with_defaults(default_events=default_events)
        return self.attempt_condense(
            llm, default_events, recent_events, initial_prompt, 0
        )

    def attempt_condense(
        self,
        llm: LLM,
        default_events: list[dict],
        recent_events: list[dict],
        action_prompt: str,
        attempt_count: int,
    ) -> str:
        if attempt_count >= 5 or not recent_events:
            raise Exception('Condensation attempts exceeded without success.')

        # get the summarize prompt to use
        summarize_prompt = self.summarize_prompt(default_events, recent_events)

        # Split events into two halves
        midpoint = len(recent_events) // 2
        first_half = recent_events[:midpoint]
        second_half = recent_events[midpoint:]

        # Try to condense the first half
        condensed_summary = self.process_events(
            llm,
            default_events=default_events,
            recent_events=first_half,
            summarize_prompt=summarize_prompt,
        )
        new_prompt = f'{action_prompt} {condensed_summary}'
        new_token_count = llm.get_token_count([{'content': new_prompt, 'role': 'user'}])

        if new_token_count < self.get_token_limit(llm):
            return new_prompt  # Condensed successfully
        else:
            # If not successful, attempt to condense the second half
            return self.attempt_condense(
                llm=llm,
                default_events=default_events,
                recent_events=second_half,
                action_prompt=new_prompt,
                attempt_count=attempt_count + 1,
            )

    def process_events(
        self,
        llm: LLM,
        default_events: list[dict],
        recent_events: list[dict],
        summarize_prompt: str,
    ) -> str:
        """
        Processes a list of events by converting them into a single string representation and sending it to the LLM for condensation.

        Parameters:
        - llm (LLM): The LLM to use for processing the events.
        - recent_events (list[dict]): The events to be processed, where each event is a dictionary containing various attributes.
        - summarize_prompt (str): The initial prompt used for summarization.

        Returns:
        - str: The summarized result of processing the events.
        """
        # apply the prompt template to the events
        summarize_prompt = self.summarize_prompt(default_events, recent_events)

        # send the combined prompt to the LLM
        messages = [{'content': f'{summarize_prompt}', 'role': 'user'}]
        response = llm.completion(messages=messages)
        return response['choices'][0]['message']['content']

    def get_token_limit(self, llm: LLM) -> int:
        """
        Returns the token limit to use for the llm passed in the call.

        Parameters:
        - llm (LLM): The llm to get the token limit from.

        Returns:
        - int: The token limit of the llm.
        """
        return llm.max_input_tokens - MAX_TOKEN_COUNT_PADDING
