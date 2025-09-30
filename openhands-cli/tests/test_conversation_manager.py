#!/usr/bin/env python3
"""
Tests for conversation manager functionality.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from openhands_cli.conversation_manager import ConversationInfo, ConversationManager


class TestConversationInfo:
    """Test ConversationInfo class."""

    def test_short_id(self):
        """Test short ID generation."""
        conversation_id = "12345678-1234-1234-1234-123456789012"
        created_at = datetime.now(timezone.utc)
        info = ConversationInfo(conversation_id, created_at)
        assert info.short_id == "12345678"

    def test_format_date_minutes(self):
        """Test date formatting for recent times."""
        now = datetime.now(timezone.utc)
        # Use timedelta to avoid minute underflow
        created_at = now - timedelta(minutes=5)
        info = ConversationInfo("test-id", created_at)
        formatted = info.format_date(created_at)
        assert "m ago" in formatted

    def test_format_date_hours(self):
        """Test date formatting for hours ago."""
        now = datetime.now(timezone.utc)
        created_at = datetime(now.year, now.month, now.day, now.hour - 2, tzinfo=timezone.utc)
        info = ConversationInfo("test-id", created_at)
        formatted = info.format_date(created_at)
        assert "h ago" in formatted

    def test_format_date_days(self):
        """Test date formatting for days ago."""
        now = datetime.now(timezone.utc)
        # Create a date 3 days ago
        import datetime as dt
        created_at = now - dt.timedelta(days=3)
        info = ConversationInfo("test-id", created_at)
        formatted = info.format_date(created_at)
        assert "days ago" in formatted


class TestConversationManager:
    """Test ConversationManager class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.conversations_dir = os.path.join(self.temp_dir, "conversation")
        os.makedirs(self.conversations_dir, exist_ok=True)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_conversation(self, conversation_id: str, title: str = None, 
                                created_at: datetime = None) -> str:
        """Create a test conversation directory with metadata."""
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        
        conv_dir = os.path.join(self.conversations_dir, conversation_id)
        os.makedirs(conv_dir, exist_ok=True)
        
        # Create metadata file
        metadata = {
            "conversation_id": conversation_id,
            "title": title,
            "created_at": created_at.isoformat(),
            "last_updated_at": created_at.isoformat()
        }
        
        metadata_file = os.path.join(conv_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        return conv_dir

    def create_test_conversation_with_messages(self, conversation_id: str, first_message: str) -> str:
        """Create a test conversation with a conversation.json file."""
        conv_dir = os.path.join(self.conversations_dir, conversation_id)
        os.makedirs(conv_dir, exist_ok=True)
        
        # Create conversation file with events
        conversation_data = {
            "events": [
                {
                    "source": "user",
                    "message": first_message,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        
        conversation_file = os.path.join(conv_dir, "conversation.json")
        with open(conversation_file, 'w') as f:
            json.dump(conversation_data, f)
        
        return conv_dir

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_discover_conversations_empty(self, mock_persistence_dir):
        """Test discovering conversations when none exist."""
        mock_persistence_dir.return_value = self.temp_dir
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        conversations = manager.discover_conversations()
        assert len(conversations) == 0

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_discover_conversations_with_metadata(self, mock_persistence_dir):
        """Test discovering conversations with metadata."""
        mock_persistence_dir.return_value = self.temp_dir
        
        # Create test conversations
        conv_id1 = str(uuid.uuid4())
        conv_id2 = str(uuid.uuid4())
        
        self.create_test_conversation(conv_id1, "Test Conversation 1")
        self.create_test_conversation(conv_id2, "Test Conversation 2")
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        conversations = manager.discover_conversations()
        assert len(conversations) == 2
        
        # Check that conversations are sorted by last_updated_at (most recent first)
        assert all(isinstance(conv, ConversationInfo) for conv in conversations)
        assert any(conv.title == "Test Conversation 1" for conv in conversations)
        assert any(conv.title == "Test Conversation 2" for conv in conversations)

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_discover_conversations_with_messages(self, mock_persistence_dir):
        """Test discovering conversations and extracting title from messages."""
        mock_persistence_dir.return_value = self.temp_dir
        
        conv_id = str(uuid.uuid4())
        first_message = "Hello, can you help me with Python programming?"
        
        self.create_test_conversation_with_messages(conv_id, first_message)
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        conversations = manager.discover_conversations()
        assert len(conversations) == 1
        assert conversations[0].title == first_message

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_discover_conversations_long_message_truncation(self, mock_persistence_dir):
        """Test that long messages are truncated for titles."""
        mock_persistence_dir.return_value = self.temp_dir
        
        conv_id = str(uuid.uuid4())
        long_message = "This is a very long message that should be truncated because it exceeds the maximum length for display purposes"
        
        self.create_test_conversation_with_messages(conv_id, long_message)
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        conversations = manager.discover_conversations()
        assert len(conversations) == 1
        assert len(conversations[0].title) <= 50
        assert conversations[0].title.endswith("...")

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_get_conversation_suggestions(self, mock_persistence_dir):
        """Test conversation ID suggestions for completion."""
        mock_persistence_dir.return_value = self.temp_dir
        
        # Create test conversations with specific IDs
        conv_id1 = "12345678-1234-1234-1234-123456789012"
        conv_id2 = "12abcdef-1234-1234-1234-123456789012"
        conv_id3 = "87654321-1234-1234-1234-123456789012"
        
        self.create_test_conversation(conv_id1, "Test 1")
        self.create_test_conversation(conv_id2, "Test 2")
        self.create_test_conversation(conv_id3, "Test 3")
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        # Test partial matching - "123" should match conv_id1 (both full and short ID)
        suggestions = manager.get_conversation_suggestions("123")
        assert len(suggestions) == 2  # Should match conv_id1 full and short ID
        assert conv_id1 in suggestions
        assert "12345678" in suggestions
        
        # Test another partial match - "12" should match conv_id1 and conv_id2
        suggestions = manager.get_conversation_suggestions("12")
        assert len(suggestions) >= 2  # Should match at least conv_id1 and conv_id2
        assert conv_id1 in suggestions
        assert conv_id2 in suggestions
        
        # Test short ID exact matching
        suggestions = manager.get_conversation_suggestions("12345678")
        assert "12345678" in suggestions or conv_id1 in suggestions

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_invalid_conversation_directories_ignored(self, mock_persistence_dir):
        """Test that invalid conversation directories are ignored."""
        mock_persistence_dir.return_value = self.temp_dir
        
        # Create valid conversation
        valid_conv_id = str(uuid.uuid4())
        self.create_test_conversation(valid_conv_id, "Valid Conversation")
        
        # Create invalid directories (not UUIDs)
        invalid_dir1 = os.path.join(self.conversations_dir, "not-a-uuid")
        invalid_dir2 = os.path.join(self.conversations_dir, "also-not-uuid")
        os.makedirs(invalid_dir1)
        os.makedirs(invalid_dir2)
        
        # Create a file (not directory)
        invalid_file = os.path.join(self.conversations_dir, "some-file.txt")
        with open(invalid_file, 'w') as f:
            f.write("test")
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        conversations = manager.discover_conversations()
        assert len(conversations) == 1  # Only the valid conversation
        assert conversations[0].conversation_id == valid_conv_id

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_extract_title_from_conversation_no_user_messages(self, mock_persistence_dir):
        """Test title extraction when there are no user messages."""
        mock_persistence_dir.return_value = self.temp_dir
        
        conv_id = str(uuid.uuid4())
        conv_dir = os.path.join(self.conversations_dir, conv_id)
        os.makedirs(conv_dir, exist_ok=True)
        
        # Create conversation file with no user messages
        conversation_data = {
            "events": [
                {
                    "source": "assistant",
                    "message": "Hello! How can I help you?",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        
        conversation_file = os.path.join(conv_dir, "conversation.json")
        with open(conversation_file, 'w') as f:
            json.dump(conversation_data, f)
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        conversations = manager.discover_conversations()
        assert len(conversations) == 1
        assert conversations[0].title is None  # No user message found

    # Tests for conversation viewing functionality

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_load_conversation_events_nonexistent(self, mock_persistence_dir):
        """Test loading events from non-existent conversation."""
        mock_persistence_dir.return_value = self.temp_dir
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        events = manager._load_conversation_events("nonexistent-id")
        assert events == []

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_load_conversation_events_no_events_file(self, mock_persistence_dir):
        """Test loading events when events.jsonl doesn't exist."""
        mock_persistence_dir.return_value = self.temp_dir
        
        # Create conversation directory without events file
        conv_id = "test-conv-id"
        conv_dir = os.path.join(self.conversations_dir, conv_id)
        os.makedirs(conv_dir, exist_ok=True)
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        events = manager._load_conversation_events(conv_id)
        assert events == []

    @patch('openhands_cli.conversation_manager.PERSISTENCE_DIR')
    def test_load_conversation_events_with_data(self, mock_persistence_dir):
        """Test loading events from valid events.jsonl file."""
        mock_persistence_dir.return_value = self.temp_dir
        
        # Create conversation directory with events file
        conv_id = "test-conv-id"
        conv_dir = os.path.join(self.conversations_dir, conv_id)
        os.makedirs(conv_dir, exist_ok=True)
        
        events_file = os.path.join(conv_dir, "events.jsonl")
        sample_events = [
            {"event_type": "MessageAction", "source": "user", "content": "Hello", "timestamp": 1234567890},
            {"event_type": "CmdRunAction", "source": "agent", "command": "ls", "timestamp": 1234567891},
            {"event_type": "CmdOutputObservation", "source": "environment", "output": "file1.txt", "timestamp": 1234567892}
        ]
        
        with open(events_file, 'w') as f:
            for event in sample_events:
                f.write(json.dumps(event) + '\n')
        
        manager = ConversationManager()
        manager.conversations_dir = self.conversations_dir
        
        events = manager._load_conversation_events(conv_id)
        
        assert len(events) == 3
        assert events[0]["event_type"] == "MessageAction"
        assert events[1]["event_type"] == "CmdRunAction"
        assert events[2]["event_type"] == "CmdOutputObservation"

    def test_filter_events_by_source(self):
        """Test filtering events by source."""
        manager = ConversationManager()
        
        events = [
            {"event_type": "MessageAction", "source": "user", "content": "Hello"},
            {"event_type": "CmdRunAction", "source": "agent", "command": "ls"},
            {"event_type": "CmdOutputObservation", "source": "environment", "output": "file1.txt"}
        ]
        
        # Filter by user
        user_events = manager._filter_events(events, "user")
        assert len(user_events) == 1
        assert user_events[0]["source"] == "user"
        
        # Filter by agent
        agent_events = manager._filter_events(events, "agent")
        assert len(agent_events) == 1
        assert agent_events[0]["source"] == "agent"

    def test_filter_events_by_category(self):
        """Test filtering events by category."""
        manager = ConversationManager()
        
        events = [
            {"event_type": "MessageAction", "source": "user", "content": "Hello"},
            {"event_type": "CmdRunAction", "source": "agent", "command": "ls"},
            {"event_type": "CmdOutputObservation", "source": "environment", "output": "file1.txt"},
            {"event_type": "FileEditAction", "source": "agent", "path": "test.py"},
            {"event_type": "AgentThinkAction", "source": "agent", "thought": "I need to..."}
        ]
        
        # Filter by action category
        action_events = manager._filter_events(events, "action")
        assert len(action_events) == 4  # MessageAction, CmdRunAction, FileEditAction, AgentThinkAction
        
        # Filter by observation category
        obs_events = manager._filter_events(events, "observation")
        assert len(obs_events) == 1  # CmdOutputObservation
        
        # Filter by command category
        cmd_events = manager._filter_events(events, "command")
        assert len(cmd_events) == 1  # CmdRunAction
        
        # Filter by file category
        file_events = manager._filter_events(events, "file")
        assert len(file_events) == 1  # FileEditAction
        
        # Filter by think category
        think_events = manager._filter_events(events, "think")
        assert len(think_events) == 1  # AgentThinkAction

    def test_matches_event_category(self):
        """Test event category matching logic."""
        manager = ConversationManager()
        
        # Test action matching
        action_event = {"event_type": "CmdRunAction", "source": "agent"}
        assert manager._matches_event_category(action_event, "action")
        assert manager._matches_event_category(action_event, "command")
        assert not manager._matches_event_category(action_event, "observation")
        
        # Test observation matching
        obs_event = {"event_type": "CmdOutputObservation", "source": "environment"}
        assert manager._matches_event_category(obs_event, "observation")
        assert not manager._matches_event_category(obs_event, "action")
        
        # Test file operations
        file_event = {"event_type": "FileEditAction", "source": "agent"}
        assert manager._matches_event_category(file_event, "file")
        assert manager._matches_event_category(file_event, "action")

    def test_extract_event_content(self):
        """Test extracting content from different event types."""
        manager = ConversationManager()
        
        # Test direct content field
        event1 = {"event_type": "MessageAction", "content": "Hello world"}
        assert manager._extract_event_content(event1) == "Hello world"
        
        # Test command field
        event2 = {"event_type": "CmdRunAction", "command": "ls -la"}
        assert manager._extract_event_content(event2) == "ls -la"
        
        # Test args structure
        event3 = {"event_type": "FileEditAction", "args": {"path": "/test/file.py", "content": "print('hello')"}}
        content = manager._extract_event_content(event3)
        assert content in ["/test/file.py", "print('hello')"]  # Either could be returned first
        
        # Test empty event
        event4 = {"event_type": "UnknownAction"}
        assert manager._extract_event_content(event4) == ""

    def test_get_available_filters(self):
        """Test getting list of available filters."""
        manager = ConversationManager()
        
        filters = manager.get_available_filters()
        expected_filters = ['action', 'observation', 'user', 'agent', 'command', 'file', 'browse', 'message', 'think']
        
        assert len(filters) == len(expected_filters)
        for filter_name in expected_filters:
            assert filter_name in filters