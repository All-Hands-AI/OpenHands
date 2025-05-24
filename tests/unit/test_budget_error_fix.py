import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from litellm import BadRequestError
from openhands.controller.agent_controller import AgentController
from openhands.events.observation.error import ErrorObservation
from openhands.events import EventStream, EventSource
from openhands.core.schema import AgentState
from openhands.storage.memory import InMemoryFileStore


@pytest.mark.asyncio
async def test_budget_error_fix_fails_without_fix():
    """
    Test that demonstrates the issue with ExceededBudgetError not being properly displayed in the frontend.
    
    This test should FAIL with the current implementation and PASS after the fix is applied.
    
    The issue is that when a BadRequestError with 'ExceededBudget' occurs:
    1. The agent_controller correctly identifies it and sets error_id to 'STATUS$ERROR_LLM_OUT_OF_CREDITS'
    2. It calls status_callback with this error_id
    3. But it doesn't create an ErrorObservation with this error_id
    4. So the frontend doesn't receive the specific error_id and shows a generic error message
    
    The fix is to create an ErrorObservation with the specific error_id and add it to the event stream.
    """
    # Create a BadRequestError with ExceededBudget message
    budget_error = BadRequestError(
        message="Litellm_proxyException - ExceededBudget: User=20d03f52-abb6-4414-b024-67cc89d53e12 over budget. Spend=750.0430599000048, Budget=750.0.",
        model="gpt-4o",
        llm_provider="openai",
    )
    
    # Create a properly mocked controller that can work with the real _react_to_exception method
    controller = MagicMock()
    controller.state = MagicMock()
    controller.state.last_error = ""
    controller.status_callback = MagicMock()
    controller.set_agent_state_to = AsyncMock()  # Mock the async method
    
    # Create a spy for event_stream.add_event
    event_stream = MagicMock()
    added_events = []
    
    def spy_add_event(event, source):
        added_events.append((event, source))
        return None
    
    event_stream.add_event = spy_add_event
    controller.event_stream = event_stream
    
    # Get the actual _react_to_exception method from AgentController
    real_react_to_exception = AgentController._react_to_exception
    
    # Call the real _react_to_exception method with our mocked controller
    await real_react_to_exception(controller, budget_error)
    
    # Check that status_callback was called with the correct error_id
    controller.status_callback.assert_called_once_with(
        'error', 
        'STATUS$ERROR_LLM_OUT_OF_CREDITS', 
        'STATUS$ERROR_LLM_OUT_OF_CREDITS'
    )
    
    # Check if any ErrorObservation was added to the event stream
    error_observations = [
        event for event, source in added_events 
        if isinstance(event, ErrorObservation)
    ]
    
    # This assertion should FAIL with the current implementation and PASS after the fix
    # The test is expected to fail here because the current implementation doesn't create an ErrorObservation
    assert len(error_observations) > 0, "No ErrorObservation was added to the event stream"
    
    # The following assertions will only run if the above assertion passes (which it shouldn't with the current implementation)
    if error_observations:
        error_observation = error_observations[0]
        assert error_observation.error_id == 'STATUS$ERROR_LLM_OUT_OF_CREDITS', \
            f"Expected error_id 'STATUS$ERROR_LLM_OUT_OF_CREDITS', got '{error_observation.error_id}'"