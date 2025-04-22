from dataclasses import dataclass

from pydantic import BaseModel

from openhands.core.schema import ActionType
from openhands.events import EventSource
from openhands.events.action import Action
from openhands.events.observation import Observation
from openhands.events.serialization.action import ACTION_TYPE_TO_CLASS
from openhands.events.serialization.event import event_from_dict, event_to_dict


class DeepNestedModel(BaseModel):
    deep_field: str
    deep_number: int
    nested_list: list[int] = []


class NestedModel(BaseModel):
    field1: str
    nested: DeepNestedModel
    numbers: list[int]


class NestedListModel(BaseModel):
    items: list[DeepNestedModel]


@dataclass
class TestAction(Action):
    nested: dict

    def __init__(self, nested: NestedModel | dict, id: str | None = None):
        if isinstance(nested, NestedModel):
            self.nested = nested.model_dump()
            if id is not None:
                self._id = int(id)
        else:
            self.nested = nested
        self._source = EventSource.AGENT
        self._action = 'test_action'


@dataclass
class TestListAction(Action):
    nested_list: dict

    def __init__(self, nested_list: NestedListModel | dict, id: str | None = None):
        if isinstance(nested_list, NestedListModel):
            self.nested_list = nested_list.model_dump()
            if id is not None:
                self._id = int(id)
        else:
            self.nested_list = nested_list
        self._source = EventSource.AGENT
        self._action = 'test_list_action'


@dataclass
class TestObservation(Observation):
    nested: dict

    def __init__(self, id: str, nested: NestedModel):
        self._id = int(id)
        self.nested = nested.model_dump()
        self._source = EventSource.AGENT
        self._observation = 'test_observation'


# Register test action types
ActionType.TEST = 'test_action'
ActionType.TEST_LIST = 'test_list_action'
ACTION_TYPE_TO_CLASS[ActionType.TEST] = TestAction
ACTION_TYPE_TO_CLASS[ActionType.TEST_LIST] = TestListAction


def test_nested_model_serialization():
    # Create a test event with nested models
    deep_nested = DeepNestedModel(
        deep_field='deep value', deep_number=42, nested_list=[1, 2, 3]
    )
    nested = NestedModel(field1='test', nested=deep_nested, numbers=[1, 2, 3])
    event = TestAction(nested=nested, id='123')

    # Test serialization
    event_dict = event_to_dict(event)
    assert event_dict['id'] == 123
    assert event_dict['action'] == 'test_action'
    assert event_dict['args']['nested']['field1'] == 'test'
    assert event_dict['args']['nested']['nested']['deep_field'] == 'deep value'
    assert event_dict['args']['nested']['nested']['deep_number'] == 42
    assert event_dict['args']['nested']['nested']['nested_list'] == [1, 2, 3]
    assert event_dict['args']['nested']['numbers'] == [1, 2, 3]

    # Test deserialization
    deserialized_event = event_from_dict(event_dict)
    assert deserialized_event._id == 123
    assert isinstance(deserialized_event.nested, dict)
    assert deserialized_event.nested['field1'] == 'test'
    assert isinstance(deserialized_event.nested['nested'], dict)
    assert deserialized_event.nested['nested']['deep_field'] == 'deep value'
    assert deserialized_event.nested['nested']['deep_number'] == 42
    assert deserialized_event.nested['nested']['nested_list'] == [1, 2, 3]
    assert deserialized_event.nested['numbers'] == [1, 2, 3]


def test_list_of_nested_models():
    # Create test data
    items = [
        DeepNestedModel(deep_field='item1', deep_number=1, nested_list=[1]),
        DeepNestedModel(deep_field='item2', deep_number=2, nested_list=[2]),
    ]
    nested_list = NestedListModel(items=items)
    event = TestListAction(nested_list=nested_list, id='456')

    # Test serialization
    event_dict = event_to_dict(event)
    assert event_dict['id'] == 456
    assert event_dict['action'] == 'test_list_action'
    assert len(event_dict['args']['nested_list']['items']) == 2
    assert event_dict['args']['nested_list']['items'][0]['deep_field'] == 'item1'
    assert event_dict['args']['nested_list']['items'][0]['deep_number'] == 1
    assert event_dict['args']['nested_list']['items'][0]['nested_list'] == [1]
    assert event_dict['args']['nested_list']['items'][1]['deep_field'] == 'item2'
    assert event_dict['args']['nested_list']['items'][1]['deep_number'] == 2
    assert event_dict['args']['nested_list']['items'][1]['nested_list'] == [2]

    # Test deserialization
    deserialized_event = event_from_dict(event_dict)
    assert deserialized_event._id == 456
    assert isinstance(deserialized_event.nested_list, dict)
    assert len(deserialized_event.nested_list['items']) == 2
    assert deserialized_event.nested_list['items'][0]['deep_field'] == 'item1'
    assert deserialized_event.nested_list['items'][0]['deep_number'] == 1
    assert deserialized_event.nested_list['items'][0]['nested_list'] == [1]
    assert deserialized_event.nested_list['items'][1]['deep_field'] == 'item2'
    assert deserialized_event.nested_list['items'][1]['deep_number'] == 2
    assert deserialized_event.nested_list['items'][1]['nested_list'] == [2]


def test_empty_nested_models():
    # Test with empty nested models
    deep_nested = DeepNestedModel(deep_field='', deep_number=0, nested_list=[])
    nested = NestedModel(field1='', nested=deep_nested, numbers=[])
    event = TestAction(nested=nested, id='789')

    # Test serialization
    event_dict = event_to_dict(event)
    assert event_dict['id'] == 789
    assert event_dict['args']['nested']['field1'] == ''
    assert event_dict['args']['nested']['nested']['deep_field'] == ''
    assert event_dict['args']['nested']['nested']['deep_number'] == 0
    assert event_dict['args']['nested']['nested']['nested_list'] == []
    assert event_dict['args']['nested']['numbers'] == []

    # Test deserialization
    deserialized_event = event_from_dict(event_dict)
    assert deserialized_event._id == 789
    assert deserialized_event.nested['field1'] == ''
    assert deserialized_event.nested['nested']['deep_field'] == ''
    assert deserialized_event.nested['nested']['deep_number'] == 0
    assert deserialized_event.nested['nested']['nested_list'] == []
    assert deserialized_event.nested['numbers'] == []
