from litellm.exceptions import ContextWindowExceededError

from opendevin.core.logger import opendevin_logger as logger
from opendevin.llm.llm import LLM

MAX_TOKEN_COUNT_PADDING = 16000


class MemoryCondenser:
    """
    Condenses the prompt with a call to the LLM.
    """

    def needs_condense(self, llm: LLM, action_prompt: str, events: list) -> bool:
        """
        Checks if the prompt needs to be condensed based on the token count against the limits of the llm passed in the call.

        Parameters:
        - llm (LLM): The llm to be used for token count.
        - action_prompt (str): The initial action prompt.

        Returns:
        - bool: True if the prompt needs to be condensed, False otherwise.
        """

        # get prompt token length
        messages = [{'content': action_prompt, 'role': 'user'}]
        token_count = llm.get_token_count(messages)

        # test against token limits of this llm
        if token_count + MAX_TOKEN_COUNT_PADDING < llm.max_input_tokens:
            return False

        return True

    def condense(
        self,
        llm: LLM,
        recent_events: list[dict],
        action_prompt: str,
        summarize_prompt: str = None,
    ) -> tuple[str, bool]:
        """
        Attempts to condense the monologue by using the llm, if necessary. Returns unmodified prompt if it is already short enough.

        Condenses the monologue with action and summary prompts using the llm when necessary.
        First checks if the action_prompt (including events) needs condensation based on token count.
        If needed, uses summarize_prompt and events to condense in manageable chunks.

        Parameters:
        - llm (LLM): LLM to be used for summarization.
        - action_prompt (str): Initial check action prompt.
        - summarize_prompt (str): Starting string for summarization if needed.
        - events (list): List of events to be condensed.

        Returns:
        - tuple: A tuple containing the condensed string and a boolean indicating if condensation was performed.
        """

        # test prompt token length
        if not self.needs_condense(llm, action_prompt, recent_events):
            return action_prompt, False

        try:
            # send the summarize prompt to the llm
            messages = [{'content': summarize_prompt, 'role': 'user'}]
            resp = llm.completion(messages=messages)
            summary_response = resp['choices'][0]['message']['content']
            return summary_response, True
        except ContextWindowExceededError:
            # this is a subclass of InvalidRequestError in litellm exceptions
            # it applies only to some (albeit apparently most) llm providers
            # for bedrock, vertexai, sagemaker it's documented to be an InvalidRequestError directly instead
            try:
                return self.process_in_chunks(
                    llm, summarize_prompt, recent_events
                ), True
            except Exception as e:
                logger.error(
                    'Error in chunk-by-chunk condensation: %s', str(e), exc_info=False
                )
                raise

        except Exception as e:
            logger.error('Error condensing history: %s', str(e), exc_info=False)
            raise

    def process_in_chunks(
        self, llm: LLM, initial_prompt: str, recent_events: list[dict]
    ) -> str:
        """
        Processes the prompt in chunks, attempting to keep each chunk within the llm's max token count.

        Parameters:
        - llm (LLM): The llm to use for processing.
        - initial_prompt (str): The initial prompt used for the beginning of the summarization.
        - events (list): The events to be included in the summarization.

        Returns:
        - str: The summarized result of processing in chunks.
        """
        chunk = []
        summarized_parts = [initial_prompt]  # Start with the initial prompt for summary
        token_limit = self.get_token_limit(llm)

        # naive approach
        # use the summarize prompt for summarization call
        # messages = [{'content': summarize_prompt, 'role': 'user'}]
        # resp = llm.completion(messages=messages)
        # summary_response = resp['choices'][0]['message']['content']

        current_count = llm.get_token_count(
            [{'content': initial_prompt, 'role': 'user'}]
        )

        for event in recent_events:
            event_count = llm.get_token_count([{'content': event, 'role': 'user'}])
            if current_count + event_count >= token_limit:
                # Process the current chunk
                messages = [{'content': ' '.join(chunk), 'role': 'user'}]
                response = llm.completion(messages=messages)
                summarized_parts.append(response['choices'][0]['message']['content'])
                chunk = []  # Reset chunk
                current_count = llm.get_token_count(
                    [{'content': initial_prompt, 'role': 'user'}]
                )  # Reset token count
            chunk.append(event)
            current_count += event_count

        if chunk:  # Handle any remaining events in the last chunk
            messages = [{'content': ' '.join(chunk), 'role': 'user'}]
            response = llm.completion(messages=messages)
            summarized_parts.append(response['choices'][0]['message']['content'])

        return ' '.join(summarized_parts)

    def get_token_limit(self, llm: LLM) -> int:
        """
        Returns the token limit to use for the llm passed in the call.

        Parameters:
        - llm (LLM): The llm to get the token limit from.

        Returns:
        - int: The token limit of the llm.
        """
        return llm.max_input_tokens - MAX_TOKEN_COUNT_PADDING
