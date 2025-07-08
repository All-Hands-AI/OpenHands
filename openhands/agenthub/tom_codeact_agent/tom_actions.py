"""Tom-specific actions for presenting improvements and suggestions to users."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from openhands.core.schema import ActionType
from openhands.events.action import MessageAction


@dataclass
class TomInstructionAction(MessageAction):
    """Action to present Tom's instruction improvements to the user.
    
    This action displays the original instruction alongside Tom's personalized
    improvements, allowing the user to choose which version to proceed with.
    """
    
    original_instruction: str = ''
    improved_instructions: List[Dict[str, Any]] = field(default_factory=list)
    action: str = ActionType.MESSAGE
    source: str = 'agent'
    
    def __post_init__(self):
        """Set the content after initialization."""
        if not self.content and self.improved_instructions:
            self.content = self._format_instruction_improvements()
    
    def _format_instruction_improvements(self) -> str:
        """Format instruction improvements for user display."""
        lines = [
            "🔍 **Tom analyzed your request and suggests improvements:**\n",
            f"**Original:** {self.original_instruction}\n"
        ]
        
        for i, rec in enumerate(self.improved_instructions, 1):
            lines.extend([
                f"**✨ Improved Option {i}:**",
                f"{rec.get('improved_instruction', '')}\n",
                f"💡 **Why:** {rec.get('reasoning', 'No reasoning provided')}",
                f"🎯 **Confidence:** {rec.get('confidence_score', 0)*100:.0f}%"
            ])
            
            # Add personalization factors if available
            factors = rec.get('personalization_factors', [])
            if factors:
                lines.append(f"👤 **Personalized for:** {', '.join(factors)}")
            
            lines.append("")  # Add spacing between options
        
        lines.append("Would you like to use the improved instruction or continue with the original?")
        return '\n'.join(lines)
    
    @property
    def message(self) -> str:
        """Return the formatted message for display."""
        return self.content or "Tom instruction improvements are available."


@dataclass
class TomSuggestionAction(MessageAction):
    """Action to present Tom's next action suggestions to the user.
    
    This action displays personalized next action suggestions from Tom,
    helping users decide what to do after completing a task.
    """
    
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    context: str = ''
    action: str = ActionType.MESSAGE
    source: str = 'agent'
    
    def __post_init__(self):
        """Set the content after initialization."""
        if not self.content and self.suggestions:
            self.content = self._format_next_action_suggestions()
    
    def _format_next_action_suggestions(self) -> str:
        """Format next action suggestions for user display."""
        lines = [
            "✅ **Task completed!** Tom suggests these next steps:\n"
        ]
        
        for i, suggestion in enumerate(self.suggestions, 1):
            priority = suggestion.get('priority', 'medium')
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "🟡")
            
            lines.extend([
                f"**{i}. {suggestion.get('action_description', 'No description')}** {emoji}",
                f"💭 {suggestion.get('reasoning', 'No reasoning provided')}",
                f"📈 Expected: {suggestion.get('expected_outcome', 'No outcome specified')}"
            ])
            
            # Add user preference alignment if available
            alignment = suggestion.get('user_preference_alignment')
            if alignment is not None:
                lines.append(f"👤 **Alignment:** {alignment*100:.0f}%")
            
            lines.append("")  # Add spacing between suggestions
        
        lines.append("What would you like to do next?")
        return '\n'.join(lines)
    
    @property
    def message(self) -> str:
        """Return the formatted message for display."""
        return self.content or "Tom has suggestions for your next actions."