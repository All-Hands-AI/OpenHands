import os
import random
import string
import gc
from memory_profiler import profile
from openhands.events.action.files import FileReadAction, FileWriteAction, FileEditAction
from openhands.events.observation.files import FileReadObservation, FileWriteObservation, FileEditObservation
from openhands.events.event import FileEditSource, FileReadSource
from openhands.core.schema import ActionType
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.locations import get_conversation_dir, get_conversation_event_filename, get_conversation_events_dir
from openhands.events.stream import EventStream
from openhands.events.event import EventSource

def generate_random_content(size_kb=100):
    """Generate random content of specified size in KB"""
    chars = string.ascii_letters + string.digits + string.punctuation + ' \n'
    content = ''.join(random.choice(chars) for _ in range(size_kb * 1024))
    return content

@profile(precision=4)
def test_file_operations():
    # Create a test file
    test_file = "/tmp/test_file.txt"
    test_content = generate_random_content()
    with open(test_file, "w") as f:
        f.write(test_content)

    # Create conversation directory
    conversation_dir = get_conversation_dir("test_session")
    events_dir = get_conversation_events_dir("test_session")
    os.makedirs(events_dir, exist_ok=True)

    # Perform operations 20 times
    for i in range(20):
        print(f"\nIteration {i+1}/20")
        
        # Force garbage collection before each iteration
        gc.collect()

        # Create new FileStore and EventStream for each iteration
        file_store = InMemoryFileStore()
        event_stream = EventStream("test_session", file_store)
        
        # 1. Read file
        read_action = FileReadAction(
            path=test_file,
            start=0,
            end=-1,
            thought="Reading file",
            action=ActionType.READ,
            impl_source=FileReadSource.DEFAULT
        )
        event_stream.add_event(read_action, EventSource.AGENT)
        
        read_obs = FileReadObservation(
            path=test_file,
            impl_source=FileReadSource.DEFAULT,
            content=test_content
        )
        event_stream.add_event(read_obs, EventSource.ENVIRONMENT)

        # 2. Write file
        write_action = FileWriteAction(
            path=test_file,
            content=test_content,
            start=0,
            end=-1,
            thought="Writing file",
            action=ActionType.WRITE
        )
        event_stream.add_event(write_action, EventSource.AGENT)

        write_obs = FileWriteObservation(
            path=test_file,
            content=test_content
        )
        event_stream.add_event(write_obs, EventSource.ENVIRONMENT)

        # 3. Edit file
        edit_action = FileEditAction(
            path=test_file,
            content=test_content,
            start=1,
            end=-1,
            thought="Editing file",
            action=ActionType.EDIT,
            impl_source=FileEditSource.LLM_BASED_EDIT
        )
        event_stream.add_event(edit_action, EventSource.AGENT)

        edit_obs = FileEditObservation(
            path=test_file,
            prev_exist=True,
            old_content=test_content,
            new_content=test_content,
            impl_source=FileEditSource.LLM_BASED_EDIT,
            content=test_content
        )
        event_stream.add_event(edit_obs, EventSource.ENVIRONMENT)

        # Close event stream at the end of each iteration
        event_stream.close()

    # Clean up
    os.remove(test_file)

if __name__ == "__main__":
    test_file_operations()