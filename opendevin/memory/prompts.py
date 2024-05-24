from opendevin.core.exceptions import LLMOutputError
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.utils import json
from opendevin.events.action.agent import AgentSummarizeAction
from opendevin.events.serialization.action import action_from_dict

SUMMARY_PROMPT = """
Below is a list of events representing the history of an automated agent. Each event is an item in a JSON array.
The events may be memories, actions taken by the agent, or outputs from those actions.

Please return a new, much smaller JSON array that summarizes the events. When summarizing, you should condense the events that appear
earlier in the list more aggressively, while preserving more details for the events that appear later in the list.

You can summarize individual events, and you can condense related events together with a description of their content.

%(events)s

Make the summaries as concise and informative as possible, especially for the earlier events in the list.
Be specific about what happened and what was learned. The summary will be used as keywords for searching for the original event.
Be sure to preserve any key words or important information.

Your response must be in JSON format. Each entry in the new monologue must have an `action` key, and an `args` key.
You can add a summarized entry with `action` set to "summarize" and a concise summary in `args.summary`.
You can also use the source event if relevant, with its original `action` and `args`.

It must be an object with the key `summarized_events`, which must be a smaller JSON array containing the summarized events.
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
    Parses a summary of the events

    Parameters:
    - response: The response string to be parsed

    Returns:
    - The list of summarized events output by the model
    """
    action_dict = json.loads(response)
    action = action_from_dict(action_dict)
    if action is None or not isinstance(action, AgentSummarizeAction):
        logger.error(
            f"Expected 'summarize' action, got {str(type(action)) if action else None}"
        )
        raise LLMOutputError(
            'Expected a summarize action, but the LLM response was invalid'
        )

    # the summarize action should have a 'summary' key
    # FIXME what kind of errors should we have or how lenient can we be?

    return action
