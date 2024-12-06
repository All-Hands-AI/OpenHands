import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from openhands.core.config import AppConfig
from openhands.events.action import MessageAction
from openhands.events.observation import MessageObservation
from openhands.server.routes.files import app
from openhands.server.session.conversation import Conversation
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def client():
    app_instance = FastAPI()
    app_instance.include_router(app)
    return TestClient(app_instance)


@pytest.fixture
def conversation():
    config = AppConfig()
    file_store = InMemoryFileStore()
    with patch("openhands.runtime.impl.eventstream.eventstream_runtime.docker") as mock_docker:
        mock_client = MagicMock()
        mock_client.version.return_value = {"Version": "20.10.0"}
        mock_docker.from_env.return_value = mock_client
        return Conversation("test_sid", file_store, config)


def test_zip_directory_with_descriptive_name(client, conversation):
    # Create a temporary file to simulate the workspace
    with tempfile.NamedTemporaryFile() as temp_file:
        # Mock the runtime to return our temp file
        mock_runtime = MagicMock()
        mock_runtime.copy_from.return_value = temp_file.name
        mock_runtime.config.workspace_mount_path_in_sandbox = "/workspace"
        conversation.runtime = mock_runtime

        # Mock the event stream to have some events
        conversation.event_stream.get_events = MagicMock(return_value=[
            MessageAction("Fix the bug"),
            MessageObservation(content="I'll help fix the bug"),
        ])

        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.completion.return_value = {
            "choices": [{"message": {"content": "fixing-bug-in-code"}}]
        }

        # Create a mock request object
        mock_request = MagicMock()
        mock_request.state.conversation = conversation
        mock_request.state.llm = mock_llm

        # Mock the FastAPI app's dependency injection
        with patch("fastapi.Request", return_value=mock_request):
            with patch("openhands.server.routes.files.Request", return_value=mock_request):
                response = client.get("/zip-directory")

                # Check that the response is successful
                assert response.status_code == 200

                # Check that the filename is correct
                assert response.headers["content-disposition"] == 'attachment; filename="fixing-bug-in-code.zip"'


def test_zip_directory_fallback_name(client, conversation):
    # Create a temporary file to simulate the workspace
    with tempfile.NamedTemporaryFile() as temp_file:
        # Mock the runtime to return our temp file
        mock_runtime = MagicMock()
        mock_runtime.copy_from.return_value = temp_file.name
        mock_runtime.config.workspace_mount_path_in_sandbox = "/workspace"
        conversation.runtime = mock_runtime

        # Mock the event stream to have no events
        conversation.event_stream.get_events = MagicMock(return_value=[])

        # Create a mock request object
        mock_request = MagicMock()
        mock_request.state.conversation = conversation
        mock_request.state.llm = None  # No LLM available

        # Mock the FastAPI app's dependency injection
        with patch("fastapi.Request", return_value=mock_request):
            with patch("openhands.server.routes.files.Request", return_value=mock_request):
                response = client.get("/zip-directory")

                # Check that the response is successful
                assert response.status_code == 200

                # Check that the filename falls back to workspace.zip
                assert response.headers["content-disposition"] == 'attachment; filename="workspace.zip"'
