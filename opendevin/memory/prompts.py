from opendevin.core.exceptions import (
    AgentMalformedActionError,
    InvalidSummaryResponseError,
    LLMOutputError,
)
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.utils import json
from opendevin.events.action.agent import AgentSummarizeAction
from opendevin.events.serialization.action import action_from_dict

SUMMARY_PROMPT = """
Given the following actions and observations, create a JSON response with:
    - "action": "summarize"
    - args:
      - "summarized_actions": A comma-separated list of unique action names from the provided actions
      - "summary": A single sentence summarizing all the provided observations
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
    except (LLMOutputError, AgentMalformedActionError) as e:
        logger.error(f'Failed to parse summary response: {e}')
        raise InvalidSummaryResponseError(
            'Failed to parse the response: {str(e)}'
        ) from e
    return action
