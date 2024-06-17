from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.agent import (
    AgentFinishAction,
    AgentRecallAction,
    AgentSummarizeAction,
)
from opendevin.events.action.browse import BrowseInteractiveAction, BrowseURLAction
from opendevin.events.action.commands import (
    CmdKillAction,
    CmdRunAction,
    IPythonRunCellAction,
)
from opendevin.events.action.files import FileReadAction, FileWriteAction
from opendevin.events.action.message import MessageAction
from opendevin.events.event import Event, EventSource
from opendevin.events.observation.observation import Observation
from opendevin.events.serialization.event import event_to_memory
from opendevin.llm.llm import LLM
from opendevin.memory.history import ShortTermHistory
from opendevin.memory.prompts import get_summarize_prompt, parse_summary_response

MAX_USER_MESSAGE_CHAR_COUNT = 200  # max char count for user messages


class MemoryCondenser:
    """
    Condenses the prompt with a call to the LLM.
    """

    def __init__(
        self,
        llm: LLM,
    ):
        """
        Initialize the MemoryCondenser.

        llm is the language model to use for summarization.
        config.max_input_tokens is an optional configuration setting specifying the maximum context limit for the LLM.
        If not provided, the condenser will act lazily and only condense when a context window limit error occurs.

        Parameters:
        - llm: The language model to use for summarization.
        """
        self.llm = llm

    def condense(
        self,
        history: ShortTermHistory,
    ) -> AgentSummarizeAction | None:
        """
        Condenses the given list of events using the llm. Returns the condensed list of events. It works one by one.

        Condensation heuristics:
        - Keep initial messages (system, user message setting task, including further tasks after AgentFinishActions)
        - Prioritize more recent history
        - Lazily summarize between initial instruction and most recent, starting with earliest condensable turns
        - Split events into chunks delimited by user message actions, condense each chunk into a sentence
        - If no more chunks of agent actions or observations, summarize individual user messages that exceeed a certain length, except likely tasks

        Parameters:
        - history: short term history

        Returns:
        - AgentSummarizeAction: a summary in a sentence.
        """
        # chunk of actions, observations to summarize
        chunk: list[Event] = []
        chunk_start_id: int | None = None
        last_summarizable_id: int | None = None

        for event in history.get_events():
            # user messages should be kept if possible
            # aside from them, there are some (mostly or firstly) non-summarizable actions
            # like AgentDelegateAction or AgentFinishAction
            if not self._is_summarizable(event):
                if chunk and len(chunk) > 1:
                    # we've just gathered a chunk to summarize
                    summary_action = self._summarize_chunk(chunk)

                    # mypy is happy with assert, and in fact it cannot/should not be None
                    assert chunk_start_id is not None
                    summary_action._chunk_start = chunk_start_id

                    # same here, a gift for mypy during development
                    assert last_summarizable_id is not None
                    summary_action._chunk_end = last_summarizable_id

                    # add it directly to history, so the agent only has to retry the request
                    history.add_summary(summary_action)
                    return summary_action
                else:
                    # reset the chunk if it has just one event
                    chunk = []
                    chunk_start_id = None
                    last_summarizable_id = None
            else:
                # these are the events we want to summarize
                if chunk_start_id is None:
                    chunk_start_id = event.id
                last_summarizable_id = event.id
                chunk.append(event)

        if chunk and len(chunk) > 1:
            summary_action = self._summarize_chunk(chunk)

            # keep mypy happy
            assert chunk_start_id is not None
            summary_action._chunk_start = chunk_start_id

            # same here
            assert last_summarizable_id is not None
            summary_action._chunk_end = (
                last_summarizable_id  # history.get_latest_event_id()
            )
            history.add_summary(summary_action)
            return summary_action

        # no more chunks of agent actions or observations
        # then summarize individual user messages that exceeed a certain length
        # except for the first user message after an AgentFinishAction
        last_event_was_finish = False
        for event in history.get_events():
            if isinstance(event, AgentFinishAction):
                last_event_was_finish = True
            elif isinstance(event, MessageAction) and event.source == EventSource.USER:
                # the message has to be large enough ish, and not a likely task
                if (
                    not last_event_was_finish
                    and len(event.content) > MAX_USER_MESSAGE_CHAR_COUNT
                ):
                    summary_action = self._summarize_chunk([event])
                    summary_action._chunk_start = event.id
                    summary_action._chunk_end = event.id
                    history.add_summary(summary_action)
                    return summary_action
                last_event_was_finish = False
            else:
                last_event_was_finish = False

        return None

    def _summarize_chunk(self, chunk: list[Event]) -> AgentSummarizeAction:
        """
        Summarizes the given chunk of events into a single sentence.

        Parameters:
        - chunk: List of events to summarize.

        Returns:
        - The summary sentence.
        """
        try:
            event_dicts = [event_to_memory(event) for event in chunk]
            prompt = get_summarize_prompt(event_dicts)

            messages = [{'role': 'user', 'content': prompt}]
            response = self.llm.completion(messages=messages)

            action_response = response['choices'][0]['message']['content']
            action = parse_summary_response(action_response)
            return action
        except Exception as e:
            logger.error(f'Failed to summarize chunk: {e}')
            raise

    def _is_summarizable(self, event: Event) -> bool:
        """
        Returns true for actions/observations that can be summarized.
        """
        # non-summarizable actions are special actions like Finish
        # a chunk started by a Delegate action has its own summarization
        # a summarize action itself is currently not summarizable, but it could be included in a future "all old events" summary
        # delegate action/obs should be included in the chunk delimited by them (AgentDelegateAction, ...things,...,AgentDelegateObservation)
        summarizable_events = (
            CmdKillAction,
            CmdRunAction,
            IPythonRunCellAction,
            BrowseURLAction,
            BrowseInteractiveAction,
            FileReadAction,
            FileWriteAction,
            AgentRecallAction,
            MessageAction,
            Observation,
        )

        if isinstance(event, summarizable_events):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                # user messages are not summarized in the first rounds, agent 'chunks' are first
                return False
            return True
        return False
