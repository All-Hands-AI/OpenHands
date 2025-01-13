from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch

from openhands.core.config import AppConfig
from openhands.events import EventStream
from openhands.events.observation import FileReadObservation
from openhands.runtime.base import Runtime
from openhands.storage.local import LocalFileStore


class MockRuntime(Runtime):
    async def connect(self) -> None:
        pass

    def run(self, action):
        return FileReadObservation('test')

    def run_ipython(self, action):
        return FileReadObservation('test')

    def read(self, action):
        return FileReadObservation('test')

    def write(self, action):
        return FileReadObservation('test')

    def browse(self, action):
        return FileReadObservation('test')

    def browse_interactive(self, action):
        return FileReadObservation('test')

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        pass

    def list_files(self, path: str | None = None) -> list[str]:
        return []

    def copy_from(self, path: str):
        return Path('test')


class TestRuntime:
    @pytest.fixture
    def mock_runtime(self, tmp_path):
        config = AppConfig()
        file_store = LocalFileStore(str(tmp_path))
        event_stream = EventStream('test_sid', file_store)
        runtime = MockRuntime(config, event_stream)
        return runtime

    def test_get_microagents_with_trailing_slash(self, mock_runtime):
        # Mock list_files to return directories with trailing slashes
        mock_runtime.list_files = MagicMock(side_effect=[
            ['repo.md', 'knowledge/', 'tasks/'],  # First call for root dir
            ['test1.md'],  # Second call for knowledge dir
            ['test2.md'],  # Third call for tasks dir
        ])

        # Mock file read to return some content
        def mock_read(action):
            if '.openhands_instructions' in action.path:
                from openhands.events.observation import ErrorObservation
                return ErrorObservation('File not found')
            return FileReadObservation(path='test.md', content="""---
name: test
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers: []
---
test content""")

        mock_runtime.read = MagicMock(side_effect=mock_read)

        # Get microagents
        microagents = mock_runtime.get_microagents_from_selected_repo(None)

        # Verify that microagents were loaded from both knowledge and tasks directories
        assert len(microagents) == 3  # 1 from repo.md, 1 from knowledge, 1 from tasks

    def test_get_microagents_without_trailing_slash(self, mock_runtime):
        # Mock list_files to return directories without trailing slashes
        mock_runtime.list_files = MagicMock(side_effect=[
            ['repo.md', 'knowledge', 'tasks'],  # First call for root dir
            ['test1.md'],  # Second call for knowledge dir
            ['test2.md'],  # Third call for tasks dir
        ])

        # Mock file read to return some content
        def mock_read(action):
            if '.openhands_instructions' in action.path:
                from openhands.events.observation import ErrorObservation
                return ErrorObservation('File not found')
            return FileReadObservation(path='test.md', content="""---
name: test
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers: []
---
test content""")

        mock_runtime.read = MagicMock(side_effect=mock_read)

        # Get microagents
        microagents = mock_runtime.get_microagents_from_selected_repo(None)

        # Verify that microagents were loaded from both knowledge and tasks directories
        assert len(microagents) == 3  # 1 from repo.md, 1 from knowledge, 1 from tasks
