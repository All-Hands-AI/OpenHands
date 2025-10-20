import pytest
from unittest.mock import Mock, patch, AsyncMock

from openhands.controller.state.state import State
from openhands.controller.stuck import StuckDetector
from openhands.controller.loop_recovery import LoopRecoveryManager
from openhands.controller.agent_controller import AgentController
from openhands.events.action import CmdRunAction, MessageAction
from openhands.events.observation import CmdOutputObservation, NullObservation
from openhands.events.stream import EventSource


class TestLoopRecoveryManager:
    @pytest.fixture
    def state(self):
        state = State(inputs={})
        state.iteration_flag.max_value = 50
        state.history = []
        return state

    @pytest.fixture
    def stuck_detector(self, state):
        return StuckDetector(state)

    @pytest.fixture
    def recovery_manager(self, state):
        controller = Mock()
        controller.state = state
        controller.memory = AsyncMock()
        controller.memory.get_events = AsyncMock(return_value=[])
        controller.memory.clear = AsyncMock()
        controller.memory.add_event = AsyncMock()
        controller.delegate = AsyncMock()
        controller.delegate.truncate_history = AsyncMock()
        controller.status_callback = None
        controller.set_agent_state_to = AsyncMock()
        return LoopRecoveryManager(controller)

    def test_analyze_loop_pattern_repeating_action_observation(self, stuck_detector, state):
        """Test that analyze_loop_pattern correctly identifies repeating action-observation patterns."""
        # Create a repeating pattern of ls command
        for i in range(4):
            cmd_action = CmdRunAction(command='ls')
            cmd_action._id = i
            state.history.append(cmd_action)
            cmd_observation = CmdOutputObservation(
                content='', command='ls', command_id=i
            )
            cmd_observation._cause = cmd_action._id
            state.history.append(cmd_observation)

        # Get filtered history (exclude user messages)
        filtered_history = [event for event in state.history if not (
            isinstance(event, MessageAction) and event._source == EventSource.USER
        )]
        
        result = stuck_detector.analyze_loop_pattern(filtered_history)
        assert result['loop_detected'] is True
        assert result['loop_type'] == 'repeating_pattern_2'
        assert result['loop_length'] == 2
        # Loop starts at index 4 because we have 4 action-observation pairs
        assert result['loop_start_index'] == 4

    def test_analyze_loop_pattern_no_loop(self, stuck_detector, state):
        """Test that analyze_loop_pattern returns no loop when there's no pattern."""
        # Add diverse events that don't form a loop
        cmd_action_1 = CmdRunAction(command='ls')
        state.history.append(cmd_action_1)
        cmd_observation_1 = CmdOutputObservation(
            content='file1.txt', command='ls'
        )
        state.history.append(cmd_observation_1)

        cmd_action_2 = CmdRunAction(command='pwd')
        state.history.append(cmd_action_2)
        cmd_observation_2 = CmdOutputObservation(
            content='/home/user', command='pwd'
        )
        state.history.append(cmd_observation_2)

        # Get filtered history (exclude user messages)
        filtered_history = [event for event in state.history if not (
            isinstance(event, MessageAction) and event._source == EventSource.USER
        )]
        
        result = stuck_detector.analyze_loop_pattern(filtered_history)
        assert result['loop_detected'] is False

    def test_analyze_loop_pattern_with_user_messages(self, stuck_detector, state):
        """Test that analyze_loop_pattern correctly handles user messages."""
        # Add user message and then repeating pattern
        user_action = MessageAction(content='Hello', wait_for_response=False)
        user_action._source = EventSource.USER
        state.history.append(user_action)
        user_observation = NullObservation(content='')
        state.history.append(user_observation)

        # Add repeating pattern after user message
        for i in range(4):
            cmd_action = CmdRunAction(command='ls')
            cmd_action._id = i
            state.history.append(cmd_action)
            cmd_observation = CmdOutputObservation(
                content='', command='ls', command_id=i
            )
            cmd_observation._cause = cmd_action._id
            state.history.append(cmd_observation)

        # Get filtered history (exclude user messages)
        filtered_history = [event for event in state.history if not (
            isinstance(event, MessageAction) and event._source == EventSource.USER
        )]
        
        result = stuck_detector.analyze_loop_pattern(filtered_history)
        assert result['loop_detected'] is True
        # Loop should start after user message (index 5)
        assert result['loop_start_index'] == 5

    def test_analyze_loop_pattern_monologue(self, stuck_detector, state):
        """Test that analyze_loop_pattern correctly identifies monologue loops."""
        # Add repeated agent messages
        for i in range(4):
            message_action = MessageAction(content="I'm stuck")
            message_action._source = EventSource.AGENT
            state.history.append(message_action)

        # Get filtered history (exclude user messages)
        filtered_history = [event for event in state.history if not (
            isinstance(event, MessageAction) and event._source == EventSource.USER
        )]
        
        result = stuck_detector.analyze_loop_pattern(filtered_history)
        assert result['loop_detected'] is True
        assert result['loop_type'] == 'monologue'

    @pytest.mark.asyncio
    async def test_recovery_manager_cli_mode(self, recovery_manager, state):
        """Test LoopRecoveryManager in CLI mode."""
        # Add some history to simulate a loop
        for i in range(4):
            cmd_action = CmdRunAction(command='ls')
            cmd_action._id = i
            state.history.append(cmd_action)
            cmd_observation = CmdOutputObservation(
                content='', command='ls', command_id=i
            )
            state.history.append(cmd_observation)

        # Get filtered history (exclude user messages)
        filtered_history = [event for event in state.history if not (
            isinstance(event, MessageAction) and event._source == EventSource.USER
        )]

        # Mock the stuck detector to return loop info
        with patch.object(recovery_manager.stuck_detector, 'analyze_loop_pattern') as mock_analyze:
            mock_analyze.return_value = {
                'loop_detected': True,
                'loop_start_index': 2,
                'loop_type': 'repeating_pattern_2',
                'loop_length': 2,
                'suggested_recovery_point': 2
            }
            
            # Mock input to simulate user choosing recovery
            with patch('builtins.input', return_value='1'):
                # Mock the controller to be in CLI mode
                recovery_manager.controller.status_callback = Mock()
                
                result = await recovery_manager.handle_loop_detection(filtered_history)
                assert result is True

    @pytest.mark.asyncio
    async def test_recovery_manager_automatic_mode(self, recovery_manager, state):
        """Test LoopRecoveryManager in automatic mode."""
        # Add some history to simulate a loop
        for i in range(4):
            cmd_action = CmdRunAction(command='ls')
            cmd_action._id = i
            state.history.append(cmd_action)
            cmd_observation = CmdOutputObservation(
                content='', command='ls', command_id=i
            )
            state.history.append(cmd_observation)

        # Get filtered history (exclude user messages)
        filtered_history = [event for event in state.history if not (
            isinstance(event, MessageAction) and event._source == EventSource.USER
        )]

        # Mock the stuck detector to return loop info
        with patch.object(recovery_manager.stuck_detector, 'analyze_loop_pattern') as mock_analyze:
            mock_analyze.return_value = {
                'loop_detected': True,
                'loop_start_index': 2,
                'loop_type': 'repeating_pattern_2',
                'loop_length': 2,
                'suggested_recovery_point': 2
            }
            
            # For automatic mode, ensure controller is not in CLI mode
            recovery_manager.controller.status_callback = None
            
            result = await recovery_manager.handle_loop_detection(filtered_history)
            assert result is True

    @pytest.mark.asyncio
    async def test_recovery_manager_no_loop_info(self, recovery_manager):
        """Test LoopRecoveryManager when no loop is detected."""
        # Mock the stuck detector to return no loop
        with patch.object(recovery_manager.stuck_detector, 'analyze_loop_pattern') as mock_analyze:
            mock_analyze.return_value = {
                'loop_detected': False
            }
            
            result = await recovery_manager.handle_loop_detection([])
            assert result is False

    @pytest.mark.asyncio
    async def test_recovery_manager_user_abort(self, recovery_manager, state):
        """Test LoopRecoveryManager when user chooses to abort."""
        # Get filtered history (exclude user messages)
        filtered_history = [event for event in state.history if not (
            isinstance(event, MessageAction) and event._source == EventSource.USER
        )]

        # Mock the stuck detector to return loop info
        with patch.object(recovery_manager.stuck_detector, 'analyze_loop_pattern') as mock_analyze:
            mock_analyze.return_value = {
                'loop_detected': True,
                'loop_start_index': 2,
                'loop_type': 'repeating_pattern_2',
                'loop_length': 2,
                'suggested_recovery_point': 2
            }
            
            # Mock input to simulate user choosing abort
            with patch('builtins.input', return_value='3'):
                # Set controller to CLI mode
                recovery_manager.controller.status_callback = Mock()
                
                result = await recovery_manager.handle_loop_detection(filtered_history)
                assert result is False


