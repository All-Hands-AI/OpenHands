"""Tests for the conversation visualizer and event visualization."""

import json

from openhands_cli.tui.visualizer import (
    CLIVisualizer,
)
from rich.text import Text

from openhands.sdk.event import (
    ActionEvent,
    SystemPromptEvent,
    UserRejectObservation,
)
from openhands.sdk.llm import (
    MessageToolCall,
    TextContent,
)
from openhands.sdk.tool import Action


class VisualizerMockAction(Action):
    """Mock action for testing."""

    command: str = 'test command'
    working_dir: str = '/tmp'


class VisualizerCustomAction(Action):
    """Custom action with overridden visualize method."""

    task_list: list[dict] = []

    @property
    def visualize(self) -> Text:
        """Custom visualization for task tracker."""
        content = Text()
        content.append('Task Tracker Action\n', style='bold')
        content.append(f'Tasks: {len(self.task_list)}')
        for i, task in enumerate(self.task_list):
            content.append(f'\n  {i + 1}. {task.get("title", "Untitled")}')
        return content


def create_tool_call(
    call_id: str, function_name: str, arguments: dict
) -> MessageToolCall:
    """Helper to create a MessageToolCall."""
    return MessageToolCall(
        id=call_id,
        name=function_name,
        arguments=json.dumps(arguments),
        origin='completion',
    )


def test_conversation_visualizer_initialization():
    """Test DefaultConversationVisualizer can be initialized."""
    visualizer = CLIVisualizer()
    assert visualizer is not None
    assert hasattr(visualizer, 'on_event')
    assert hasattr(visualizer, '_create_event_panel')


def test_visualizer_event_panel_creation():
    """Test that visualizer creates panels for different event types."""
    conv_viz = CLIVisualizer()

    # Test with a simple action event
    action = VisualizerMockAction(command='test')
    tool_call = create_tool_call('call_1', 'test', {})
    action_event = ActionEvent(
        thought=[TextContent(text='Testing')],
        action=action,
        tool_name='test',
        tool_call_id='call_1',
        tool_call=tool_call,
        llm_response_id='response_1',
    )
    panel = conv_viz._create_event_panel(action_event)
    assert panel is not None
    assert hasattr(panel, 'renderable')


def test_visualizer_action_event_with_none_action_panel():
    """ActionEvent with action=None should render as 'Agent Action (Not Executed)'."""
    visualizer = CLIVisualizer()
    tc = create_tool_call('call_ne_1', 'missing_fn', {})
    action_event = ActionEvent(
        thought=[TextContent(text='...')],
        tool_call=tc,
        tool_name=tc.name,
        tool_call_id=tc.id,
        llm_response_id='resp_viz_1',
        action=None,
    )
    panel = visualizer._create_event_panel(action_event)
    assert panel is not None
    # Ensure it doesn't fall back to UNKNOWN
    assert 'UNKNOWN Event' not in str(panel.title)
    # And uses the 'Agent Action (Not Executed)' title
    assert 'Agent Action (Not Executed)' in str(panel.title)


def test_visualizer_user_reject_observation_panel():
    """UserRejectObservation should render a dedicated panel."""
    visualizer = CLIVisualizer()
    event = UserRejectObservation(
        tool_name='demo_tool',
        tool_call_id='fc_call_1',
        action_id='action_1',
        rejection_reason='User rejected the proposed action.',
    )

    panel = visualizer._create_event_panel(event)
    assert panel is not None
    title = str(panel.title)
    assert 'UNKNOWN Event' not in title
    assert 'User Rejected Action' in title
    # ensure the reason is part of the renderable text
    renderable = panel.renderable
    assert isinstance(renderable, Text)
    assert 'User rejected the proposed action.' in renderable.plain


def test_metrics_formatting():
    """Test metrics subtitle formatting."""
    from unittest.mock import MagicMock

    from openhands.sdk.conversation.conversation_stats import ConversationStats
    from openhands.sdk.llm.utils.metrics import Metrics

    # Create conversation stats with metrics
    conversation_stats = ConversationStats()

    # Create metrics and add to conversation stats
    metrics = Metrics(model_name='test-model')
    metrics.add_cost(0.0234)
    metrics.add_token_usage(
        prompt_tokens=1500,
        completion_tokens=500,
        cache_read_tokens=300,
        cache_write_tokens=0,
        reasoning_tokens=200,
        context_window=8000,
        response_id='test_response',
    )

    # Add metrics to conversation stats
    conversation_stats.usage_to_metrics['test_usage'] = metrics

    # Create visualizer and initialize with mock state
    visualizer = CLIVisualizer()
    mock_state = MagicMock()
    mock_state.stats = conversation_stats
    visualizer.initialize(mock_state)

    # Test the metrics subtitle formatting
    subtitle = visualizer._format_metrics_subtitle()
    assert subtitle is not None
    assert '1.5K' in subtitle  # Input tokens abbreviated (trailing zeros removed)
    assert '500' in subtitle  # Output tokens
    assert '20.00%' in subtitle  # Cache hit rate
    assert '200' in subtitle  # Reasoning tokens
    assert '0.0234' in subtitle  # Cost


def test_metrics_abbreviation_formatting():
    """Test number abbreviation with various edge cases."""
    from unittest.mock import MagicMock

    from openhands.sdk.conversation.conversation_stats import ConversationStats
    from openhands.sdk.llm.utils.metrics import Metrics

    test_cases = [
        # (input_tokens, expected_abbr)
        (999, '999'),  # Below threshold
        (1000, '1K'),  # Exact K boundary, trailing zeros removed
        (1500, '1.5K'),  # K with one decimal, trailing zero removed
        (89080, '89.08K'),  # K with two decimals (regression test for bug)
        (89000, '89K'),  # K with trailing zeros removed
        (1000000, '1M'),  # Exact M boundary
        (1234567, '1.23M'),  # M with decimals
        (1000000000, '1B'),  # Exact B boundary
    ]

    for tokens, expected in test_cases:
        stats = ConversationStats()
        metrics = Metrics(model_name='test-model')
        metrics.add_token_usage(
            prompt_tokens=tokens,
            completion_tokens=100,
            cache_read_tokens=0,
            cache_write_tokens=0,
            reasoning_tokens=0,
            context_window=8000,
            response_id='test',
        )
        stats.usage_to_metrics['test'] = metrics

        visualizer = CLIVisualizer()
        mock_state = MagicMock()
        mock_state.stats = stats
        visualizer.initialize(mock_state)
        subtitle = visualizer._format_metrics_subtitle()

        assert subtitle is not None, f'Failed for {tokens}'
        assert expected in subtitle, (
            f"Expected '{expected}' in subtitle for {tokens}, got: {subtitle}"
        )


def test_event_base_fallback_visualize():
    """Test that Event provides fallback visualization."""
    from openhands.sdk.event.base import Event
    from openhands.sdk.event.types import SourceType

    class UnknownEvent(Event):
        source: SourceType = 'agent'

    event = UnknownEvent()

    conv_viz = CLIVisualizer()
    panel = conv_viz._create_event_panel(event)

    assert 'UNKNOWN Event' in str(panel.title)


def test_visualizer_does_not_render_system_prompt():
    """Test that Event provides fallback visualization."""
    system_prompt_event = SystemPromptEvent(
        source='agent', system_prompt=TextContent(text='dummy'), tools=[]
    )
    conv_viz = CLIVisualizer()
    panel = conv_viz._create_event_panel(system_prompt_event)
    assert panel is None
