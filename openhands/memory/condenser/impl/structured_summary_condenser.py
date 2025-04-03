from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from openhands.core.config.condenser_config import (
    StructuredSummaryCondenserConfig,
)
from openhands.core.message import Message, TextContent
from openhands.events.action.agent import CondensationAction
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.events.serialization.event import truncate_content
from openhands.llm import LLM
from openhands.memory.condenser.condenser import (
    Condensation,
    RollingCondenser,
    View,
)


class StateSummary(BaseModel):
    """A structured representation summarizing the state of the agent and the task."""

    # Required core fields
    user_context: str = Field(
        default='',
        description='Essential user requirements, goals, and clarifications in concise form.',
    )
    completed_tasks: str = Field(
        default='', description='List of tasks completed so far with brief results.'
    )
    pending_tasks: str = Field(
        default='', description='List of tasks that still need to be done.'
    )
    current_state: str = Field(
        default='',
        description='Current variables, data structures, or other relevant state information.',
    )

    # Code state fields
    files_modified: str = Field(
        default='', description='List of files that have been created or modified.'
    )
    function_changes: str = Field(
        default='', description='List of functions that have been created or modified.'
    )
    data_structures: str = Field(
        default='', description='List of key data structures in use or modified.'
    )

    # Test status fields
    tests_written: str = Field(
        default='',
        description='Whether tests have been written for the changes. True, false, or unknown.',
    )
    tests_passing: str = Field(
        default='',
        description='Whether all tests are currently passing. True, false, or unknown.',
    )
    failing_tests: str = Field(
        default='', description='List of names or descriptions of any failing tests.'
    )
    error_messages: str = Field(
        default='', description='List of key error messages encountered.'
    )

    # Version control fields
    branch_created: str = Field(
        default='',
        description='Whether a branch has been created for this work. True, false, or unknown.',
    )
    branch_name: str = Field(
        default='', description='Name of the current working branch if known.'
    )
    commits_made: str = Field(
        default='',
        description='Whether any commits have been made. True, false, or unknown.',
    )
    pr_created: str = Field(
        default='',
        description='Whether a pull request has been created. True, false, or unknown.',
    )
    pr_status: str = Field(
        default='',
        description="Status of any pull request: 'draft', 'open', 'merged', 'closed', or 'unknown'.",
    )

    # Other fields
    dependencies: str = Field(
        default='',
        description='List of dependencies or imports that have been added or modified.',
    )
    other_relevant_context: str = Field(
        default='',
        description="Any other important information that doesn't fit into the categories above.",
    )

    @classmethod
    def tool_description(cls) -> dict[str, Any]:
        """Description of a tool whose arguments are the fields of this class.

        Can be given to an LLM to force structured generation.
        """
        properties = {}

        # Build properties dictionary from field information
        for field_name, field in cls.model_fields.items():
            description = field.description or ''

            properties[field_name] = {'type': 'string', 'description': description}

        return {
            'type': 'function',
            'function': {
                'name': 'create_state_summary',
                'description': 'Creates a comprehensive summary of the current state of the interaction to preserve context when history grows too large. You must include non-empty values for user_context, completed_tasks, and pending_tasks.',
                'parameters': {
                    'type': 'object',
                    'properties': properties,
                    'required': ['user_context', 'completed_tasks', 'pending_tasks'],
                },
            },
        }

    def __str__(self) -> str:
        """Format the state summary in a clear way for Claude 3.7 Sonnet."""
        sections = [
            '# State Summary',
            '## Core Information',
            f'**User Context**: {self.user_context}',
            f'**Completed Tasks**: {self.completed_tasks}',
            f'**Pending Tasks**: {self.pending_tasks}',
            f'**Current State**: {self.current_state}',
            '## Code Changes',
            f'**Files Modified**: {self.files_modified}',
            f'**Function Changes**: {self.function_changes}',
            f'**Data Structures**: {self.data_structures}',
            f'**Dependencies**: {self.dependencies}',
            '## Testing Status',
            f'**Tests Written**: {self.tests_written}',
            f'**Tests Passing**: {self.tests_passing}',
            f'**Failing Tests**: {self.failing_tests}',
            f'**Error Messages**: {self.error_messages}',
            '## Version Control',
            f'**Branch Created**: {self.branch_created}',
            f'**Branch Name**: {self.branch_name}',
            f'**Commits Made**: {self.commits_made}',
            f'**PR Created**: {self.pr_created}',
            f'**PR Status**: {self.pr_status}',
            '## Additional Context',
            f'**Other Relevant Context**: {self.other_relevant_context}',
        ]

        # Join all sections with double newlines
        return '\n\n'.join(sections)


