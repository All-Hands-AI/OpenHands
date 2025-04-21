from __future__ import annotations

from openhands.core.config.condenser_config import LLMAgentCacheCondenserConfig
from openhands.events.action.agent import CondensationAction
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.memory.condenser.condenser import (
    Condensation,
    RollingCondenser,
    View,
)


class LLMAgentCacheCondenser(RollingCondenser):
    """A condenser that allows the agent to trigger condensation.
    
    This condenser monitors the agent's messages for a trigger word. When the trigger
    word is found, it condenses the history by keeping the first message and the most
    recent messages up to the max_size.
    """

    def __init__(
        self,
        trigger_word: str = "CONDENSE!",
        max_size: int = 100,
    ):
        """Initialize the LLMAgentCacheCondenser.
        
        Args:
            trigger_word: The word that triggers condensation when found in agent messages.
            max_size: The maximum number of events to keep in the history.
        """
        self.trigger_word = trigger_word
        self.max_size = max_size
        super().__init__()

    def should_condense(self, view: View) -> bool:
        """Determine if the view should be condensed.
        
        The view should be condensed if:
        1. The number of events exceeds max_size, OR
        2. The agent's most recent message contains the trigger word.
        
        Args:
            view: The view to check.
            
        Returns:
            bool: True if the view should be condensed, False otherwise.
        """
        # Check if the history is too long
        if len(view) > self.max_size:
            return True
            
        # Check if the agent's most recent message contains the trigger word
        for event in reversed(view):
            if hasattr(event, 'message') and isinstance(event.message, str):
                if self.trigger_word in event.message:
                    return True
            # Stop checking once we find any agent message
            if hasattr(event, 'role') and event.role == 'assistant':
                break
                
        return False

    def get_condensation(self, view: View) -> Condensation:
        """Get the condensation from a view.
        
        This keeps the first message (usually the user's task) and the most recent
        messages up to max_size/2.
        
        Args:
            view: The view to condense.
            
        Returns:
            Condensation: The condensation action.
        """
        # Keep the first message (usually the user's task)
        head = view[:1]
        
        # Calculate how many events to keep from the tail
        target_size = self.max_size // 2
        events_from_tail = target_size - len(head) - 1  # -1 for the summary event
        
        # Check if there's already a summary event
        summary_event = (
            view[1]
            if len(view) > 1 and isinstance(view[1], AgentCondensationObservation)
            else AgentCondensationObservation('No events summarized')
        )
        
        # Identify events to be forgotten (those not in head or tail)
        forgotten_events = []
        for event in view[1:-events_from_tail]:
            if not isinstance(event, AgentCondensationObservation):
                forgotten_events.append(event)
        
        # If there are no events to forget, return the view
        if not forgotten_events:
            return view
            
        # Create a summary that indicates the number of events condensed
        summary = f"Condensed {len(forgotten_events)} events to save context window space."
        
        self.add_metadata('num_events_condensed', len(forgotten_events))
        
        return Condensation(
            action=CondensationAction(
                forgotten_events_start_id=min(event.id for event in forgotten_events),
                forgotten_events_end_id=max(event.id for event in forgotten_events),
                summary=summary,
                summary_offset=1,  # Place summary after the first event
            )
        )

    @classmethod
    def from_config(
        cls, config: LLMAgentCacheCondenserConfig
    ) -> LLMAgentCacheCondenser:
        """Create a LLMAgentCacheCondenser from a configuration.
        
        Args:
            config: The configuration for the condenser.
            
        Returns:
            LLMAgentCacheCondenser: The configured condenser.
        """
        return LLMAgentCacheCondenser(
            trigger_word=config.trigger_word,
            max_size=config.max_size,
        )


LLMAgentCacheCondenser.register_config(LLMAgentCacheCondenserConfig)