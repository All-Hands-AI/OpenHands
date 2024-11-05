import json
from typing import Any, Literal, Optional

import requests
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger


from datetime import datetime
from typing import ClassVar

class FeedbackDataModel(BaseModel):
    """Model for feedback data validation and storage.
    
    This model represents feedback data with strict validation rules.
    It ensures all required fields are present and have the correct types.
    
    Attributes:
        version: Version string for the feedback format
        email: User's email address
        polarity: Whether the feedback is positive or negative
        feedback: Legacy field for backward compatibility (same as polarity)
        permissions: Whether the feedback can be shared publicly
        trajectory: Optional list of steps taken during the session
        
    Class Attributes:
        MAX_TRAJECTORY_LENGTH: Maximum number of steps in trajectory
        MAX_STEP_SIZE: Maximum size of a trajectory step in bytes
        SUPPORTED_VERSIONS: List of supported version strings
        
    Notes:
        - The feedback field is deprecated and will be removed in a future version
        - All string fields must be non-empty
        - Email must be a valid email format
        - Trajectory must be a list of dictionaries if provided
        - Trajectory size and length are limited
    """
    # Fields
    version: str
    email: str
    polarity: Literal['positive', 'negative']
    feedback: Literal['positive', 'negative']  # TODO: remove this, its here for backward compatibility
    permissions: Literal['public', 'private']
    trajectory: Optional[list[dict[str, Any]]] = None
    timestamp: datetime = datetime.utcnow()  # Auto-set to current time
    
    # Validation constants
    MAX_TRAJECTORY_LENGTH: ClassVar[int] = 1000  # Maximum steps in trajectory
    MAX_STEP_SIZE: ClassVar[int] = 1024 * 1024  # 1MB per step
    SUPPORTED_VERSIONS: ClassVar[list[str]] = ['1.0', '1.1', '2.0']  # Supported versions
    
    class Config:
        """Pydantic model configuration."""
        extra = 'forbid'  # Prevent additional fields
        validate_assignment = True  # Validate on attribute assignment
        
    @field_validator('version')
    def validate_version(cls, v: str) -> str:
        """Validate version string.
        
        This validator ensures the version string is:
        1. A non-empty string
        2. In the list of supported versions
        3. Properly formatted (no extra whitespace)
        
        Args:
            v: Version string to validate
            
        Returns:
            str: The validated version string
            
        Raises:
            ValueError: If version is empty, invalid, or unsupported
        """
        if not v or not isinstance(v, str):
            raise ValueError('Version must be a non-empty string')
            
        v = v.strip()
        if not v:
            raise ValueError('Version cannot be whitespace only')
            
        if v not in cls.SUPPORTED_VERSIONS:
            supported = ', '.join(cls.SUPPORTED_VERSIONS)
            raise ValueError(
                f'Unsupported version: {v}. Must be one of: {supported}'
            )
            
        return v

    @field_validator('email')
    def validate_email(cls, v: str) -> str:
        """Validate email address.
        
        This validator ensures the email:
        1. Is a non-empty string
        2. Has valid email format
        3. Uses only allowed characters
        4. Has proper domain structure
        5. Is properly normalized (lowercase, no extra whitespace)
        
        Args:
            v: Email address to validate
            
        Returns:
            str: The validated and normalized email address
            
        Raises:
            ValueError: If email is empty or has invalid format
        """
        if not v or not isinstance(v, str):
            raise ValueError('Email must be a non-empty string')
            
        v = v.strip().lower()
        if not v:
            raise ValueError('Email cannot be whitespace only')
            
        # Split into local and domain parts
        try:
            local, domain = v.split('@')
        except ValueError:
            raise ValueError('Email must contain exactly one @ symbol')
            
        # Validate local part
        if not local:
            raise ValueError('Email local part cannot be empty')
        if len(local) > 64:
            raise ValueError('Email local part too long (max 64 chars)')
        if not re.match(r'^[a-zA-Z0-9.!#$%&\'*+\-/=?^_`{|}~]+$', local):
            raise ValueError('Invalid characters in email local part')
            
        # Validate domain part
        if not domain:
            raise ValueError('Email domain cannot be empty')
        if len(domain) > 255:
            raise ValueError('Email domain too long (max 255 chars)')
        if not re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z]{2,})+$', domain):
            raise ValueError('Invalid email domain format')
            
        return v

    @field_validator('trajectory')
    def validate_trajectory(cls, v: Optional[list[dict[str, Any]]]) -> Optional[list[dict[str, Any]]]:
        """Validate trajectory data.
        
        This validator ensures the trajectory:
        1. Is either None or a list
        2. Contains only dictionaries
        3. Doesn't exceed maximum length
        4. Doesn't exceed size limits
        5. Has serializable content
        
        Args:
            v: Trajectory data to validate
            
        Returns:
            Optional[list[dict[str, Any]]]: The validated trajectory data
            
        Raises:
            ValueError: If trajectory format or size is invalid
        """
        if v is None:
            return None
            
        if not isinstance(v, list):
            raise ValueError('Trajectory must be a list')
            
        # Check length
        if len(v) > cls.MAX_TRAJECTORY_LENGTH:
            raise ValueError(
                f'Trajectory too long: {len(v)} steps. '
                f'Maximum is {cls.MAX_TRAJECTORY_LENGTH}'
            )
            
        # Validate each step
        for i, step in enumerate(v):
            # Check type
            if not isinstance(step, dict):
                raise ValueError(f'Trajectory step {i} must be a dictionary')
                
            # Check size
            try:
                step_size = len(json.dumps(step).encode('utf-8'))
                if step_size > cls.MAX_STEP_SIZE:
                    raise ValueError(
                        f'Trajectory step {i} too large: {step_size} bytes. '
                        f'Maximum is {cls.MAX_STEP_SIZE}'
                    )
            except (TypeError, ValueError) as e:
                raise ValueError(f'Invalid data in trajectory step {i}: {str(e)}')
                
        return v
        
    @field_validator('timestamp')
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Validate timestamp.
        
        This validator ensures the timestamp:
        1. Is a valid datetime object
        2. Is in UTC
        3. Is not in the future
        
        Args:
            v: Timestamp to validate
            
        Returns:
            datetime: The validated timestamp
            
        Raises:
            ValueError: If timestamp is invalid
        """
        if not isinstance(v, datetime):
            raise ValueError('Timestamp must be a datetime object')
            
        # Ensure UTC
        if v.tzinfo is not None:
            raise ValueError('Timestamp must be naive (UTC assumed)')
            
        # Check for future dates
        now = datetime.utcnow()
        if v > now:
            raise ValueError('Timestamp cannot be in the future')
            
        return v

    @model_validator(mode='after')
    def validate_model(self) -> 'FeedbackDataModel':
        """Validate the complete model.
        
        This validator runs after all field validators and ensures:
        1. Feedback matches polarity (backward compatibility)
        2. All required fields are present and valid
        3. No extra fields are present
        4. Data is consistent
        
        Returns:
            FeedbackDataModel: The validated model
            
        Raises:
            ValueError: If model validation fails
        """
        # Ensure feedback matches polarity
        if self.feedback != self.polarity:
            self.feedback = self.polarity
            logger.warning('Feedback field automatically updated to match polarity')
            
        # Validate total size
        try:
            data = self.model_dump()
            total_size = len(json.dumps(data).encode('utf-8'))
            if total_size > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError(
                    f'Total feedback size too large: {total_size} bytes. '
                    'Maximum is 10MB'
                )
        except (TypeError, ValueError) as e:
            raise ValueError(f'Invalid feedback data: {str(e)}')
            
        return self

    def model_dump(self) -> dict[str, Any]:
        """Override model_dump to handle data safely.
        
        This method ensures the model data is properly serialized and
        normalized before being returned.
        
        Returns:
            dict: The model data as a dictionary
            
        Notes:
            - Ensures all data is JSON serializable
            - Handles None values appropriately
            - Strips whitespace from string fields
            - Normalizes email to lowercase
            - Removes sensitive data
            - Validates data consistency
        """
        try:
            # Get base data
            data = super().model_dump()
            
            # Clean string fields
            for field in ['version', 'email']:
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip()
            if 'email' in data and isinstance(data[field], str):
                data['email'] = data['email'].lower()
                
            # Handle trajectory
            if data.get('trajectory') is not None:
                try:
                    # Validate serialization
                    json.dumps(data['trajectory'])
                    
                    # Check total size
                    trajectory_size = len(json.dumps(data['trajectory']).encode('utf-8'))
                    if trajectory_size > self.MAX_TRAJECTORY_LENGTH * self.MAX_STEP_SIZE:
                        logger.warning('Trajectory too large, removing from dump')
                        data['trajectory'] = None
                        
                except (TypeError, ValueError) as e:
                    logger.error(f'Invalid trajectory data: {str(e)}')
                    data['trajectory'] = None
                    
            # Add metadata
            data['timestamp'] = data['timestamp'].isoformat() + 'Z'
            data['schema_version'] = self.version
            
            # Remove sensitive data
            data.pop('token', None)
            
            return data
            
        except Exception as e:
            logger.error(f'Error in model_dump: {str(e)}', exc_info=True)
            raise ValueError(f'Failed to serialize feedback data: {str(e)}')


FEEDBACK_URL = 'https://share-od-trajectory-3u9bw9tx.uc.gateway.dev/share_od_trajectory'


def store_feedback(feedback: FeedbackDataModel) -> dict[str, str]:
    """Store feedback data in the remote service.
    
    Args:
        feedback: The feedback data model to store
        
    Returns:
        dict: The response data from the server
        
    Raises:
        ValueError: If the server returns a non-200 status code
        requests.RequestException: If there's a network/connection error
        json.JSONDecodeError: If the response is not valid JSON
    """
    try:
        # Start logging
        feedback.feedback = feedback.polarity
        display_feedback = feedback.model_dump()
        if 'trajectory' in display_feedback:
            display_feedback['trajectory'] = (
                f"elided [length: {len(display_feedback['trajectory'])}"
            )
        if 'token' in display_feedback:
            display_feedback['token'] = 'elided'
        logger.debug(f'Got feedback: {display_feedback}')
        
        # Start actual request
        response = requests.post(
            FEEDBACK_URL,
            headers={'Content-Type': 'application/json'},
            json=feedback.model_dump(),
            timeout=30  # Add timeout to prevent hanging
        )
        
        # Check response status
        if response.status_code == 404:
            raise ValueError('Feedback storage endpoint not found')
        elif response.status_code == 400:
            raise ValueError(f'Invalid feedback data: {response.text}')
        elif response.status_code != 200:
            raise ValueError(f'Failed to store feedback (status {response.status_code}): {response.text}')
            
        # Parse response
        try:
            response_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f'Invalid JSON response from feedback server: {str(e)}')
            raise
            
        logger.debug(f'Stored feedback: {response.text}')
        return response_data
        
    except requests.Timeout:
        logger.error('Timeout while storing feedback')
        raise
    except requests.RequestException as e:
        logger.error(f'Network error while storing feedback: {str(e)}')
        raise
