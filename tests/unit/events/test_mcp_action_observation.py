import json

from openhands.core.schema import ActionType, ObservationType
from openhands.events.action.mcp import MCPAction
from openhands.events.observation.mcp import MCPObservation


def test_mcp_action_creation():
    """Test creating an MCPAction."""
    action = MCPAction(name='test_tool', arguments={'arg1': 'value1', 'arg2': 42})

    assert action.name == 'test_tool'
    assert action.arguments == {'arg1': 'value1', 'arg2': 42}
    assert action.action == ActionType.MCP
    assert action.thought == ''
    assert action.runnable is True
    assert action.security_risk is None


def test_mcp_action_with_thought():
    """Test creating an MCPAction with a thought."""
    action = MCPAction(
        name='test_tool',
        arguments={'arg1': 'value1', 'arg2': 42},
        thought='This is a test thought',
    )

    assert action.name == 'test_tool'
    assert action.arguments == {'arg1': 'value1', 'arg2': 42}
    assert action.thought == 'This is a test thought'


def test_mcp_action_message():
    """Test the message property of MCPAction."""
    action = MCPAction(name='test_tool', arguments={'arg1': 'value1', 'arg2': 42})

    message = action.message
    assert 'test_tool' in message
    assert 'arg1' in message
    assert 'value1' in message
    assert '42' in message


def test_mcp_action_str_representation():
    """Test the string representation of MCPAction."""
    action = MCPAction(
        name='test_tool',
        arguments={'arg1': 'value1', 'arg2': 42},
        thought='This is a test thought',
    )

    str_repr = str(action)
    assert 'MCPAction' in str_repr
    assert 'THOUGHT: This is a test thought' in str_repr
    assert 'NAME: test_tool' in str_repr
    assert 'ARGUMENTS:' in str_repr
    assert 'arg1' in str_repr
    assert 'value1' in str_repr
    assert '42' in str_repr


def test_mcp_observation_creation():
    """Test creating an MCPObservation."""
    observation = MCPObservation(
        content=json.dumps({'result': 'success', 'data': 'test data'})
    )

    assert observation.content == json.dumps({'result': 'success', 'data': 'test data'})
    assert observation.observation == ObservationType.MCP


def test_mcp_observation_message():
    """Test the message property of MCPObservation."""
    observation = MCPObservation(
        content=json.dumps({'result': 'success', 'data': 'test data'})
    )

    message = observation.message
    assert message == json.dumps({'result': 'success', 'data': 'test data'})
    assert 'result' in message
    assert 'success' in message
    assert 'data' in message
    assert 'test data' in message


def test_mcp_action_with_complex_arguments():
    """Test MCPAction with complex nested arguments."""
    complex_args = {
        'simple_arg': 'value',
        'number_arg': 42,
        'boolean_arg': True,
        'nested_arg': {'inner_key': 'inner_value', 'inner_list': [1, 2, 3]},
        'list_arg': ['a', 'b', 'c'],
    }

    action = MCPAction(name='complex_tool', arguments=complex_args)

    assert action.name == 'complex_tool'
    assert action.arguments == complex_args
    assert action.arguments['nested_arg']['inner_key'] == 'inner_value'
    assert action.arguments['list_arg'] == ['a', 'b', 'c']

    # Check that the message contains the complex arguments
    message = action.message
    assert 'complex_tool' in message
    assert 'nested_arg' in message
    assert 'inner_key' in message
    assert 'inner_value' in message


def test_mcp_observation_with_arguments():
    """Test MCPObservation with arguments."""
    complex_args = {
        'simple_arg': 'value',
        'number_arg': 42,
        'boolean_arg': True,
        'nested_arg': {'inner_key': 'inner_value', 'inner_list': [1, 2, 3]},
        'list_arg': ['a', 'b', 'c'],
    }

    observation = MCPObservation(
        content=json.dumps({'result': 'success', 'data': 'test data'}),
        name='test_tool',
        arguments=complex_args,
    )

    assert observation.content == json.dumps({'result': 'success', 'data': 'test data'})
    assert observation.observation == ObservationType.MCP
    assert observation.name == 'test_tool'
    assert observation.arguments == complex_args
    assert observation.arguments['nested_arg']['inner_key'] == 'inner_value'
    assert observation.arguments['list_arg'] == ['a', 'b', 'c']

    # Test serialization
    from openhands.events.serialization import event_to_dict

    serialized = event_to_dict(observation)

    assert serialized['observation'] == ObservationType.MCP
    assert serialized['content'] == json.dumps(
        {'result': 'success', 'data': 'test data'}
    )
    assert serialized['extras']['name'] == 'test_tool'
    assert serialized['extras']['arguments'] == complex_args
    assert serialized['extras']['arguments']['nested_arg']['inner_key'] == 'inner_value'
