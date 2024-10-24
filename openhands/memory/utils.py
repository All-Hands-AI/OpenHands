import openhands.core.utils.json as json
from openhands.core.exceptions import (
    InvalidSummaryResponseError,
    LLMMalformedActionError,
    LLMResponseError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.agent import AgentSummarizeAction
from openhands.events.event import EventSource
from openhands.events.serialization.event import action_from_dict


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
        action.summary = (
            action.summarized_actions + '\n' + action.summarized_observations
        )
    except (LLMResponseError, LLMMalformedActionError) as e:
        logger.error(f'Failed to parse summary response: {str(e)}')
        raise InvalidSummaryResponseError(
            f'Failed to parse the response: {str(e)}'
        ) from e
    return action