class TestAgentControllerLoopRecovery:
    @pytest.fixture
    def controller(self):
        controller = Mock(spec=AgentController)
        controller._is_stuck = AgentController._is_stuck.__get__(
            controller, AgentController
        )
        controller._handle_loop_detection = AgentController._handle_loop_detection.__get__(
            controller, AgentController
        )
        controller.delegate = None
        controller.headless_mode = True
        controller.state = Mock()
        controller.state.history = []
        controller._stuck_detector = Mock()
        controller._loop_recovery_manager = AsyncMock()
        return controller

    @pytest.mark.asyncio
    async def test_handle_loop_detection_no_stuck(self, controller):
        """Test _handle_loop_detection when agent is not stuck."""
        controller._stuck_detector.is_stuck.return_value = False
        
        result = await controller._handle_loop_detection()
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_loop_detection_recovery_success(self, controller):
        """Test _handle_loop_detection when recovery is successful."""
        controller._stuck_detector.is_stuck.return_value = True
        controller._stuck_detector.analyze_loop_pattern.return_value = {
            'loop_detected': True,
            'loop_start_index': 2,
            'loop_type': 'repeating_pattern_2',
            'loop_length': 2,
            'suggested_recovery_point': 2
        }
        controller._loop_recovery_manager.handle_loop_detection.return_value = True
        
        result = await controller._handle_loop_detection()
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_loop_detection_recovery_failed(self, controller):
        """Test _handle_loop_detection when recovery fails."""
        controller._stuck_detector.is_stuck.return_value = True
        controller._stuck_detector.analyze_loop_pattern.return_value = {
            'loop_detected': True,
            'loop_start_index': 2,
            'loop_type': 'repeating_pattern_2',
            'loop_length': 2,
            'suggested_recovery_point': 2
        }
        controller._loop_recovery_manager.handle_loop_detection.return_value = False
        
        result = await controller._handle_loop_detection()
        assert result is False