#!/usr/bin/env python3
"""
Tests for conversation manager functionality.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
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
        created_at = datetime(now.year, now.month, now.day, now.hour, now.minute - 5, tzinfo=timezone.utc)
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