class StructuredSummaryCondenser(RollingCondenser):
    """A condenser that summarizes forgotten events.

    Maintains a condensed history and forgets old events when it grows too large. Uses structured generation via function-calling to produce summaries that replace forgotten events.
    """

    def __init__(self, llm: LLM, max_size: int = 100, keep_first: int = 1):
        if keep_first >= max_size // 2:
            raise ValueError(
                f'keep_first ({keep_first}) must be less than half of max_size ({max_size})'
            )
        if keep_first < 0:
            raise ValueError(f'keep_first ({keep_first}) cannot be negative')
        if max_size < 1:
            raise ValueError(f'max_size ({max_size}) cannot be non-positive')

        if not llm.is_function_calling_active():
            raise ValueError(
                'LLM must support function calling to use StructuredSummaryCondenser'
            )

        self.max_size = max_size
        self.keep_first = keep_first
        self.llm = llm

        super().__init__()

    def get_condensation(self, view: View) -> Condensation:
        head = view[: self.keep_first]
        target_size = self.max_size // 2
        # Number of events to keep from the tail -- target size, minus however many
        # prefix events from the head, minus one for the summarization event
        events_from_tail = target_size - len(head) - 1

        summary_event = (
            view[self.keep_first]
            if isinstance(view[self.keep_first], AgentCondensationObservation)
            else AgentCondensationObservation('No events summarized')
        )

        # Identify events to be forgotten (those not in head or tail)
        forgotten_events = []
        for event in view[self.keep_first : -events_from_tail]:
            if not isinstance(event, AgentCondensationObservation):
                forgotten_events.append(event)

        # Construct prompt for summarization
        prompt = """You are maintaining a context-aware state summary for an interactive software agent. This summary is critical because it:
1. Preserves essential context when conversation history grows too large
2. Prevents lost work when the session length exceeds token limits
3. Helps maintain continuity across multiple interactions

You will be given:
- A list of events (actions taken by the agent)
- The most recent previous summary (if one exists)

Capture all relevant information, especially:
- User requirements that were explicitly stated
- Work that has been completed
- Tasks that remain pending
- Current state of code, variables, and data structures
- The status of any version control operations"""

        prompt += '\n\n'

        summary_event_content = truncate_content(
            summary_event.message if summary_event.message else '', max_chars=10_000
        )
        prompt += f'<PREVIOUS SUMMARY>\n{summary_event_content}\n</PREVIOUS SUMMARY>\n'

        prompt += '\n\n'

        for forgotten_event in forgotten_events:
            event_content = truncate_content(str(forgotten_event), max_chars=10_000)
            prompt += f'<EVENT id={forgotten_event.id}>\n{event_content}\n</EVENT>\n'

        messages = [Message(role='user', content=[TextContent(text=prompt)])]

        response = self.llm.completion(
            messages=self.llm.format_messages_for_llm(messages),
            tools=[StateSummary.tool_description()],
            tool_choice={
                'type': 'function',
                'function': {'name': 'create_state_summary'},
            },
        )

        try:
            # Extract the message containing tool calls
            message = response.choices[0].message

            # Check if there are tool calls
            if not hasattr(message, 'tool_calls') or not message.tool_calls:
                raise ValueError('No tool calls found in response')

            # Find the create_state_summary tool call
            summary_tool_call = None
            for tool_call in message.tool_calls:
                if tool_call.function.name == 'create_state_summary':
                    summary_tool_call = tool_call
                    break

            if not summary_tool_call:
                raise ValueError('create_state_summary tool call not found')

            # Parse the arguments
            args_json = summary_tool_call.function.arguments
            args_dict = json.loads(args_json)

            # Create a StateSummary object
            summary = StateSummary.model_validate(args_dict)

        except (AttributeError, KeyError, json.JSONDecodeError) as e:
            raise ValueError(f'Failed to extract summary from response: {str(e)}')

        self.add_metadata('response', response.model_dump())
        self.add_metadata('metrics', self.llm.metrics.get())

        return Condensation(
            action=CondensationAction(
                forgotten_events_start_id=min(event.id for event in forgotten_events),
                forgotten_events_end_id=max(event.id for event in forgotten_events),
                summary=str(summary),
                summary_offset=self.keep_first,
            )
        )

    def should_condense(self, view: View) -> bool:
        return len(view) > self.max_size

    @classmethod
    def from_config(
        cls, config: StructuredSummaryCondenserConfig
    ) -> StructuredSummaryCondenser:
        return StructuredSummaryCondenser(
            llm=LLM(config=config.llm_config),
            max_size=config.max_size,
            keep_first=config.keep_first,
        )


StructuredSummaryCondenser.register_config(StructuredSummaryCondenserConfig)
