from openhands.events.action import CmdRunAction
from openhands.events.event import EventSource
from openhands.events.observation import CmdOutputObservation


def test_setup_script_events_source_property():
    """Test that setup script events use the source property correctly."""
    # Create a mock action with the ENVIRONMENT source
    action = CmdRunAction(
        command='chmod +x .openhands/setup.sh && source .openhands/setup.sh',
        thought='Running setup script to configure the workspace environment.',
    )
    action._source = EventSource.ENVIRONMENT

    # Verify the source property works correctly
    assert action.source == EventSource.ENVIRONMENT

    # Create a mock observation with the ENVIRONMENT source
    observation = CmdOutputObservation(
        command='chmod +x .openhands/setup.sh && source .openhands/setup.sh',
        content='Setup completed successfully',
        exit_code=0,
    )
    observation._source = EventSource.ENVIRONMENT
    observation._cause = 1  # Mock ID of the action

    # Verify the source property works correctly
    assert observation.source == EventSource.ENVIRONMENT
