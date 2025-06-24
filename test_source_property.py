from openhands.events.event import Event, EventSource


def test_source_property():
    # Create an event and set its source
    event = Event()
    event._source = EventSource.ENVIRONMENT

    # Test that the source property works correctly
    assert event.source == EventSource.ENVIRONMENT

    # Test that the source property returns the correct type
    assert isinstance(event.source, EventSource)

    # Print the source for debugging
    print(f'Source: {event.source}')
    print(f'Source type: {type(event.source)}')

    # Test that we can compare the source with an EventSource enum value
    assert event.source == EventSource.ENVIRONMENT


if __name__ == '__main__':
    test_source_property()
    print('All tests passed!')
