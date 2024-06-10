from opendevin.core.exceptions import LLMResponseError
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.utils import json
from opendevin.events.action.agent import (
    AgentDelegateSummaryAction,
    AgentSummarizeAction,
)
from opendevin.events.serialization.action import action_from_dict

SUMMARY_PROMPT = """
Given the following actions and observations, create a JSON response with:
    - "action": "summarize"
    - args:
      - "summarized_actions": A comma-separated list of unique action names from the provided actions
      - "summary": A single sentence summarizing all the provided observations
"""

DELEGATE_SUMMARY_PROMPT = """
The delegate agent "%(delegate_agent)s" was assigned the task: "%(delegate_task)s".
Given the following actions and observations performed by the delegate, create a JSON response with:
    - "action": "summarize_delegate"
    - "args":
      - "summary": A concise summary of the delegate's activities and findings, focusing on the key information relevant to the delegator.
      - "relevant_info": A list of key points or information that the delegator might need to know or can find in the delegate's detailed history if needed.

Delegate's actions and observations:
"""


def get_summarize_prompt(events: list[dict]) -> str:
    """
    Gets the prompt for summarizing a chunk of events.

    Returns:
    - A formatted string with the events within the prompt
    """
    events_str = '\n'.join(json.dumps(events, indent=2))
    return SUMMARY_PROMPT + events_str


def get_delegate_summarize_prompt(
    delegate_events: list[dict], delegate_agent: str, delegate_task: str
) -> str:
    """
    Gets the prompt for summarizing a delegate's events.

    Returns:
    - A formatted string with the delegate's events within the prompt
    """
    events_str = '\n'.join(json.dumps(delegate_events, indent=2))
    return (
        DELEGATE_SUMMARY_PROMPT
        % {
            'delegate_agent': delegate_agent,
            'delegate_task': delegate_task,
        }
        + events_str
    )


def parse_summary_response(response: str) -> AgentSummarizeAction:
    """
    Parses a JSON summary of events.

    Parameters:
    - response: The response string to be parsed
    Returns:
    - The summary action output by the model
    """
    action_dict = json.loads(response)
    action = action_from_dict(action_dict)
    if action is None or not isinstance(action, AgentSummarizeAction):
        logger.error(
            f"Expected 'summarize' action, got {str(type(action)) if action else None}"
        )
        raise LLMResponseError(
            'Expected a summarize action, but the LLM response was invalid'
        )
    return action


def parse_delegate_summary_response(response: str) -> AgentDelegateSummaryAction:
    """
    Parses a JSON summary of a delegate's events.

    Parameters:
    - response: The response string to be parsed
    Returns:
    - The summary action output by the model
    """
    action_dict = json.loads(response)
    action = action_from_dict(action_dict)
    if action is None or not isinstance(action, AgentDelegateSummaryAction):
        logger.error(
            f"Expected 'summarize_delegate' action, got {str(type(action)) if action else None}"
        )
        raise LLMResponseError(
            'Expected a summarize_delegate action, but the LLM response was invalid'
        )
    return action
