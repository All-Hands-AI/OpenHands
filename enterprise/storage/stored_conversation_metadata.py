import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from storage.base import Base

from openhands.app_server.app_conversation.sql_app_conversation_info_service import StoredAppConversationInfo


StoredConversationMetadata = StoredAppConversationInfo
