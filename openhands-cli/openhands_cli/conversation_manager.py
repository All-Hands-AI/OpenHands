#!/usr/bin/env python3
"""
Conversation management functionality for OpenHands CLI.
Handles listing, loading, and managing past conversations.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

try:
    from openhands.sdk import BaseConversation, Conversation, LocalFileStore
    from openhands.storage.data_models.conversation_metadata import ConversationMetadata
    SDK_AVAILABLE = True
except ImportError:
    # For testing or when SDK is not available
    BaseConversation = None
    Conversation = None
    LocalFileStore = None
    ConversationMetadata = None
    SDK_AVAILABLE = False
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands_cli.locations import PERSISTENCE_DIR


class ConversationInfo:
    """Information about a stored conversation."""
    
    def __init__(self, conversation_id: str, created_at: datetime, title: Optional[str] = None, 
                 last_updated_at: Optional[datetime] = None):
        self.conversation_id = conversation_id
        self.created_at = created_at
        self.title = title
        self.last_updated_at = last_updated_at or created_at
    
    @property
    def short_id(self) -> str:
        """Return a shortened version of the conversation ID for display."""
        return self.conversation_id[:8]
    
    def format_date(self, date: datetime) -> str:
        """Format a datetime for display."""
        now = datetime.now(date.tzinfo)
        diff = now - date
        
        if diff.days == 0:
            if diff.seconds < 3600:  # Less than 1 hour
                minutes = diff.seconds // 60
                return f"{minutes}m ago"
            else:  # Less than 1 day
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "1 day ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return date.strftime("%Y-%m-%d")


class ConversationManager:
    """Manages conversation listing and loading for the CLI."""
    
    def __init__(self):
        self.conversations_dir = os.path.join(PERSISTENCE_DIR, "conversation")
    
    def discover_conversations(self) -> List[ConversationInfo]:
        """Discover all stored conversations."""
        conversations = []
        
        if not os.path.exists(self.conversations_dir):
            return conversations
        
        for item in os.listdir(self.conversations_dir):
            conversation_path = os.path.join(self.conversations_dir, item)
            if os.path.isdir(conversation_path):
                try:
                    # Try to parse as UUID to validate it's a conversation directory
                    UUID(item)
                    
                    # Look for metadata or conversation files
                    metadata_file = os.path.join(conversation_path, "metadata.json")
                    conversation_file = os.path.join(conversation_path, "conversation.json")
                    
                    created_at = datetime.fromtimestamp(os.path.getctime(conversation_path))
                    last_updated_at = datetime.fromtimestamp(os.path.getmtime(conversation_path))
                    title = None
                    
                    # Try to extract title from metadata if available
                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                                title = metadata.get('title')
                                if 'created_at' in metadata:
                                    created_at = datetime.fromisoformat(metadata['created_at'].replace('Z', '+00:00'))
                                if 'last_updated_at' in metadata:
                                    last_updated_at = datetime.fromisoformat(metadata['last_updated_at'].replace('Z', '+00:00'))
                        except (json.JSONDecodeError, ValueError, KeyError):
                            pass  # Use default values
                    
                    # If no title from metadata, try to extract from first user message
                    if not title and os.path.exists(conversation_file):
                        title = self._extract_title_from_conversation(conversation_file)
                    
                    conversations.append(ConversationInfo(
                        conversation_id=item,
                        created_at=created_at,
                        title=title,
                        last_updated_at=last_updated_at
                    ))
                    
                except ValueError:
                    # Not a valid UUID, skip
                    continue
                except Exception:
                    # Other errors, skip this conversation
                    continue
        
        # Sort by last updated time, most recent first
        conversations.sort(key=lambda c: c.last_updated_at, reverse=True)
        return conversations
    
    def _extract_title_from_conversation(self, conversation_file: str) -> Optional[str]:
        """Extract a title from the first user message in the conversation."""
        try:
            with open(conversation_file, 'r') as f:
                data = json.load(f)
                
            # Look for the first user message
            events = data.get('events', [])
            for event in events:
                if event.get('source') == 'user' and event.get('message'):
                    message = event['message']
                    # Take first 50 characters as title
                    if len(message) > 50:
                        return message[:47] + "..."
                    return message
                    
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            pass
        
        return None
    
    def list_conversations(self, limit: int = 10) -> None:
        """Display a list of past conversations."""
        conversations = self.discover_conversations()
        
        if not conversations:
            print_formatted_text(HTML("<yellow>No past conversations found.</yellow>"))
            print_formatted_text(HTML("<grey>Start a new conversation by typing a message!</grey>"))
            return
        
        print_formatted_text(HTML("<gold>📚 Past Conversations</gold>"))
        print_formatted_text("")
        
        # Show up to the specified limit
        for i, conv in enumerate(conversations[:limit]):
            if i >= limit:
                break
                
            # Format the display
            title_display = conv.title or "<untitled>"
            if len(title_display) > 60:
                title_display = title_display[:57] + "..."
            
            created_display = conv.format_date(conv.created_at)
            updated_display = conv.format_date(conv.last_updated_at)
            
            print_formatted_text(HTML(
                f"  <white>{conv.short_id}</white> - {title_display}"
            ))
            print_formatted_text(HTML(
                f"    <grey>Created: {created_display}, Updated: {updated_display}</grey>"
            ))
            print_formatted_text("")
        
        if len(conversations) > limit:
            remaining = len(conversations) - limit
            print_formatted_text(HTML(f"<grey>... and {remaining} more conversations</grey>"))
            print_formatted_text("")
        
        print_formatted_text(HTML("<grey>Use '/load <id>' to resume a conversation</grey>"))
        print_formatted_text("")
    
    def load_conversation(self, conversation_id: str) -> Optional[object]:
        """Load a conversation by ID (supports both full UUID and short ID)."""
        conversations = self.discover_conversations()
        
        # Find matching conversation (support both full and short ID)
        matching_conv = None
        for conv in conversations:
            if conv.conversation_id == conversation_id or conv.conversation_id.startswith(conversation_id):
                matching_conv = conv
                break
        
        if not matching_conv:
            print_formatted_text(HTML(f"<red>Conversation '{conversation_id}' not found.</red>"))
            print_formatted_text(HTML("<grey>Use '/list' to see available conversations.</grey>"))
            return None
        
        try:
            # Load the conversation using the SDK
            conversation_uuid = UUID(matching_conv.conversation_id)
            conversation_path = os.path.join(self.conversations_dir, matching_conv.conversation_id)
            
            # We need to reconstruct the conversation with the agent
            # For now, we'll return None and let the caller handle creating a new conversation
            # This is a limitation that would need agent configuration to fully implement
            print_formatted_text(HTML(f"<yellow>Found conversation {matching_conv.short_id}</yellow>"))
            print_formatted_text(HTML(f"<grey>Title: {matching_conv.title or 'Untitled'}</grey>"))
            print_formatted_text(HTML(f"<grey>Created: {matching_conv.format_date(matching_conv.created_at)}</grey>"))
            print_formatted_text(HTML("<red>Note: Full conversation loading requires agent reconfiguration.</red>"))
            print_formatted_text(HTML("<grey>This feature will be enhanced in a future update.</grey>"))
            
            return None
            
        except Exception as e:
            print_formatted_text(HTML(f"<red>Error loading conversation: {e}</red>"))
            return None
    
    def get_conversation_suggestions(self, partial_id: str) -> List[str]:
        """Get conversation ID suggestions for command completion."""
        conversations = self.discover_conversations()
        suggestions = []
        
        for conv in conversations:
            # Add both short and full IDs if they match the partial input
            if conv.conversation_id.startswith(partial_id):
                suggestions.append(conv.conversation_id)
            if conv.short_id.startswith(partial_id) and conv.short_id not in suggestions:
                suggestions.append(conv.short_id)
        
        return suggestions[:10]  # Limit to 10 suggestions