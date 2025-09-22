import uuid

from sqlalchemy import JSON, Boolean, Column, Float, Integer, String
from storage.base import Base


class StoredSettings(Base):  # type: ignore
    """
    Legacy user settings storage. This should be considered deprecated - use UserSettings isntead
    """

    __tablename__ = 'settings'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    language = Column(String, nullable=True)
    agent = Column(String, nullable=True)
    max_iterations = Column(Integer, nullable=True)
    security_analyzer = Column(String, nullable=True)
    confirmation_mode = Column(Boolean, nullable=True, default=False)
    llm_model = Column(String, nullable=True)
    llm_api_key = Column(String, nullable=True)
    llm_base_url = Column(String, nullable=True)
    remote_runtime_resource_factor = Column(Integer, nullable=True)
    enable_default_condenser = Column(Boolean, nullable=False, default=True)
    user_consents_to_analytics = Column(Boolean, nullable=True)
    margin = Column(Float, nullable=True)
    enable_sound_notifications = Column(Boolean, nullable=True, default=False)
    sandbox_base_container_image = Column(String, nullable=True)
    sandbox_runtime_container_image = Column(String, nullable=True)
    secrets_store = Column(JSON, nullable=True)
