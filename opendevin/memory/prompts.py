from opendevin.core.exceptions import (
    InvalidSummaryResponseError,
    LLMMalformedActionError,
    LLMResponseError,
)
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.utils import json
from opendevin.events.action.agent import AgentSummarizeAction
from opendevin.events.event import EventSource
from opendevin.events.serialization.action import action_from_dict

SUMMARY_PROMPT = """
Given the following actions and observations, create a JSON response with:
    - "action": "summarize"
    - args:
      - "summarized_actions": A sentence summarizing all the provided actions, at first person
      - "summarized observations": A few sentences summarizing all the provided observations, at third person

Example:
        {
            "action": "summarize",
            "args": {
                "summarized_actions": "I opened the uml file.",
                "summarized observations": "The agent ran a python script to open the uml.pdf file."
            }
        }
Make sure to include in observations any relevant information that the agent should remember.
%(events)s
"""


def get_summarize_prompt(events: list[dict]) -> str:
    """
    Gets the prompt for summarizing the events

    Returns:
    - A formatted string with the current events within the prompt
    """
    return SUMMARY_PROMPT % {
        'events': json.dumps(events, indent=2),
    }


def parse_summary_response(response: str) -> AgentSummarizeAction:
    """
    Parses a JSON summary of events.

    Parameters:
    - response: The response string to be parsed
    Returns:
    - The summary action output by the model
    """
    try:
        action_dict = json.loads(response)
        action = action_from_dict(action_dict)
        if action is None or not isinstance(action, AgentSummarizeAction):
            error_message = f'Expected a summarize action, but the response got {str(type(action)) if action else None}'
            logger.error(error_message)
            raise InvalidSummaryResponseError(error_message)
        action._source = EventSource.AGENT  # type: ignore
    except (LLMResponseError, LLMMalformedActionError) as e:
        logger.error(f'Failed to parse summary response: {e}')
        raise InvalidSummaryResponseError(
            'Failed to parse the response: {str(e)}'
        ) from e
    return action
