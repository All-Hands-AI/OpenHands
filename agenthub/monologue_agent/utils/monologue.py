import agenthub.monologue_agent.utils.json as json
import agenthub.monologue_agent.utils.prompts as prompts
from opendevin.core.exceptions import AgentEventTypeError
from opendevin.core.logger import opendevin_logger as logger
from opendevin.llm.llm import LLM


class Monologue:
    """
    The monologue is a representation for the agent's internal monologue where it can think.
    The agent has the capability of using this monologue for whatever it wants.
    """

    def __init__(self):
        """
        Initialize the empty list of thoughts
        """
        self.thoughts = []

    def add_event(self, t: dict):
        """
        Adds an event to memory if it is a valid event.

        Parameters:
        - t (dict): The thought that we want to add to memory

        Raises:
        - AgentEventTypeError: If t is not a dict
        """
        if not isinstance(t, dict):
            raise AgentEventTypeError()
        self.thoughts.append(t)

    def get_thoughts(self):
        """
        Get the current thoughts of the agent.

        Returns:
        - List: The list of thoughts that the agent has.
        """
        return self.thoughts

    def get_total_length(self):
        """
        Gives the total number of characters in all thoughts

        Returns:
        - Int: Total number of chars in thoughts.
        """
        total_length = 0
        for t in self.thoughts:
            try:
                total_length += len(json.dumps(t))
            except TypeError as e:
                logger.error('Error serializing thought: %s', str(e), exc_info=False)
        return total_length

    def condense(self, llm: LLM):
        """
        Attempts to condense the monologue by using the llm

        Parameters:
        - llm (LLM): llm to be used for summarization

        Raises:
        - Exception: the same exception as it got from the llm or processing the response
        """

        try:
            prompt = prompts.get_summarize_monologue_prompt(self.thoughts)
            messages = [{'content': prompt, 'role': 'user'}]
            resp = llm.completion(messages=messages)
            summary_resp = resp['choices'][0]['message']['content']
            self.thoughts = prompts.parse_summary_response(summary_resp)
        except Exception as e:
            logger.error('Error condensing thoughts: %s', str(e), exc_info=False)

            # TODO If the llm fails with ContextWindowExceededError, we can try to condense the monologue chunk by chunk
            raise
