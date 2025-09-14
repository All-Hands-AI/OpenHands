from dataclasses import dataclass
from typing import Any

from openhands_cli.user_actions.prompt_spec import PromptSpec, PromptType, ValidationRule
from openhands_cli.user_actions.types import UserConfirmation
from openhands_cli.user_actions.utils import cli_confirm, prompt_user, prompt_with_completer


@dataclass
class PromptResult:
    """Result of executing a prompt."""
    value: str | None
    confirmation: UserConfirmation
    selected_index: int | None = None  # For selection prompts


class PromptHandler:
    """Unified handler for all prompt types using specifications."""
    
    def execute_prompt(self, spec: PromptSpec) -> PromptResult:
        """Execute a prompt based on its specification."""
        try:
            if spec.prompt_type == PromptType.SELECTION:
                return self._handle_selection_prompt(spec)
            elif spec.prompt_type == PromptType.FREE_TEXT:
                return self._handle_free_text_prompt(spec)
            elif spec.prompt_type == PromptType.TEXT_WITH_AUTOCOMPLETE:
                return self._handle_autocomplete_prompt(spec)
            else:
                raise ValueError(f"Unsupported prompt type: {spec.prompt_type}")
        except KeyboardInterrupt:
            return PromptResult(
                value=None,
                confirmation=UserConfirmation.DEFER,
                selected_index=None
            )
    
    def _handle_selection_prompt(self, spec: PromptSpec) -> PromptResult:
        """Handle selection-type prompts."""
        if not spec.options:
            raise ValueError("Selection prompts require options")
        
        question = spec.get_formatted_question()
        selected_index = cli_confirm(
            question=question,
            choices=spec.options,
            escapable=spec.escapable
        )
        
        return PromptResult(
            value=spec.options[selected_index],
            confirmation=UserConfirmation.ACCEPT,
            selected_index=selected_index
        )
    
    def _handle_free_text_prompt(self, spec: PromptSpec) -> PromptResult:
        """Handle free text input prompts."""
        question = spec.get_formatted_question()
        
        while True:
            response, deferred = prompt_user(question, escapable=spec.escapable)
            
            if deferred:
                return PromptResult(
                    value=None,
                    confirmation=UserConfirmation.DEFER,
                    selected_index=None
                )
            
            # Handle empty response with default value
            if not response.strip() and spec.default_value is not None:
                response = spec.default_value
            
            # Validate input
            if spec.validation_rules:
                validation_error = self._validate_input(response, spec.validation_rules)
                if validation_error:
                    print(f"Error: {validation_error}")
                    continue
            
            return PromptResult(
                value=response,
                confirmation=UserConfirmation.ACCEPT,
                selected_index=None
            )
    
    def _handle_autocomplete_prompt(self, spec: PromptSpec) -> PromptResult:
        """Handle text input with autocomplete prompts."""
        if not spec.options:
            raise ValueError("Autocomplete prompts require options")
        
        question = spec.get_formatted_question()
        
        while True:
            response, deferred = prompt_with_completer(
                question=question,
                choices=spec.options,
                escapable=spec.escapable
            )
            
            if deferred:
                return PromptResult(
                    value=None,
                    confirmation=UserConfirmation.DEFER,
                    selected_index=None
                )
            
            # Handle empty response with default value
            if not response.strip() and spec.default_value is not None:
                response = spec.default_value
            
            # Validate input
            if spec.validation_rules:
                validation_error = self._validate_input(response, spec.validation_rules)
                if validation_error:
                    print(f"Error: {validation_error}")
                    continue
            
            return PromptResult(
                value=response,
                confirmation=UserConfirmation.ACCEPT,
                selected_index=None
            )
    
    def _validate_input(self, value: str, rules: list[ValidationRule]) -> str | None:
        """Validate input against validation rules.
        
        Returns:
            Error message if validation fails, None if validation passes.
        """
        for rule in rules:
            if not rule.validator(value):
                return rule.error_message
        return None