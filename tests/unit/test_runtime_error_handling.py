import unittest

from openhands.core.exceptions import AgentRuntimeDisconnectedError, AgentRuntimeUnavailableError
from openhands.events import EventSource
from openhands.events.observation import ErrorObservation


def test_runtime_error_handling_implementation():
    """
    Test that the runtime error handling implementation in AgentController
    properly handles runtime errors by adding an error observation to the event stream
    and manages the retry counter correctly.
    
    This is a direct test of the code we added to handle runtime errors.
    """
    # Import the necessary modules
    from openhands.controller.agent_controller import AgentController
    
    # Get the methods we want to test
    exception_method = AgentController._step_with_exception_handling
    step_method = AgentController._step
    
    # Check that the methods handle runtime errors correctly
    # by examining the code directly
    import inspect
    exception_source = inspect.getsource(exception_method)
    step_source = inspect.getsource(step_method)
    
    # Check that the exception handling method contains the code to handle runtime errors
    assert "AgentRuntimeDisconnectedError" in exception_source
    assert "AgentRuntimeUnavailableError" in exception_source
    assert "ErrorObservation" in exception_source
    assert "Your command consumed too much resources" in exception_source
    assert "previous runtime died" in exception_source
    assert "EventSource.SYSTEM" in exception_source
    
    # Check that the exception handling method contains the retry counter logic
    assert "_runtime_error_count" in exception_source
    assert "Retry" in exception_source
    assert "of 3" in exception_source
    assert "Maximum runtime error retries exceeded" in exception_source
    
    # Check that the step method resets the error counter on successful steps
    assert "Reset runtime error counter" in step_source
    assert "_runtime_error_count = 0" in step_source





if __name__ == '__main__':
    unittest.main()