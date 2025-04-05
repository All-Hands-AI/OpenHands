from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List

from openhands.agenthub.agent_interface import LLMCompletionProvider
from openhands.controller.state.state import State
from openhands.core.message import Message
from openhands.events.event import Event
from openhands.memory.condenser.condenser import Condensation, Condenser, View


class CachingCondenser(Condenser, ABC):
    """Abstract base class for condensers that use prompt caching.

    This class provides a framework for condensers that begin their prompt with the
    whole current prompt, so they can use caching. They then add their own messages
    to instruct the LLM.

    Subclasses need to implement:
    - createCondensationPrompt: Create the prompt for condensation
    - processResponse: Process the LLM response to create a Condensation
    """

    def condense(self, view: View, state: State, agent=None) -> View | Condensation:
        """Condense the events in the view using the agent's LLM.

        This implementation requires an agent that implements the LLMCompletionProvider
        interface to provide access to the agent's LLM and message formatting.

        Args:
            view: The view to condense
            state: The current state
            agent: The agent to use for condensation

        Returns:
            A View or Condensation object
        """
        if not state:
            raise ValueError('CachingCondenser: No state provided, cannot condense')

        if not agent:
            raise ValueError('CachingCondenser: No agent provided, cannot condense')

        # Check if the agent implements the LLMCompletionProvider interface
        if not isinstance(agent, LLMCompletionProvider):
            raise ValueError(
                f'CachingCondenser: Agent {agent.__class__.__name__} does not implement '
                'LLMCompletionProvider interface, cannot condense'
            )

        # Check if the agent's LLM supports caching
        if not agent.llm.is_caching_prompt_active():
            raise ValueError(
                "CachingCondenser: Agent's LLM does not support prompt caching. "
                'This condenser works best with prompt caching enabled.'
            )

        # Check if we should condense
        if not self.should_condense(view):
            return view

        # Do the condensation
        return self._do_condensation(view.events, state, agent)

    def _do_condensation(
        self, events: List[Event], state: State, agent: LLMCompletionProvider
    ) -> Condensation | View:
        """Do a condensation for the given events.

        Args:
            events: The events to condense
            state: The current state
            agent: The agent to use for condensation

        Returns:
            A Condensation or View object
        """
        # Convert events to messages using the agent's method
        base_messages = agent._get_messages(events)

        # Add condensation instructions
        base_messages.append(
            self.createCondensationPrompt(events, state, base_messages)
        )

        # Use the agent's method to build the parameters
        # This ensures that the parameters are consistent with the agent's LLM
        params = agent.build_llm_completion_params(events, state)
        # Now we add our own prompt at the end
        params['messages'] += agent.llm.format_messages_for_llm(
            [self.createCondensationPrompt(events, state, base_messages)]
        )

        # Get the LLM response
        response = agent.llm.completion(**params)
        self.add_metadata('response', response.model_dump())

        # Process the response
        return self.processResponse(events, state, response, base_messages)

    @abstractmethod
    def createCondensationPrompt(
        self, events: List[Event], state: State, base_messages: List[Message]
    ) -> Message:
        """Create the prompt for condensation.

        Args:
            events: The events to condense
            state: The current state
            messages: the messages that are already in the prompt(cached)

        Returns:
            The message with condensation instructions
        """
        pass

    @abstractmethod
    def processResponse(
        self, events: List[Event], state: State, response: Any, messages: List[Message]
    ) -> Condensation | View:
        """Process the LLM response to create a Condensation.

        Args:
            events: The events that were condensed
            state: The current state
            response: The LLM response
            messages: The messages that were already in the prompt(cached)

        Returns:
            A Condensation or View object
        """
        pass

    @abstractmethod
    def should_condense(self, view: View) -> bool:
        """Determine if a view should be condensed.

        Args:
            view: The view to check

        Returns:
            True if the view should be condensed, False otherwise
        """
        pass
