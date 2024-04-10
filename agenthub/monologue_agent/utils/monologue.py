import traceback
from opendevin.llm.llm import LLM
from typing import Any
import agenthub.monologue_agent.utils.json as json
import agenthub.monologue_agent.utils.prompts as prompts


class Monologue:
    """
    The monologue is a representation for the agent's internal monologue where it can think.
    The agent has the capability of using this monologue for whatever it wants.
    """

    def __init__(self) -> None:
        """
        Initialize the empty list of thoughts
        """
        self.thoughts: list[dict[str, Any]] = []

    def add_event(self, t: dict[str, Any]) -> None:
        """
        Adds an event to memory if it is a valid event.

        Parameters:
        - t (dict): The thought that we want to add to memory

        Raises:
        - ValueError: If t is not a dict
        """
        if not isinstance(t, dict):
            raise ValueError('Event must be a dictionary')
        self.thoughts.append(t)

    def get_thoughts(self) -> list[dict[str, Any]]:
        """
        Get the current thoughts of the agent.

        Returns:
        - List: The list of thoughts that the agent has.
        """
        return self.thoughts

    def get_total_length(self) -> int:
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
                print(f'Error serializing thought: {e}')
        return total_length

    def condense(self, llm: LLM) -> None:
        """
        Attempts to condense the monologue by using the llm

        Parameters:
        - llm (LLM): llm to be used for summarization

        Raises:
        - RunTimeError: When the condensing process fails for any reason
        """

        try:
            prompt = prompts.get_summarize_monologue_prompt(self.thoughts)
            messages = [{'content': prompt, 'role': 'user'}]
            resp = llm.completion(messages=messages)
            summary_resp = resp['choices'][0]['message']['content']
            self.thoughts = prompts.parse_summary_response(
                strip_markdown(summary_resp))
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f'Error condensing thoughts: {e}')


def strip_markdown(markdown_json: str) -> str:
    # remove markdown code block
    return markdown_json.replace('```json\n', '').replace('```', '').strip()
